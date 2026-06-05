from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    File,
    UploadFile,
    Form,
    WebSocket,
    WebSocketDisconnect,
)
from typing import Optional
import sys
import time
import logging
from pathlib import Path
import cv2
import numpy as np

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ocr_ai/load_model")
async def load_ocr_model(request: Request, model_path: str):
    """Load OCR model"""
    ocr_ai = request.app.state.ocr_ai

    try:
        ocr_ai.load_model(model_path)
        return {"success": True, "message": f"Model loaded from {model_path}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/ocr_ai/input_config")
async def input_ocr_config(
    request: Request,
    acceptance_threshold_ocr: float = 0.5,
    duplication_threshold_ocr: float = 0.5,
    row_threshold: int = 20,
):
    """Input OCR configuration"""
    ocr_ai = request.app.state.ocr_ai

    try:
        ocr_ai.input_config(
            acceptance_threshold_ocr=acceptance_threshold_ocr,
            duplication_threshold_ocr=duplication_threshold_ocr,
            row_threshold=row_threshold,
        )
        return {"success": True, "message": "OCR configuration updated"}

    except Exception as e:
        return {"success": False, "error": str(e)}


# @router.post("/ocr_ai/predict")
# async def ocr_predict(
#     request: Request,
#     img_ocr: UploadFile = File(...),
#     acceptance_threshold_ocr: float = Form(0.5),
#     duplication_threshold_ocr: float = Form(0.5),
#     row_threshold: int = Form(20),
# ):
#     """Perform OCR prediction on image"""
#     ocr_ai = request.app.state.ocr_ai
#     t0 = time.time()

#     try:
#         # Read binary image data
#         img_data = await img_ocr.read()
#         t1 = time.time()
#         logger.info(f"[Router] Read file: {t1-t0:.3f}s")

#         np_arr = np.frombuffer(img_data, np.uint8)
#         img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
#         t2 = time.time()
#         logger.info(f"[Router] Decode image: {t2-t1:.3f}s")

#         result = ocr_ai.predict(
#             img,
#             acceptance_threshold_ocr,
#             duplication_threshold_ocr,
#             row_threshold,
#         )
#         t3 = time.time()
#         logger.info(f"[Router] Predict: {t3-t2:.3f}s")
#         logger.info(f"[Router] Total: {t3-t0:.3f}s")

#         return result

#     except Exception as e:
#         return {"success": False, "error": str(e)}


@router.websocket("/ocr_ai/ws")
async def websocket_ocr(websocket: WebSocket):
    """WebSocket endpoint for real-time OCR prediction"""
    await websocket.accept()
    ocr_ai = websocket.app.state.ocr_ai

    logger.info("[WebSocket] Client connected")

    try:
        while True:
            data = await websocket.receive()

            if "bytes" in data:
                t0 = time.time()

                np_arr = np.frombuffer(data["bytes"], np.uint8)
                img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                t1 = time.time()

                result = ocr_ai.predict(img)
                t2 = time.time()

                logger.info(
                    f"[WebSocket] Decode: {t1-t0:.3f}s, Predict: {t2-t1:.3f}s, Total: {t2-t0:.3f}s"
                )
                await websocket.send_json(result)

    except (WebSocketDisconnect, RuntimeError):
        logger.info("[WebSocket] Client disconnected")
    except Exception as e:
        logger.error(f"[WebSocket] Error: {e}")
