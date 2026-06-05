import sys
import os
import logging
from typing import Optional, Dict, Any
import numpy as np
import time

if getattr(sys, "frozen", False):
    _ai_dir = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "backend", "AI")
else:
    _ai_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_ai_dir, "RunTime_Sofware"))
import Deep_Learning_Tool
from Deep_Learning_Tool import OCR_DEEP_LEARNING

logger = logging.getLogger(__name__)


class OCR:
    def __init__(self):
        # Save current working directory
        original_cwd = os.getcwd()

        # Change to RunTime_Sofware directory for UI file loading
        runtime_dir = os.path.join(_ai_dir, "RunTime_Sofware")
        os.chdir(runtime_dir)

        try:
            self.OCR_DEEP_LEARNING_TOOL = OCR_DEEP_LEARNING()
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def load_model(self, model_path: str):
        """Load the OCR model from the specified path"""
        if not model_path:
            raise ValueError("model_path cannot be empty")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")

        try:
            self._model_OCR = self.OCR_DEEP_LEARNING_TOOL.Load_Model_OCR(model_path)
            logger.info(f"Model loaded successfully from: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise

    def input_config(
        self,
        acceptance_threshold_ocr: float,
        duplication_threshold_ocr: float,
        row_threshold: int,
    ):
        if not (0 <= acceptance_threshold_ocr <= 1):
            raise ValueError("acceptance_threshold_ocr must be between 0 and 1")

        if not (0 <= duplication_threshold_ocr <= 1):
            raise ValueError("duplication_threshold_ocr must be between 0 and 1")

        if row_threshold < 0:
            raise ValueError("row_threshold must be non-negative")

        self.acceptance_threshold_ocr = acceptance_threshold_ocr
        self.duplication_threshold_ocr = duplication_threshold_ocr
        self.row_threshold = row_threshold
        logger.info("OCR configuration set successfully")

    def predict(self, img_ocr: np.ndarray) -> Dict[str, Any]:
        """Predict text from image using OCR model"""
        if not hasattr(self, "_model_OCR") or self._model_OCR is None:
            raise RuntimeError("Model not loaded. Call load_model() first")

        if img_ocr is None or img_ocr.size == 0:
            raise ValueError("img_ocr cannot be None or empty")

        if not (0 <= self.acceptance_threshold_ocr <= 1):
            raise ValueError("acceptance_threshold_ocr must be between 0 and 1")

        if not (0 <= self.duplication_threshold_ocr <= 1):
            raise ValueError("duplication_threshold_ocr must be between 0 and 1")

        if self.row_threshold < 0:
            raise ValueError("row_threshold must be non-negative")

        try:
            start_time = time.time()
            result = self.OCR_DEEP_LEARNING_TOOL.Prediction_OCR_None_Img_E(
                img_ocr,
                self._model_OCR,
                self.acceptance_threshold_ocr,
                self.duplication_threshold_ocr,
                self.row_threshold,
            )
            _, text, _, message = result
            if message == "key_ok":
                logger.info(
                    f"OCR Prediction completed with text: {text}, message: {message}"
                )
                end_time = time.time()
                processing_time = end_time - start_time
                logger.info(
                    f"OCR Prediction processing time: {processing_time:.2f} seconds"
                )
                return {"success": True, "text": text}
            else:
                return {"success": False, "error": message}

        except Exception as e:
            logger.error(f"Error occurred during OCR prediction: {e}")
            return {"success": False, "error": str(e)}
