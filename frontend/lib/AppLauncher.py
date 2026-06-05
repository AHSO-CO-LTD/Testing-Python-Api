import os
import sys
import json
import subprocess
import time
import logging

import requests
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QDialog, QFrame, QVBoxLayout, QLabel, QProgressBar

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
_DEFAULT_CONFIG = {"api_host": "localhost", "api_port": 8000}


def load_config(base_path: str) -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    config_path = os.path.join(base_path, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            logger.warning("Không đọc được config.json: %s — dùng mặc định", e)
    return cfg


# ─────────────────────────────────────────────
# Splash Screen
# ─────────────────────────────────────────────
class SplashScreen(QDialog):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(480, 220)
        self._build_ui()
        self._center()

    def _build_ui(self):
        frame = QFrame(self)
        frame.setGeometry(0, 0, 480, 220)
        frame.setStyleSheet(
            "QFrame {"
            "  background-color: #1a2236;"
            "  border-radius: 14px;"
            "  border: 1px solid #2e4070;"
            "}"
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(40, 28, 40, 28)
        layout.setSpacing(8)

        _base = "background: transparent; border: none;"

        title = QLabel("VisionCenter OCR AI")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            f"color: #e8eaf6; font-size: 22px; font-weight: bold; {_base}"
        )
        layout.addWidget(title)

        subtitle = QLabel("DRB OCR AI System")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: #5c7ac9; font-size: 12px; {_base}")
        layout.addWidget(subtitle)

        layout.addStretch()

        self.status_label = QLabel("Starting...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet(f"color: #90caf9; font-size: 12px; {_base}")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # indeterminate
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar         { background-color: #253050; border-radius: 2px; border: none; }"
            "QProgressBar::chunk { background-color: #5c6bc0; border-radius: 2px; }"
        )
        layout.addWidget(self.progress_bar)

    def _center(self):
        geo = QtWidgets.QApplication.primaryScreen().availableGeometry()
        self.move(
            (geo.width() - self.width()) // 2,
            (geo.height() - self.height()) // 2,
        )

    def set_status(self, text: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            "color: #90caf9; font-size: 12px; background: transparent; border: none;"
        )

    def set_error(self, text: str):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(
            "color: #ef5350; font-size: 12px; background: transparent; border: none;"
        )
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        QtWidgets.QApplication.processEvents()


# ─────────────────────────────────────────────
# Background thread: check / start API
# ─────────────────────────────────────────────
class APIStartThread(QThread):
    status_changed = pyqtSignal(str)
    ready = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, api_url: str, api_exe: str):
        super().__init__()
        self.api_url = api_url
        self.api_exe = api_exe
        self.proc = None

    def _ping(self) -> bool:
        try:
            r = requests.get(f"{self.api_url}/", timeout=1)
            return r.status_code == 200
        except Exception:
            return False

    def run(self):
        # Bước 1: API đã chạy sẵn chưa?
        self.status_changed.emit("Checking server...")
        if self._ping():
            self.ready.emit()
            return

        # Bước 2: Start api exe
        self.status_changed.emit("Starting server...")

        if not os.path.exists(self.api_exe):
            self.failed.emit(f"{os.path.basename(self.api_exe)} not found")
            return

        try:
            self.proc = subprocess.Popen(
                [self.api_exe],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            self.failed.emit(f"Failed to start server: {e}")
            return

        # Bước 3: Chờ API sẵn sàng (tối đa 20 giây)
        for attempt in range(40):
            time.sleep(0.5)

            if self.proc.poll() is not None:
                self.failed.emit(
                    f"Server exited unexpectedly (code {self.proc.returncode})"
                )
                return

            self.status_changed.emit(
                f"Waiting for server... ({(attempt + 1) * 0.5:.0f}s)"
            )
            if self._ping():
                self.ready.emit()
                return

        self.failed.emit("Server not responding (timeout 20s)")


# ─────────────────────────────────────────────
# AppLauncher — orchestrator chính
# ─────────────────────────────────────────────
class AppLauncher:
    def __init__(self, base_path: str, module_path: str):
        self.base_path = base_path
        self.module_path = module_path
        self._window = None

    def run(self, qt_app: QtWidgets.QApplication):
        self._qt_app = qt_app

        cfg = load_config(self.base_path)
        api_url = f"http://{cfg['api_host']}:{cfg['api_port']}"
        api_exe = os.path.join(os.path.dirname(self.base_path), "api", "main.exe")

        splash = SplashScreen()
        splash.show()
        QtWidgets.QApplication.processEvents()

        self._thread = APIStartThread(api_url, api_exe)
        self._thread.status_changed.connect(splash.set_status)
        self._thread.ready.connect(lambda: self._on_ready(splash))
        self._thread.failed.connect(lambda msg: self._on_failed(splash, msg, qt_app))
        self._thread.start()

    def _on_ready(self, splash):
        splash.set_status("Loading interface...")
        QtWidgets.QApplication.processEvents()  # flush repaint trước khi load UI nặng
        # CWD phải trỏ đến thư mục chứa form_UI/ để loadUi() dùng relative path
        os.chdir(self.base_path)
        if self.module_path not in sys.path:
            sys.path.insert(0, self.module_path)

        from StackUI import StackedWidget

        self._window = StackedWidget()  # lưu vào self để tránh Python GC thu hồi
        self._window.setCurrentIndex(0)
        self._window._api_proc = self._thread.proc  # None nếu API đã chạy sẵn

        original_close = self._window.__class__.__dict__.get("closeEvent")

        def _close_event(self_win, event):
            if self_win._api_proc and self_win._api_proc.poll() is None:
                self_win._api_proc.terminate()
                try:
                    self_win._api_proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self_win._api_proc.kill()
            if original_close:
                original_close(self_win, event)
            else:
                event.accept()

        self._window.__class__.closeEvent = _close_event

        splash.close()
        self._window.showFullScreen()
        logger.info("Giao diện đã tải xong")

    def _on_failed(self, splash, msg: str, qt_app):
        splash.set_error(f"Error: {msg}")
        QTimer.singleShot(6000, qt_app.quit)
