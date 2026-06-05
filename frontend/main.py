# ===== SAFE IMPORT ZONE for PyInstaller =====
# Các thư viện dùng trong .pyd (lib/) mà PyInstaller không tự detect được.
# Stdlib và thư viện có hook tốt (torch...) xử lý qua hiddenimports trong .spec.

import os, sys, multiprocessing  # dùng trực tiếp trong main.py

# --- Data / Database ---
import numpy as np
import pandas as pd
import pymysql
from pymysql.err import MySQLError

# --- HTTP / WebSocket Client ---
import requests
import websocket
import psutil

# --- Communication / PLC (không có hook chuẩn) ---
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import pymodbus
import pymcprotocol

# --- Windows API (Single Instance) ---
import win32event
import win32api
import winerror

# --- Image / Vision ---
import cv2
from pypylon import pylon  # không có hook chuẩn

# --- GUI (PyQt5) ---
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# ===== END SAFE IMPORT ZONE =====


# Lấy thư mục chứa file main.py hoặc main.exe
if getattr(sys, "frozen", False):
    # Đang chạy trong EXE (PyInstaller)
    base_path = os.path.dirname(sys.executable)
else:
    # Đang chạy Python bình thường
    base_path = os.path.dirname(os.path.abspath(__file__))

module_path = os.path.join(base_path, "module")


if __name__ == "__main__":
    # QUAN TRỌNG: Phải có dòng này khi đóng EXE để tránh spawn vô hạn processes
    multiprocessing.freeze_support()

    # Kiểm tra single instance bằng Mutex
    # Tạo mutex với tên unique cho app này
    mutex = win32event.CreateMutex(None, False, "Global\\AHSO_DRB_OCR_AI_Metalcore_UI")
    last_error = win32api.GetLastError()

    if last_error == winerror.ERROR_ALREADY_EXISTS:
        # Đã có instance đang chạy
        sys.exit(0)

    sys.path.insert(0, module_path)
    from AppLauncher import AppLauncher

    app = QtWidgets.QApplication(sys.argv)
    launcher = AppLauncher(base_path, module_path)
    launcher.run(app)
    sys.exit(app.exec_())
