import requests
import websocket
import json
from typing import Optional, Dict, Any, List
import logging
import time

logger = logging.getLogger(__name__)


class APIClient:
    """Client for communicating with Backend API"""

    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.timeout = 30  # seconds
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        files: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint}"
        start_time = time.time()

        try:
            if files:
                # Multipart form-data request (files + form data)
                response = self.session.request(
                    method=method,
                    url=url,
                    files=files,
                    data=data,
                    params=params,
                    timeout=self.timeout,
                )
            else:
                # JSON request
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    timeout=self.timeout,
                )

            response.raise_for_status()
            result = response.json()

            elapsed = time.time() - start_time
            logger.info(f"[API Client] {method} {endpoint}: {elapsed:.3f}s")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"success": False, "error": str(e)}

    def load_model(self, model_path: str) -> Dict[str, Any]:
        """Load a model from a path"""
        endpoint = f"ai/ocr_ai/load_model"
        params = {"model_path": model_path}
        return self._request("POST", endpoint, params=params)

    # def ocr_predict(
    #     self,
    #     img_ocr_binary: bytes,
    #     acceptance_threshold_ocr: float = 0.5,
    #     duplication_threshold_ocr: float = 0.5,
    #     row_threshold: int = 20,
    # ) -> Dict[str, Any]:
    #     """Perform OCR prediction on image using binary data"""
    #     endpoint = "ai/ocr_ai/predict"
    #     files = {"img_ocr": ("image.jpg", img_ocr_binary, "image/jpeg")}
    #     data = {
    #         "acceptance_threshold_ocr": acceptance_threshold_ocr,
    #         "duplication_threshold_ocr": duplication_threshold_ocr,
    #         "row_threshold": row_threshold,
    #     }
    #     return self._request("POST", endpoint, data=data, files=files)

    def input_config(
        self,
        acceptance_threshold_ocr: float = 0.5,
        duplication_threshold_ocr: float = 0.5,
        row_threshold: int = 20,
    ) -> Dict[str, Any]:
        """Update OCR configuration"""
        endpoint = "ai/ocr_ai/input_config"
        params = {
            "acceptance_threshold_ocr": acceptance_threshold_ocr,
            "duplication_threshold_ocr": duplication_threshold_ocr,
            "row_threshold": row_threshold,
        }
        return self._request("POST", endpoint, params=params)

    # ── WebSocket methods ──

    def ws_connect(self):
        """Connect to WebSocket server"""
        ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_url}/ai/ocr_ai/ws"

        self._ws = websocket.WebSocket()
        self._ws.connect(ws_url)
        logger.info(f"[WebSocket] Connected to {ws_url}")

    def ws_disconnect(self):
        """Disconnect from WebSocket server"""
        if hasattr(self, "_ws") and self._ws:
            self._ws.close()
            self._ws = None
            logger.info("[WebSocket] Disconnected")

    def ws_predict(self, img_ocr_binary: bytes) -> Dict[str, Any]:
        """Send binary image and receive OCR result via WebSocket"""
        start_time = time.time()

        self._ws.send_binary(img_ocr_binary)
        result = json.loads(self._ws.recv())

        elapsed = time.time() - start_time
        logger.info(f"[WebSocket] Predict: {elapsed:.3f}s")

        return result
