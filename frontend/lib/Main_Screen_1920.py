import threading
import time
import os
import sys
import pandas as pd
import psutil

from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QFileDialog
from PyQt5.QtCore import QTimer, QProcess, QTime, QDate, Qt
from PyQt5.QtGui import QTransform

from Global import signal, initialize_secure_dongle, catch_errors, delete_folder
from Camera_Program import CameraController
from Display import ReferenceImage
from PLC import PLCModbus
from Database import DatabaseConnection, BaseModel, Product, CurrentSession, User

db = DatabaseConnection()
BaseModel.use_db(db)
from Authentication import Authentication


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("form_UI/screenMain.ui", self)
        self.camera_controller = CameraController()
        self.reference_image = ReferenceImage(GUI=self)
        self.PLC = PLCModbus()
        self.set_event()
        self.set_value()
        self.set_timer()
        self.set_state()
        # delete_folder(rf"{self.drive}/DRB Metalcore Text Result", 7)

    # Setup
    def set_event(self):
        # signal=================================================================
        signal.show_error_message_main.connect(self.on_show_error_message)
        signal.camera_connected.connect(self.on_camera_connected)
        signal.camera_disconnected.connect(self.on_camera_disconnected)
        signal.PLC_connected.connect(self.on_PLC_connected)
        signal.PLC_disconnected.connect(self.on_PLC_disconnected)
        signal.send_quantity.connect(self.on_count)
        signal.PLC_grab_image.connect(self.on_grab)
        signal.switch_screen.connect(self.right_access)
        signal.PLC_stop.connect(self.on_stop)
        signal.PLC_start.connect(self.on_start)

        # UI=====================================================================
        self.action_logout.triggered.connect(self.on_logout)
        self.button_connect_camera.clicked.connect(signal.connect_camera.emit)
        self.button_disconnect_camera.clicked.connect(signal.disconnect_camera.emit)
        # self.button_connect_PLC.clicked.connect(lambda: signal.connect_PLC.emit(self.line_edit_PLCIP.text(), 1))
        self.button_connect_PLC.clicked.connect(
            lambda: signal.connect_PLC.emit(
                {"protocol_type": "tcp", "ip": self.line_edit_PLCIP.text(), "tries": 1}
            )
        )
        self.button_disconnect_PLC.clicked.connect(signal.disconnect_PLC.emit)
        self.button_grab.clicked.connect(self.on_grab)
        # self.button_grab.clicked.connect(self.on_start)
        self.button_exit.clicked.connect(self.on_exit)
        self.button_live_camera.clicked.connect(self.on_live_camera)
        self.action_open_training_screen.triggered.connect(self.on_goto_training)
        self.button_real_time.clicked.connect(self.on_real_time)
        self.button_save_AI_config.clicked.connect(self.on_save_AI_config)
        self.button_auto.clicked.connect(self.on_auto_mode)
        self.button_manual.clicked.connect(self.on_manual_mode)
        self.button_record.clicked.connect(self.on_record)
        self.button_save_camera.clicked.connect(self.on_save_camera)
        self.combobox_product.currentIndexChanged.connect(self.on_change_product)
        self.action_load_model.triggered.connect(self.on_load_model)
        self.action_update_product_list.triggered.connect(self.on_update_product)
        self.button_on_save_default.clicked.connect(self.on_save_default)
        self.button_save_result_time.clicked.connect(self.on_save_result_time)
        self.button_save_sleep_time.clicked.connect(self.on_save_sleep_time)
        self.button_save_zoom.clicked.connect(self.on_save_zoom)
        self.button_save_PLCIP.clicked.connect(self.on_save_PLCIP)
        self.button_reset_counter.clicked.connect(self.on_reset_counter)
        # self.button_reset_counter.clicked.connect(self.on_stop)
        self.button_authentication.clicked.connect(self.open_authentication)
        self.button_move_ROI_left.clicked.connect(
            lambda: self.on_move_ROI(direction="left")
        )
        self.button_move_ROI_right.clicked.connect(
            lambda: self.on_move_ROI(direction="right")
        )
        self.button_move_ROI_up.clicked.connect(
            lambda: self.on_move_ROI(direction="up")
        )
        self.button_move_ROI_down.clicked.connect(
            lambda: self.on_move_ROI(direction="down")
        )

    def set_value(self):
        self.live_camera_status = False
        self.real_time_status = False
        self.auto_mode_status = False
        # self.OCR_detect_status = True # Mặc định bật OCR detect
        # self.show_ROI_status = self.checkbox_show_ROI.isChecked()
        self.record_status = False
        self.current_product = self.combobox_product.currentText().strip()
        self.count = 0
        self.batch = 0
        self.quantity = 0
        self.result = True
        self.model_path = "IS35R_100_E35.pt"
        self.ng_frame = 0
        self.button_stylesheet_off = """
                QPushButton {
                    background-color: #A6CAEE;
                    border: 2px solid black;
                    border-radius: 12px;
                    padding: 10px 10px;}
                QPushButton:hover {
                    background-color: qlineargradient(
                    spread:pad, 
                    x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #738B95, 
                    stop:1 #BAE5F5);}
                QPushButton:pressed {
                    background-color: qlineargradient(
                    spread:pad, 
                    x1:0, y1:0, x2:0, y2:1, 
                    stop:0  #BAE5F5, 
                    stop:1 #738B95);
                    padding-top: 6px;   /* tạo cảm giác ấn xuống */}"""
        self.button_stylesheet_on = """
                    QPushButton {
                        border: 2px solid black;
                        border-radius: 12px;
                        padding: 10px 10px;
                        background-color: qlineargradient(
                        spread:pad, 
                        x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #738B95, 
                        stop:1 #BAE5F5);}"""

    def set_state(self):
        self.check_secure_dongle()
        self.current_drive()
        self.on_load_setting()
        # self.on_change_product() # on_update_product() gọi luôn on_change_product()
        self.on_update_product()
        self.on_camera_disconnected()
        self.graphics_view_reference.setScene(self.reference_image)
        self.on_real_time()
        self.on_save_AI_config()
        self.current_model_path.setText(self.model_path)
        self.start_clock()
        self.on_get_ROI_value()

        # Delay
        QTimer.singleShot(100, signal.connect_camera.emit)
        QTimer.singleShot(300, self.on_save_camera)
        # QTimer.singleShot(400, lambda: signal.connect_PLC.emit(self.line_edit_PLCIP.text(), 1))
        QTimer.singleShot(
            400,
            lambda: signal.connect_PLC.emit(
                {"protocol_type": "tcp", "ip": self.line_edit_PLCIP.text(), "tries": 1}
            ),
        )
        QTimer.singleShot(400, self.on_live_camera)

        # Set style giao diện
        # self.setStyle("Windows")
        self.setStyleSheet("")
        self.setFont(QtGui.QFont())  # về font mặc định

    def set_timer(self):
        # Checking... label timer
        self.check_timer = QTimer()
        self.dots = 0
        self.check_timer.timeout.connect(
            lambda: (
                setattr(self, "dots", (self.dots + 1) % 4),
                self.label_result.setText("Checking" + "." * self.dots),
            )
        )
        # Stop system timer
        self.stop_timer = QTimer()
        self.stop_timer.setSingleShot(True)  # Chạy 1 lần không lặp lại
        self.stop_timer.timeout.connect(self.turn_off_system)
        # Sau 1 khoảng thời gian từ lúc chạy chương trình nếu ko có tín hiệu chụp thì tắt
        self.stop_timer.start(2 * 60000)

    # Excecute===================================================================
    # signal=====================================================================
    def on_show_error_message(self, error_message):
        """Error handler - KHÔNG dùng @catch_errors để tránh infinite loop"""
        # Set cờ để ngăn recursive error handling
        self._in_error_handler = True
        try:
            if self.live_camera_status:
                signal.live_camera.emit(False)
                self.live_camera_status = False
                self.button_live_camera.setText("Live Camera")
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(error_message)
            msg_box.exec_()
        except Exception as e:
            # Fallback: in ra console thay vì gọi lại signal
            print(f"[CRITICAL] Error in error handler: {e}")
            print(f"[CRITICAL] Original error: {error_message}")
        finally:
            # Luôn reset cờ sau khi xong
            self._in_error_handler = False

    @catch_errors
    def on_count(self, quantity, result, ok_count, ng_count):
        # Đếm số lượng đang hiển thị và kết quả ok/ng hiện tại
        self.quantity = quantity
        self.result = result
        self.label_quantity.setText(str(quantity))

        if result and self.quantity == 5:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("OK")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: rgb(74, 212, 90);
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )
            # Reset ng_frame
            self.ng_frame = 0

        elif self.quantity != 5 or self.ng_frame < 30:
            # Nếu chưa đủ 5 hoặc ng_frame chưa đủ nhiều thì để checking
            if not self.check_timer.isActive():
                # Nếu Checking đang chạy thì ko chạy nữa
                self.label_result.setText("Checking")
                self.dots = 0
                # self.check_timer = QTimer()
                # try:
                #     self.check_timer.timeout.disconnect()
                # except TypeError:
                #     pass  # pass lỗi nếu chưa connect trước đó
                # self.check_timer.timeout.connect(lambda: (
                #     setattr(self, "dots", (self.dots + 1) % 4),
                #     self.label_result.setText("Checking" + "." * self.dots)
                # ))
                self.check_timer.start(500)
                self.label_result.setStyleSheet(
                    """
                                QLabel{
                                font: 50pt;
                                background-color: yellow;
                                color: rgb(14,114,190);
                                border-radius: 7px;}"""
                )
        else:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("FAIL")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: red;
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )

        if self.quantity == 5 and ng_count != 0:
            # Nếu đủ 5 và NG xuất hiện thì đếm số frame
            self.ng_frame += 1

    @catch_errors
    def right_access(self, main_screen=1):
        current_user = CurrentSession.get_column("UserName")
        self.label_current_user.setText(
            f"User: {current_user[0] if current_user else ''}"
        )
        user = User.get_by("UserName", current_user)
        current_role = user[0]["Role"] if user and user[0]["Role"] else "Operator"

        # Admin
        self.button_authentication.setEnabled(True)
        self.button_report.setEnabled(True)

        self.widget_image.setEnabled(True)
        self.widget_hardware_setting.setEnabled(True)
        self.widget_AI_configure.setEnabled(True)
        # self.button_exit.setEnabled(True)
        self.action_load_model.setEnabled(True)
        self.action_select_path_save_image.setEnabled(True)
        self.action_open_training_screen.setEnabled(True)
        self.action_update_product_list.setEnabled(True)
        # self.widget_button.setEnabled(True)
        self.button_grab.setEnabled(True)
        self.button_live_camera.setEnabled(True)
        self.button_real_time.setEnabled(True)
        self.button_manual.setEnabled(True)
        self.button_auto.setEnabled(True)
        self.spinbox_result_time.setEnabled(True)
        self.spinbox_sleep_time.setEnabled(True)

        # Supervisor
        if current_role == "Supervisor":
            self.button_authentication.setEnabled(False)
            self.button_report.setEnabled(False)

        # Operator
        elif current_role == "Operator":
            self.button_authentication.setEnabled(False)
            self.button_report.setEnabled(False)

            self.widget_image.setEnabled(False)
            self.widget_hardware_setting.setEnabled(False)
            self.widget_AI_configure.setEnabled(False)
            # self.button_exit.setEnabled(False)
            self.action_load_model.setEnabled(False)
            self.action_select_path_save_image.setEnabled(False)
            self.action_open_training_screen.setEnabled(False)
            self.action_update_product_list.setEnabled(False)
            # self.widget_button.setEnabled(False)
            self.button_grab.setEnabled(False)
            self.button_live_camera.setEnabled(False)
            self.button_real_time.setEnabled(False)
            self.button_manual.setEnabled(False)
            self.button_auto.setEnabled(False)
            self.spinbox_result_time.setEnabled(False)
            self.spinbox_sleep_time.setEnabled(False)

    @catch_errors
    def on_stop(self):
        # print("stoping")
        # Chạy timer mới
        self.stop_timer.start(self.spinbox_sleep_time.value() * 60000)

    @catch_errors
    def on_start(self):
        # print("sta")
        if self.stop_timer.isActive():
            # Ngắt timer
            self.stop_timer.stop()
        # Bật live camera
        if not self.live_camera_status:
            signal.connect_camera.emit()
            signal.live_camera.emit(True)
            self.live_camera_status = True
            self.button_live_camera.setText("Live ON")
        # Bật đèn bên PLC.py
        # Gửi tín hiệu bật AI
        if not self.real_time_status:
            self.real_time_status = True
            self.button_real_time.setText("AI Checking")
        # Khóa lại các nút theo user
        self.right_access()

    # UI=========================================================================
    @catch_errors
    def on_logout(self, checked=False):
        signal.switch_screen.emit(0)  # LoginScreen(0)

    @catch_errors
    def on_camera_connected(self):
        # Doi tran thai nut nhan
        self.button_connect_camera.setText("Connected")
        self.button_connect_camera.setStyleSheet(self.button_stylesheet_on)
        # Khoa cheo
        self.button_connect_camera.setEnabled(False)
        self.button_disconnect_camera.setEnabled(True)
        self.button_disconnect_camera.setText("Disconnect")
        self.button_disconnect_camera.setStyleSheet(self.button_stylesheet_off)
        # MỞ Khóa các nút lấy hình
        self.button_grab.setEnabled(True)
        self.button_live_camera.setEnabled(True)

    @catch_errors
    def on_camera_disconnected(self):
        # Doi tran thai nut nhan
        self.button_disconnect_camera.setText("Disconnected")
        self.button_disconnect_camera.setStyleSheet(self.button_stylesheet_on)
        # Khoa cheo
        self.button_disconnect_camera.setEnabled(False)
        self.button_connect_camera.setEnabled(True)
        self.button_connect_camera.setText("Connect")
        self.button_connect_camera.setStyleSheet(self.button_stylesheet_off)
        # Khóa các nút lấy hình
        self.button_grab.setEnabled(False)
        self.button_live_camera.setEnabled(False)

    @catch_errors
    def on_PLC_connected(self):
        self.on_auto_mode()
        # Doi tran thai nut nhan
        self.button_connect_PLC.setText("Connected")
        self.button_connect_PLC.setStyleSheet(self.button_stylesheet_on)
        # Khoa cheo
        self.button_connect_PLC.setEnabled(False)
        self.button_disconnect_PLC.setEnabled(True)
        self.button_disconnect_PLC.setText("Disconnect")
        self.button_disconnect_PLC.setStyleSheet(self.button_stylesheet_off)

    @catch_errors
    def on_PLC_disconnected(self):
        # Doi tran thai nut nhan
        self.button_disconnect_PLC.setText("Disconnected")
        self.button_disconnect_PLC.setStyleSheet(self.button_stylesheet_on)
        # Khoa cheo
        self.button_disconnect_PLC.setEnabled(False)
        self.button_connect_PLC.setEnabled(True)
        self.button_connect_PLC.setText("Connect")
        self.button_connect_PLC.setStyleSheet(self.button_stylesheet_off)

    @catch_errors
    def on_exit(self, checked=False):
        signal.live_camera.emit(False)
        signal.disconnect_camera.emit()
        signal.disconnect_PLC.emit()
        if db and db.conn.open:
            db.close()
            # print("Đã đóng kết nối MySQL")
        time.sleep(0.01)
        QtWidgets.QApplication.quit()  # Thoát ứng dụng

    @catch_errors
    def on_grab(self, checked=False):
        # Nếu ko live thì chụp hình và hiển thị và lưu hình
        if not self.live_camera_status:
            self.scale_zoom_factor()
            signal.grap_image.emit()
        # Nếu ko
        else:
            # Hiển thị kết quả trong 1 khoảng thời gian
            signal.live_camera.emit(False)
            self.live_camera_status = False
            result_time = self.spinbox_result_time.value()
            QTimer.singleShot(
                result_time * 1000, lambda: setattr(self, "live_camera_status", True)
            )
            QTimer.singleShot(result_time * 1000, lambda: signal.live_camera.emit(True))
            # Khóa tạm thời nút grab ko cho chụp nhiều lần tránh lỗi khi đang ko auto
            if not self.auto_mode_status:
                self.button_grab.setEnabled(False)
                QTimer.singleShot(
                    result_time * 1000, lambda: self.button_grab.setEnabled(True)
                )

            # Lưu hình kết quả
            signal.save_result.emit()
            # Lưu hình
            if self.record_status and self.quantity != 0:
                signal.grap_record.emit()

        # Chốt kết quả (cộng dồn count và batch)
        self.count += self.quantity
        counter = self.count % self.spinbox_default_value.value()
        self.label_count.setText(str(counter))
        self.batch = self.count // self.spinbox_default_value.value()
        self.label_batch.setText(str(self.batch))

        # Nếu sô lượng khác 0 thì chốt kết quả ok/fail
        if self.quantity != 0:
            if self.result:
                if self.check_timer.isActive():
                    # Nếu Checking đang chạy thì dừng
                    self.check_timer.stop()
                self.label_result.setText("OK")
                self.label_result.setStyleSheet(
                    """
                                QLabel{
                                background-color: rgb(74, 212, 90);
                                color: rgb(14,114,190);
                                border-radius: 7px;}"""
                )
            else:
                if self.check_timer.isActive():
                    # Nếu Checking đang chạy thì dừng
                    self.check_timer.stop()
                self.label_result.setText("FAIL")
                self.label_result.setStyleSheet(
                    """
                                QLabel{
                                background-color: red;
                                color: rgb(14,114,190);
                                border-radius: 7px;}"""
                )
                # Gửi tín hiệu đèn error cho PLC
                signal.send_error_PLC.emit()

        # # Nếu stop timer đang đếm thì ngắt stop timer vì còn chạy
        # if self.stop_timer.isActive():
        #     # Ngắt timer
        #     self.stop_timer.stop()

        # Reset stop timer nếu nhận được tín hiệu chụp
        self.stop_timer.start(self.spinbox_sleep_time.value() * 60000)

    @catch_errors
    def on_live_camera(self, checked=False):
        # Dừng label Checking
        if self.result:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("OK")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: rgb(74, 212, 90);
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )
        else:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("FAIL")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: red;
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )

        self.scale_zoom_factor()
        if self.live_camera_status == False:  # Nếu đang không live
            # Gửi tín hiệu bật live camera
            signal.live_camera.emit(True)
            self.live_camera_status = True
            self.button_live_camera.setText("Live ON")
            # Khóa nút disconnect camera
            self.button_disconnect_camera.setEnabled(False)

        else:  # Nếu đang live
            # Gửi tín hiệu tắt live camera
            signal.live_camera.emit(False)
            self.live_camera_status = False
            self.button_live_camera.setText("Live Camera")
            # Mở Khóa nút disconnect camera
            self.button_disconnect_camera.setEnabled(True)

    @catch_errors
    def on_goto_training(self, checked=False):
        self.on_manual_mode()
        if self.live_camera_status:
            self.on_live_camera()
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        exe_path = os.path.join(
            base_dir, "OCR_DeepLearning_Software", "OCR_DeepLearning_Software.exe"
        )
        exe_dir = os.path.join(base_dir, "OCR_DeepLearning_Software")
        # self.setEnabled(False)
        self.hide()
        self.proc = QProcess(self)
        self.proc.setWorkingDirectory(exe_dir)
        # self.proc.finished.connect(lambda: self.setEnabled(True))
        self.proc.finished.connect(self.show)
        self.proc.start(exe_path)

    @catch_errors
    def on_real_time(self, checked=False):
        if not self.model_path:
            QMessageBox.warning(self, "Warning", "Please select a model AI!")
            self.on_load_model()
        if self.model_path:
            if self.real_time_status == False:
                # Gửi tín hiệu bật AI
                self.real_time_status = True
                self.button_real_time.setText("AI Checking")

            else:
                # Gửi tín hiệu tắt AI
                self.real_time_status = False
                self.button_real_time.setText("Real-time")

        # Dừng label Checking
        if self.result:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("OK")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: rgb(74, 212, 90);
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )
        else:
            if self.check_timer.isActive():
                # Nếu Checking đang chạy thì dừng
                self.check_timer.stop()
            self.label_result.setText("FAIL")
            self.label_result.setStyleSheet(
                """
                            QLabel{
                            background-color: red;
                            color: rgb(14,114,190);
                            border-radius: 7px;}"""
            )

    @catch_errors
    def on_save_AI_config(self, checked=False):

        self.show_ROI_status = self.checkbox_show_ROI.isChecked()
        self.acceptance_threshold = float(
            self.combobox_acceptance_threshold.currentText()
        )
        self.mns_threshold = float(self.combobox_mns_threshold.currentText())
        Product.update(
            "ProductName",
            self.current_product,
            {
                "ThresholdAccept": self.acceptance_threshold,
                "ThresholdMns": self.mns_threshold,
            },
        )

        if hasattr(self, "ROIx1"):
            CurrentSession.update(
                "ID",
                1,
                {
                    "ROIx1": self.ROIx1,
                    "ROIx2": self.ROIx2,
                    "ROIx3": self.ROIx3,
                    "ROIx4": self.ROIx4,
                    "ROIx5": self.ROIx5,
                    "ROIy1": self.ROIy1,
                    "ROIy2": self.ROIy2,
                    "ROIy3": self.ROIy3,
                    "ROIy4": self.ROIy4,
                    "ROIy5": self.ROIy5,
                },
            )

    @catch_errors
    def on_record(self, checked=False):
        if self.record_status == False:  # Bật
            # Gửi tín hiệu bật
            self.record_status = True
            self.button_record.setText("Recording")

        else:  # Tắt
            # Gửi tín hiệu tắt
            self.record_status = False
            self.button_record.setText("Record")

    @catch_errors
    def on_auto_mode(self, checked=False):
        self.auto_mode_status = True
        # Gửi tín hiệu bật auto mode
        signal.auto_read_PLC.emit(True)
        # Khoa nut auto
        self.button_auto.setText("Auto ON")
        self.button_auto.setStyleSheet(self.button_stylesheet_on)
        self.button_auto.setEnabled(False)
        self.button_grab.setEnabled(False)

        # Mo khoa nut manual
        self.button_manual.setText("Manual")
        self.button_manual.setStyleSheet(self.button_stylesheet_off)
        self.button_manual.setEnabled(True)

    @catch_errors
    def on_manual_mode(self, checked=False):
        self.auto_mode_status = False
        # Gửi tín hiệu tat auto mode
        signal.auto_read_PLC.emit(False)
        # Khoa nut manual
        self.button_manual.setText("Manual ON")
        self.button_manual.setStyleSheet(self.button_stylesheet_on)
        self.button_manual.setEnabled(False)

        # Mo khoa nut auto
        self.button_auto.setText("Auto")
        self.button_auto.setStyleSheet(self.button_stylesheet_off)
        self.button_auto.setEnabled(True)
        self.button_grab.setEnabled(True)

    @catch_errors
    def on_save_camera(self, checked=False):
        # Update value
        exposure_time = self.spinbox_exposure_time.value()
        signal.send_exposure.emit(exposure_time)
        self.offset_x = self.spinbox_offset_x.value()
        self.offset_y = self.spinbox_offset_y.value()
        self.image_width = self.spinbox_image_width.value()
        self.image_height = self.spinbox_image_height.value()
        signal.update_img_size.emit()

        # Update database
        Product.update("ProductName", self.current_product, {"Exposure": exposure_time})
        CurrentSession.update(
            "ID",
            "1",
            {
                "OffsetX": self.offset_x,
                "OffsetY": self.offset_y,
                "ImageWidth": self.image_width,
                "ImageHeight": self.image_height,
            },
        )
        self.label_dimention_image.setText(f"{self.image_width} x {self.image_height}")

    # @catch_errors
    def on_change_product(self, value=None):
        change_real_time_status_flag = False
        if self.real_time_status:
            # Tắt realtime để đổi model
            self.real_time_status = False
            change_real_time_status_flag = True
            time.sleep(0.3)

        # start_time = time.time()

        self.current_product = self.combobox_product.currentText().strip()
        self.label_product.setText(self.current_product)
        self.label_quantity.setText("0")
        self.count = 0
        self.label_count.setText("0")
        self.batch = 0
        self.label_batch.setText("0")

        # Read excel
        df = pd.read_excel(rf"{self.drive}/DRB product text.xlsx")
        model_path = df.loc[
            df["Product name"] == self.current_product, "Model path"
        ].values
        if len(model_path) == 0:
            return
        if pd.isna(model_path[0]):
            signal.show_error_message_main.emit("Product has no Model AI!")
            return
        self.model_path = model_path[0]
        signal.load_model.emit()

        # end_time = time.time()
        # processing_time = (end_time - start_time)*1000
        # print("change", processing_time)

        self.current_model_path.setText(self.model_path)

        # Load product setting
        if self.current_product in ["", None]:
            QMessageBox.warning(self, "Warning", "Current product is None!")
            return
        settings = Product.get_by("ProductName", self.current_product)
        if not settings or len(settings) == 0:
            signal.show_error_message_main.emit("Invalid product!")
            return
        if not isinstance(settings, list):
            QMessageBox.warning(
                self, "Warning", f"Database returned unexpected: {settings}"
            )
            return
        (
            self.spinbox_default_value.setValue(settings[0]["DefaultNumber"])
            if settings[0]["DefaultNumber"]
            else self.spinbox_default_value.setValue(160)
        )
        (
            self.spinbox_exposure_time.setValue(settings[0]["Exposure"])
            if settings[0]["Exposure"]
            else self.spinbox_exposure_time.setValue(3500)
        )
        (
            self.combobox_acceptance_threshold.setCurrentText(
                str(settings[0]["ThresholdAccept"])
            )
            if settings[0]["ThresholdAccept"]
            else self.combobox_acceptance_threshold.setCurrentText("0.5")
        )
        (
            self.combobox_mns_threshold.setCurrentText(str(settings[0]["ThresholdMns"]))
            if settings[0]["ThresholdMns"]
            else self.combobox_mns_threshold.setCurrentText("0.5")
        )
        # print(settings)
        # print(settings[0])
        # print(settings[0]["Exposure"])
        if change_real_time_status_flag:
            # Nếu đã tắt realtime thì bật realtime lên lại nếu ko thì ko bật
            self.real_time_status = True

        # Cập nhật dung lượng ổ đĩa
        self.load_usage_disk()

    @catch_errors
    def on_load_model(self, checked=False):
        if self.real_time_status:
            self.real_time_status = False
            time.sleep(0.3)
        model_path, _ = QFileDialog.getOpenFileName(
            None,  # Không cần truyền đối tượng QWidget ở đây
            "Select model",
            "",
            "Model files (*.pt);;All Files (*)",
        )
        if not model_path:
            signal.show_error_message_main.emit("Model AI is not selected!")
            return
        self.model_path = model_path
        signal.load_model.emit()
        self.current_model_path.setText(self.model_path)
        self.real_time_status = True

    @catch_errors
    def on_update_product(self, checked=False):
        df = pd.read_excel(rf"{self.drive}/DRB product text.xlsx")
        product_list = df["Product name"].tolist()
        self.combobox_product.clear()
        self.combobox_product.addItems(product_list)
        for product in product_list:
            Product.insert_or_update({"ProductName": product})

    @catch_errors
    def on_save_default(self, checked=False):

        product = self.combobox_product.currentText().strip()
        default = self.spinbox_default_value.value()
        Product.update("ProductName", product, {"DefaultNumber": default})

    @catch_errors
    def on_save_result_time(self, checked=False):
        result_time = self.spinbox_result_time.value()
        CurrentSession.update("ID", 1, {"ResultTime": result_time})

    @catch_errors
    def on_save_sleep_time(self, checked=False):
        sleep_time = self.spinbox_sleep_time.value()
        CurrentSession.update("ID", 1, {"SleepTime": sleep_time})

    @catch_errors
    def on_save_zoom(self, checked=False):
        zoom_factor = float(self.combobox_zoom_factor.currentText())
        CurrentSession.update("ID", 1, {"ZoomFactor": zoom_factor})

    @catch_errors
    def on_save_PLCIP(self, checked=False):
        plc_ip = self.line_edit_PLCIP.text()
        CurrentSession.update("ID", 1, {"PLCIP": plc_ip})

    @catch_errors
    def on_load_setting(self):
        settings = CurrentSession.get_by("ID", 1)
        self.spinbox_result_time.setValue(settings[0]["ResultTime"])
        self.spinbox_sleep_time.setValue(settings[0]["SleepTime"])
        self.combobox_zoom_factor.setCurrentText(str(settings[0]["ZoomFactor"]))
        self.spinbox_offset_x.setValue(settings[0]["OffsetX"])
        self.spinbox_offset_y.setValue(settings[0]["OffsetY"])
        self.spinbox_image_width.setValue(settings[0]["ImageWidth"])
        self.spinbox_image_height.setValue(settings[0]["ImageHeight"])
        self.line_edit_PLCIP.setText(str(settings[0]["PLCIP"]))

    @catch_errors
    def on_reset_counter(self, checked=False):
        # self.current_product = self.combobox_product.currentText()
        # self.label_product.setText(self.current_product)
        # self.label_quantity.setText("0")
        self.count = 0
        self.label_count.setText("0")
        self.batch = 0
        self.label_batch.setText("0")
        QMessageBox.information(
            self, "Success", "Reset Counter and Batch successfully!"
        )

    @catch_errors
    def open_authentication(self, checked=False):
        self.on_manual_mode()
        if self.live_camera_status:
            self.on_live_camera()
        self.authentication = Authentication()
        # self.authentication.setWindowFlags(
        #     self.authentication.windowFlags() | Qt.WindowStaysOnTopHint
        # )
        self.setEnabled(False)
        self.authentication.closed.connect(lambda: self.setEnabled(True))
        self.authentication.show()

    @catch_errors
    def turn_off_system(self):
        # print("stop")
        # Tắt đèn
        signal.light_PLC.emit(False)
        # Tắt live camera
        if self.live_camera_status:
            signal.live_camera.emit(False)
            self.live_camera_status = False
            self.button_live_camera.setText("Live Camera")
            QTimer.singleShot(400, signal.disconnect_camera.emit)

        # Gửi tín hiệu tắt AI
        if self.real_time_status:
            self.real_time_status = False
            self.button_real_time.setText("Real-time")

        # Xóa thư mục kết quả cũ (chạy trong background thread để không đóng băng UI)
        threading.Thread(
            target=delete_folder,
            args=(rf"{self.drive}/DRB Metalcore Text Result", 6),
            daemon=True,
        ).start()

    @catch_errors
    def on_get_ROI_value(self):
        value = CurrentSession.get_by("ID", 1)
        self.ROIx1 = value[0]["ROIx1"]
        self.ROIx2 = value[0]["ROIx2"]
        self.ROIx3 = value[0]["ROIx3"]
        self.ROIx4 = value[0]["ROIx4"]
        self.ROIx5 = value[0]["ROIx5"]
        self.ROIy1 = value[0]["ROIy1"]
        self.ROIy2 = value[0]["ROIy2"]
        self.ROIy3 = value[0]["ROIy3"]
        self.ROIy4 = value[0]["ROIy4"]
        self.ROIy5 = value[0]["ROIy5"]

    @catch_errors
    def on_move_ROI(self, direction, checked=False):
        # Di chuyển ROI
        if direction == "left":
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 1
            ):
                self.ROIx1 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 2
            ):
                self.ROIx2 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 3
            ):
                self.ROIx3 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 4
            ):
                self.ROIx4 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 5
            ):
                self.ROIx5 -= 10

        if direction == "right":
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 1
            ):
                self.ROIx1 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 2
            ):
                self.ROIx2 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 3
            ):
                self.ROIx3 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 4
            ):
                self.ROIx4 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 5
            ):
                self.ROIx5 += 10

        if direction == "up":
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 1
            ):
                self.ROIy1 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 2
            ):
                self.ROIy2 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 3
            ):
                self.ROIy3 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 4
            ):
                self.ROIy4 -= 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 5
            ):
                self.ROIy5 -= 10

        if direction == "down":
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 1
            ):
                self.ROIy1 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 2
            ):
                self.ROIy2 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 3
            ):
                self.ROIy3 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 4
            ):
                self.ROIy4 += 10
            if (
                self.checkbox_move_all_ROI.isChecked()
                or self.spinbox_ROI_to_move.value() == 5
            ):
                self.ROIy5 += 10

        signal.move_ROI.emit()

    # Function==================================================================
    def scale_zoom_factor(self):
        transform = QTransform()
        zoom_factor = float(self.combobox_zoom_factor.currentText())
        transform.scale(zoom_factor, zoom_factor)
        self.graphics_view_reference.setTransform(transform)

    @catch_errors
    def start_clock(self):
        # Tạo QTimer để cập nhật mỗi giây
        self.timer_clock = QTimer(self)
        self.timer_clock.timeout.connect(self.update_clock)
        self.timer_clock.start(1000)

        # Hiển thị lần đầu
        self.update_clock()

    def update_clock(self):
        now = (
            QDate.currentDate().toString("dd/MM/yyyy")
            + "  "
            + QTime.currentTime().toString("HH:mm:ss")
        )
        self.label_clock.setText(now)

    def current_drive(self):
        # Thu muc chua file python hien tai
        if getattr(sys, "frozen", False):
            # Neu chay tu file exe
            # sys.executable = D:\MyApp\main.exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Neu chay tu file python
            # sys.modules[__name__].__file__ = D:\MyApp\lib\Main_Screen.py
            module_dir = os.path.dirname(sys.modules[__name__].__file__)
            # Đi lên 1 cấp để tới MyApp
            base_dir = os.path.abspath(os.path.join(module_dir, ".."))

        # Lấy ổ đĩa (C:\, D:\, E:\ ...)
        self.drive = os.path.splitdrive(base_dir)[0]

    @catch_errors
    def closeEvent(self, event):
        try:
            signal.live_camera.emit(False)
            signal.disconnect_camera.emit()
            signal.disconnect_PLC.emit()
        except:
            signal.show_error_message_main.emit("Error when closing camera/PLC!")
        try:
            if db and db.conn.open:
                db.close()
                print("Đã đóng kết nối MySQL")
        except:
            signal.show_error_message_main.emit("Error when closing database!")
            time.sleep(0.01)
        event.accept()

    def check_secure_dongle(self):
        if not initialize_secure_dongle():
            signal.show_error_message_main.emit("License key not found!")
            sys.exit(0)

    # Đọc dung lượng ổ đĩa
    def load_usage_disk(self):
        usage = psutil.disk_usage(self.drive)
        self.progressbar_stored.setValue(usage.percent)
