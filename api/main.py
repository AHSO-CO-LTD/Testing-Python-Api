# ===== SAFE IMPORT ZONE for PyInstaller =====
# Các thư viện dùng trong .pyd (api/, backend/) mà PyInstaller không tự detect được.
# Bao gồm dependencies của Deep_Learning_Tool (phần explicit imports từ .pyi).

# --- API / Server ---
import fastapi
import uvicorn

# --- Windows API (Single Instance) ---
import win32event
import win32api
import winerror

# --- Data / AI ---
import numpy
import pandas
import cv2
import torch
import torch.nn
import torch.optim
import torch.utils.data
from torch.utils.data import DataLoader, Dataset
import torchvision
from torchvision import datasets, transforms
from torchvision.models import resnet18
from torchinfo import summary
from ultralytics import YOLO
import tqdm
from sklearn.model_selection import train_test_split
import yaml

# --- Image / Vision ---
from PIL import Image, ImageTk
import cvzone
from cvzone.Utils import putTextRect

# --- GUI (Deep_Learning_Tool dùng PyQt5 nội bộ) ---
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# ===== END SAFE IMPORT ZONE =====

import sys, os

# Lấy thư mục chứa file main.py hoặc main.exe
if getattr(sys, "frozen", False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Fix windowed exe: stdout/stderr là None → uvicorn crash khi gọi sys.stderr.isatty()
if sys.stdout is None or sys.stderr is None:
    _log = os.path.join(base_path, "backend", "logs", "console.log")
    os.makedirs(os.path.dirname(_log), exist_ok=True)
    _stream = open(_log, "a", encoding="utf-8")
    if sys.stdout is None:
        sys.stdout = _stream
    if sys.stderr is None:
        sys.stderr = _stream

# Thêm các thư mục vào sys.path để app import khi đóng exe
# sys.path.insert(0, os.path.join(base_path, "routers"))
# sys.path.insert(0, os.path.join(os.path.dirname(base_path), "backend"))
from app import app


if __name__ == "__main__":
    import multiprocessing

    # QUAN TRỌNG: Phải là dòng ĐẦU TIÊN trong __main__ để intercept worker processes
    # spawned bởi torch/YOLO trước khi chúng chạy full main code
    multiprocessing.freeze_support()

    # --- Windows API (Single Instance) ---
    import win32event
    import win32api
    import winerror

    # Kiểm tra single instance bằng Mutex
    # Tạo mutex với tên unique cho app này
    mutex = win32event.CreateMutex(None, False, "Global\\AHSO_DRB_OCR_AI_Metalcore_API")
    last_error = win32api.GetLastError()

    if last_error == winerror.ERROR_ALREADY_EXISTS:
        # Đã có instance đang chạy
        sys.exit(0)

    import uvicorn

    is_frozen = getattr(sys, "frozen", False)
    uvicorn.run(
        app if is_frozen else "main:app",
        host="0.0.0.0",
        port=8000,
        reload=not is_frozen,
        log_level="info",
        ws_ping_interval=None,
        ws_ping_timeout=None,
    )
