from PyQt5.QtCore import QObject, pyqtSignal


class Signal(QObject):
    """# Object connect
    pyqtSignal # Object emit
    ...
    """

    # StackedWidget, MainScreen(1)
    switch_screen = pyqtSignal(int)  # MainScreen(1), LoginScreen(0)

    # MainScreen
    show_error_message_main = pyqtSignal(str)  # MainScreen, CameraController
    camera_connected = pyqtSignal()  # CameraController
    camera_disconnected = pyqtSignal()  # CameraController
    PLC_connected = pyqtSignal()  # PLCController
    PLC_disconnected = pyqtSignal()  # PLCController
    PLC_stop = pyqtSignal()  # PLCController
    PLC_start = pyqtSignal()  # PLCController
    send_quantity = pyqtSignal(int, bool, int, int)  # ReferenceImage

    # LoginScreen
    show_error_message_login = pyqtSignal(str)  # LoginScreen

    # CameraController
    connect_camera = pyqtSignal()  # MainScreen
    disconnect_camera = pyqtSignal()  # MainScreen
    grab_image = pyqtSignal()  # MainScreen
    live_camera = pyqtSignal(bool)  # MainScreen
    send_exposure = pyqtSignal(int)  # MainScreen
    update_img_size = pyqtSignal(int, int, int, int)  # MainScreen
    PLC_grab_image = pyqtSignal()  # PLCController

    # ReferenceImage
    image_grapped = pyqtSignal(object, float)  # CameraController
    new_frame_ready = pyqtSignal(bool)  # CameraController
    load_model = pyqtSignal()  # MainScreen
    update_thresholds = pyqtSignal()  # MainScreen
    grap_record = pyqtSignal()  # MainScreen
    save_result = pyqtSignal()  # MainScreen
    update_roi_rect_list = pyqtSignal()  # MainScreen
    move_ROI = pyqtSignal()  # MainScreen

    # PLCController
    connect_PLC = pyqtSignal(object)  # MainScreen - dict params cho TCP/RTU
    disconnect_PLC = pyqtSignal()  # MainScreen
    auto_read_PLC = pyqtSignal(bool)  # MainScreen
    light_PLC = pyqtSignal(bool)  # MainScreen
    send_error_PLC = pyqtSignal()  # MainScreen


signal = Signal()

# =========================================================================================
import numpy as np


class GlobalVariables:
    camera_frame: np.ndarray = None
    camera_time: float = 0


global_vars = GlobalVariables()

# ========================================================================================
import subprocess, os, psutil

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QSpinBox,
    QDoubleSpinBox,
    QDateEdit,
    QTimeEdit,
    QDateTimeEdit,
    QTextEdit,
    QPlainTextEdit,
    QComboBox,
    QTableWidget,
)
from PyQt5.QtWidgets import QMessageBox, QAction, QMainWindow, QInputDialog
from PyQt5.QtCore import QEvent, QObject, pyqtSignal, Qt


# Nhấn đúp gọi phím ảo
class OskEventFilter(QObject):
    def eventFilter(self, obj, event):
        # đường dẫn shortcut
        shortcut_path = os.path.join(
            os.path.expanduser("~"), "Desktop", "osk - Shortcut.lnk"
        )

        # Bắt double click
        if event.type() == QEvent.MouseButtonDblClick:
            if isinstance(
                obj,
                (
                    QLineEdit,
                    QSpinBox,
                    QDoubleSpinBox,
                    QDateEdit,
                    QTimeEdit,
                    QDateTimeEdit,
                    QTextEdit,
                    QPlainTextEdit,
                ),
            ):

                try:
                    # Nếu osk.exe đang chạy thì tắt trước
                    for p in psutil.process_iter(["name"]):
                        if p.info["name"] and p.info["name"].lower() == "osk.exe":
                            p.terminate()
                            p.wait(timeout=2)
                            break

                    # Mở mới lại osk.exe
                    subprocess.Popen(["explorer.exe", shortcut_path])
                except Exception as e:
                    print("Lỗi mở bàn phím ảo:", e)

        return super().eventFilter(obj, event)


# ====================================================================================
import re


def CheckPasswordMessage(s: str, min_length: int = 8) -> str:
    errors = []

    if len(s) < min_length:
        errors.append(f"at least {min_length} characters")
    if not re.search(r"[A-Z]", s):
        errors.append("an uppercase letter (A-Z)")
    if not re.search(r"[a-z]", s):
        errors.append("a lowercase letter (a-z)")
    if not re.search(r"\d", s):
        errors.append("a digit (0-9)")
    if not re.search(r"[^A-Za-z0-9]", s):
        errors.append("a special character (@, #, $, %...)")

    if not errors:
        return True
    else:
        return "Password is invalid: Missing " + ", ".join(errors) + "!"


# ====================================================================================
import ctypes, sys
from ctypes import c_int, byref

SD_FIND = 1
current_file_path = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_file_path, "System8.dll")
hinst = ctypes.windll.LoadLibrary(path)
SecureDongle = hinst.SecureDongle

_dongle_log = {"ok_count": 0}
_DONGLE_OK_LOG_COUNT = 100  # Log OK sau mỗi 100 lần check thành công


def _write_dongle_log(retcode, force=False):
    """Ghi log retcode vào file"""
    from datetime import datetime as _datetime

    # Nếu retcode == 0 (OK), chỉ log sau mỗi _DONGLE_OK_LOG_COUNT lần
    if retcode == 0 and not force:
        _dongle_log["ok_count"] += 1
        if _dongle_log["ok_count"] < _DONGLE_OK_LOG_COUNT:
            return
        _dongle_log["ok_count"] = 0  # Reset counter sau khi log

    try:
        log_path = os.path.join(current_file_path, "dongle_log.txt")
        timestamp = _datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        status = "OK" if retcode == 0 else "ERROR"
        log_line = f"[{timestamp}] retcode={retcode} ({status})\n"

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_line)
    except:
        pass  # Bỏ qua lỗi ghi file


def check_dongle_and_log():
    """
    Đọc retcode từ dongle và ghi log.
    Không retry, không trả về kết quả.
    """
    p1 = c_int(0x015A)
    p2 = c_int(0x2D58)
    p3 = c_int(0xEA8D)
    p4 = c_int(0x5D21)

    buff = bytes(1024)
    handle = c_int(0)
    lp1 = c_int(0)
    lp2 = c_int(0)

    retcode = SecureDongle(
        SD_FIND,
        byref(handle),
        byref(lp1),
        byref(lp2),
        byref(p1),
        byref(p2),
        byref(p3),
        byref(p4),
        buff,
    )
    _write_dongle_log(retcode, force=(retcode != 0))


_DONGLE_RETRY_COUNT = 3  # Số lần retry tối đa
_DONGLE_RETRY_INTERVAL = 1  # Mỗi lần retry cách nhau 1 giây


def initialize_secure_dongle():
    """
    Kiểm tra dongle với retry logic.
    Retry tối đa _DONGLE_RETRY_COUNT lần cho đến khi thành công.
    """
    import time as _time

    p1 = c_int(0x015A)  # mật khẩu mặc định của key
    p2 = c_int(0x2D58)
    p3 = c_int(0xEA8D)  # advance password. Must set to 0 for end user application.
    p4 = c_int(0x5D21)

    retcode = None

    for attempt in range(_DONGLE_RETRY_COUNT):
        buff = bytes(1024)
        handle = c_int(0)
        lp1 = c_int(0)
        lp2 = c_int(0)

        retcode = SecureDongle(
            SD_FIND,
            byref(handle),
            byref(lp1),
            byref(lp2),
            byref(p1),
            byref(p2),
            byref(p3),
            byref(p4),
            buff,
        )

        # Ghi log mỗi lần check (ERROR ghi ngay, OK ghi mỗi 100 lần)
        _write_dongle_log(retcode, force=(retcode != 0))

        # Nếu thành công (retcode == 0), thoát vòng lặp
        if retcode == 0:
            break

        # Chờ trước khi retry (không chờ ở lần cuối)
        if attempt < _DONGLE_RETRY_COUNT - 1:
            _time.sleep(_DONGLE_RETRY_INTERVAL)

    return retcode == 0


# ====================================================================================
def catch_errors(func):
    """Decorator để bắt lỗi trong các hàm của class, phát tín hiệu hiển thị lỗi"""

    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Lấy tên hàm trực tiếp từ object → Cython vẫn giữ
            func_name = func.__name__

            # Bảo vệ chống infinite loop: không emit nếu đang xử lý lỗi
            if not getattr(self, "_in_error_handler", False):
                try:
                    signal.show_error_message_main.emit(f"[{func_name}] {e}")
                except:
                    # Nếu emit signal cũng lỗi → in ra console
                    print(
                        f"[CRITICAL] Failed to emit error signal for [{func_name}]: {e}"
                    )
            else:
                # Đang trong error handler → chỉ in ra console
                print(f"[ERROR in error handler] [{func_name}] {e}")

    return wrapper


# =======================================================================================
import shutil
from pathlib import Path
from datetime import datetime


def delete_folder(path, days):
    ROOT = Path(path)
    FMT = "%d_%m_%Y"
    DAYS = days

    now = datetime.now()

    for folder in ROOT.iterdir():
        if folder.is_dir():
            try:
                folder_date = datetime.strptime(folder.name, FMT)
                if (now - folder_date).days > DAYS:
                    shutil.rmtree(folder)
                    # print(f"Đã xóa thư mục: {folder}")
            except ValueError:
                pass
