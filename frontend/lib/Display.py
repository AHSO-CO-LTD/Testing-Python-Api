import cv2
from datetime import datetime
import os
import sys
import time
import threading
import re
import numpy as np

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (
    QGraphicsScene,
    QMessageBox,
    QGraphicsRectItem,
    QGraphicsPolygonItem,
    QGraphicsLineItem,
    QGraphicsTextItem,
    QGraphicsEllipseItem,
)
from PyQt5.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QFont
from PyQt5.QtCore import QTimer, QProcess, pyqtSignal

from Global import (
    signal,
    global_vars,
    initialize_secure_dongle,
    catch_errors,
    check_dongle_and_log,
)

from API_client import APIClient


class ReferenceImage(QGraphicsScene):
    update_OCR_text = pyqtSignal()

    def __init__(self, parent=None, GUI=None):
        super().__init__(parent)
        self.GUI = GUI
        self.pixmap_item = self.addPixmap(QPixmap())  # Tạo sẵn 1 item để tái sử dụng
        # self.OCR_DEEP_LEARNING_TOOL = OCR_DEEP_LEARNING()
        self.api_client = APIClient(base_url="http://localhost:8000/api/v1")
        self.set_event()
        self.set_value()
        self.set_state()

    def set_event(self):
        # signal.image_grapped.connect(self.on_show_grapped_image)
        signal.new_frame_ready.connect(self.on_show_grapped_image)
        signal.load_model.connect(self.on_load_model)
        signal.update_thresholds.connect(self.on_update_thresholds)
        signal.grap_record.connect(self.on_record_crop)
        signal.save_result.connect(self.on_save_result)
        signal.update_roi_rect_list.connect(self.on_update_roi_rect_list)
        signal.move_ROI.connect(self.on_move_ROI)

    def set_value(self):
        # Biến nội Class
        # Create default ROI
        # self.roi_rect_list = [[410+300-self.GUI.offset_x, 260, 300, 440, 0], # x, y, w, h, color
        #                     [890+300-self.GUI.offset_x, 260, 300, 440, 0],
        #                     [1370+300-self.GUI.offset_x, 260, 300, 440, 0],
        #                     [1850+300-self.GUI.offset_x, 260, 300, 440, 0],
        #                     [2330+300-self.GUI.offset_x, 260, 300, 440, 0]
        #                     ]
        self.roi_rect_list = []
        self.single_OCR_text = []
        self.continuous_OCR_text = []
        # self.model_OCR = self.OCR_DEEP_LEARNING_TOOL.Load_Model_OCR("IS35R_100_E35.pt")
        self.thread_OCR_detect = False
        self.new_pixmap = None
        self.result = True
        self.quantity = 0
        self.fps_start_time = 0  # Wall time bắt đầu đếm FPS
        self.fps_count = 0
        self._inference_lock = threading.Lock()
        self._displaying = False  # Flag chống xử lý frame trùng lặp

    def set_state(self):
        self.current_drive()
        self.api_client.ws_connect()

    # Excecute=======================================================================
    @catch_errors
    def on_show_grapped_image(self, is_continuous=False):
        # Bỏ qua signal nếu đang xử lý frame trước (chống xử lý frame trùng lặp)
        if is_continuous and self._displaying:
            return
        self._displaying = True

        img = global_vars.camera_frame
        if img is None or img.size == 0:
            signal.show_error_message_main.emit("Image not found or empty!")
            return

        # Crop hình
        # x, y, w, h = (
        #     self.GUI.offset_x,
        #     self.GUI.offset_y,
        #     self.GUI.image_width,
        #     self.GUI.image_height,
        # )
        # img = img[y : y + h, x : x + w]

        # Cắt nhiều hình==========================================================================
        # # Đường dẫn đến thư mục chứa ảnh
        # folder_path = f"E:/Image"
        # # Duyệt qua tất cả các file trong thư mục
        # for filename in os.listdir(folder_path):
        #     if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
        #         img_path = os.path.join(folder_path, filename)
        #         img = cv2.imread(img_path)
        # ==========================================================================
        img = cv2.imread(
            r"E:\DRB Metalcore Text Result\Data\Image_20251026160331293.bmp"
        )

        # Kiểm tra ảnh có hợp lệ không
        if img is None or img.size == 0:
            signal.show_error_message_main.emit("Image crop is empty!")
            return

        self.img_crop = img.copy()
        img_crop = self.img_crop

        # Chuyển BGR (OpenCV) sang RGB (Qt)
        if img_crop is not None and img_crop.size > 0:
            height, width, channels = img_crop.shape
            self.width = width  # lấy độ rộng của hình để các hàm khác vẽ ROI
            bytes_per_line = channels * width

            # Tạo QImage trực tiếp từ numpy buffer
            qimage = QImage(
                img_crop.data, width, height, bytes_per_line, QImage.Format_RGB888
            )

            # QImage -> QPixmap
            pixmap = QPixmap.fromImage(qimage)
            self.pixmap = pixmap  # Lưu pixmap vào biến instance
        else:
            signal.show_error_message_main.emit("Image crop is empty!")
            return

        # Nếu ko realtime thì hiển thị hình bình thường
        if not self.GUI.real_time_status:
            if not self.GUI.show_ROI_status:
                # Cập nhật nội dung ảnh cho item cũ thay vì tạo item mới
                self.pixmap_item.setPixmap(pixmap)

            if self.GUI.show_ROI_status:
                # Draw default ROI
                self.draw_ROI(pixmap, self.roi_rect_list, image_width=width)
            # Tắt luồng detect OCR
            self.thread_OCR_detect = False

        # Nếu ko live camera và ko phải live chụp hình cuối
        # (tức là chỉ chụp bằng grab) thì cho phép record
        if not self.GUI.live_camera_status and not is_continuous:
            if self.GUI.record_status:
                # Crop ROI để lưu
                self.crop_ROI(self.roi_rect_list)
        # Nếu realtime
        if self.GUI.real_time_status:
            if not self.GUI.live_camera_status and not is_continuous:
                # Nếu realtime AI và chụp đơn ko live thì detect luôn
                self.OCR_detect()
                # Tắt luồng detect OCR
                self.thread_OCR_detect = False
                # print("AI")
            else:
                # Nếu realtime AI và live thì chạy luồng riêng để detect
                if self.thread_OCR_detect == False:
                    # Nếu luồng đang tắt thì mới bật
                    self.start_thread_OCR(True)

        # Hien thi ket quả OCR
        if self.GUI.real_time_status:
            if self.GUI.live_camera_status:
                current_OCR_text = self.continuous_OCR_text
            else:
                current_OCR_text = self.single_OCR_text
            roi_ORC_list = []
            OCR_text_list = []
            self.result = True
            ok_count = 0
            ng_count = 0

            # Pre-compile regex patterns trước vòng lặp để tối ưu performance
            base = self.GUI.current_product
            rev = self.GUI.current_product[::-1]

            # Tạo các biến thể đảo được chấp nhận
            rev_variants = {rev}
            sep = "-"
            if sep in base:
                parts = base.split(sep)
                if len(parts) == 2:
                    left, right = parts
                    rev_variants.add(right[::-1] + sep + left[::-1])
                    rev_variants.add(
                        right[::-1] + left[-1::-1][0] + sep + left[::-1][1:]
                    )
                    rev_variants.add(
                        right[::-1][:-1] + sep + right[::-1][-1] + left[::-1]
                    )

            # Compile pattern thuận 1 lần duy nhất
            pattern_forward = re.compile(
                rf"(?:(?<=^)|(?<=[-_])){re.escape(base)}(?:(?=$)|(?=[-_]))"
            )

            # Compile tất cả pattern đảo 1 lần duy nhất
            patterns_reverse = [
                re.compile(
                    rf"(?:(?<=^)|(?<=[-_])){re.escape(variant)}(?:(?=$)|(?=[-_]))"
                )
                for variant in rev_variants
            ]

            for idx, text in enumerate(current_OCR_text):
                # print(text)
                if text != "":
                    # Nếu có text thì vẽ box
                    roi_ORC_list.append(self.roi_rect_list[idx].copy())

                    matched = False
                    # Nếu thuận
                    if pattern_forward.search(text):
                        OCR_text_list.append(base)
                        matched = True
                        ok_count += 1
                    else:
                        # Nếu đảo
                        for pattern_rev in patterns_reverse:
                            if pattern_rev.search(text):
                                OCR_text_list.append(base)
                                matched = True
                                ok_count += 1
                                break

                    # Nếu sai
                    if not matched:
                        OCR_text_list.append("")
                        ng_count += 1

                        # Vẽ box màu đỏ cho phần tử cuối vừa thêm
                        if roi_ORC_list:
                            roi_ORC_list[-1][4] = 1
                        self.result = False

            self.draw_ROI(
                pixmap, roi_ORC_list, image_width=width, OCR_text_list=OCR_text_list
            )

            # Nếu dừng live thì reset pixmap
            # if not self.GUI.live_camera_status:
            #     self.pixmap_item.setPixmap(pixmap)

            # Gui so luong gang cau dung
            self.quantity = len(OCR_text_list)
            signal.send_quantity.emit(self.quantity, self.result, ok_count, ng_count)

        # Cập nhật thời gian xử lý, fps
        processing_time = global_vars.camera_time * 1000
        processing_time_ms = f"{processing_time:.1f} ms"
        if is_continuous:
            now = time.time()
            if self.fps_count == 0:
                self.fps_start_time = now  # Bắt đầu đếm từ frame đầu tiên
            self.fps_count += 1
            elapsed = now - self.fps_start_time
            # Cập nhật FPS mỗi giây
            if elapsed >= 1.0:
                fps = f"{self.fps_count / elapsed:.0f}"
                self.GUI.label_fps.setText(fps)
                self.GUI.label_cycle_time.setText(processing_time_ms)
                self.fps_count = 0
                self.fps_start_time = now
        else:
            self.fps_count = 0

        self._displaying = False

    @catch_errors
    def on_load_model(self):
        # self.model_OCR = self.OCR_DEEP_LEARNING_TOOL.Load_Model_OCR(self.GUI.model_path)
        response = self.api_client.load_model(self.GUI.model_path)
        if response.get("error"):
            raise Exception(f"Failed to load model: {response['error']}")

    @catch_errors
    def on_update_thresholds(self):
        self.api_client.input_config(
            acceptance_threshold_ocr=self.GUI.acceptance_threshold,
            duplication_threshold_ocr=self.GUI.mns_threshold,
            row_threshold=20,
        )

    @catch_errors
    def start_thread_OCR(self, status):
        if status:
            # Nếu đã có thread OCR đang chạy thì không tạo thêm
            if hasattr(self, "thread_OCR") and self.thread_OCR.is_alive():
                return

            self.thread_OCR_detect = True
            self.thread_OCR = threading.Thread(
                target=self.OCR_detect_continuous, daemon=True
            )
            self.thread_OCR.start()
        else:
            self.thread_OCR_detect = False

    def on_record_crop(self):
        # print("CR")
        self.crop_ROI(self.roi_rect_list)

    def on_save_result(self):
        # Lưu hình kết quả
        if self.new_pixmap is not None:
            if self.quantity != 0:
                self.save_pixmap_image(self.new_pixmap, self.result)

    def on_update_roi_rect_list(self):
        # Update default ROI
        self.roi_rect_list = [
            [
                self.GUI.ROIx1 - self.GUI.offset_x,
                self.GUI.ROIy1 - self.GUI.offset_y,
                300,
                440,
                0,
            ],  # x, y, w, h, color
            [
                self.GUI.ROIx2 - self.GUI.offset_x,
                self.GUI.ROIy2 - self.GUI.offset_y,
                300,
                440,
                0,
            ],
            [
                self.GUI.ROIx3 - self.GUI.offset_x,
                self.GUI.ROIy3 - self.GUI.offset_y,
                300,
                440,
                0,
            ],
            [
                self.GUI.ROIx4 - self.GUI.offset_x,
                self.GUI.ROIy4 - self.GUI.offset_y,
                300,
                440,
                0,
            ],
            [
                self.GUI.ROIx5 - self.GUI.offset_x,
                self.GUI.ROIy5 - self.GUI.offset_y,
                300,
                440,
                0,
            ],
        ]
        # print("ROI updated:", self.roi_rect_list)

    def on_move_ROI(self):
        self.on_update_roi_rect_list()
        if self.GUI.show_ROI_status and not self.GUI.live_camera_status:
            # Draw default ROI
            self.draw_ROI(self.pixmap, self.roi_rect_list, image_width=self.width)

    # Function=======================================================================
    @catch_errors
    def draw_ROI(self, pixmap, roi_list, image_width, OCR_text_list=None):

        self.new_pixmap = pixmap.copy()  # Sao chép để không ghi đè ảnh gốc
        painter = QPainter(self.new_pixmap)

        painter.setFont(QFont("Arial", 40))

        for idx, roi_rect in enumerate(roi_list):
            if isinstance(roi_rect, (list, tuple)):
                x, y, w, h, color = roi_rect
            # else:
            #     x, y, w, h= roi_rect.x(), roi_rect.y(), roi_rect.width(), roi_rect.height()
            if color == 0:
                pen = QPen(QColor(0, 255, 0), max(1, int(image_width / 350)))
            elif color == 1:
                pen = QPen(QColor(255, 0, 0), max(1, int(image_width / 350)))
            else:
                # Mặc định màu xanh nếu color không phải 0 hoặc 1
                pen = QPen(QColor(0, 255, 0), max(1, int(image_width / 350)))

            painter.setPen(pen)
            painter.drawRect(x, y, w, h)
            if OCR_text_list and idx < len(OCR_text_list):
                text = OCR_text_list[idx]
                # print(type(text), text)
                painter.drawText(x, y - 20, text)

        painter.end()
        self.pixmap_item.setPixmap(self.new_pixmap)

    @catch_errors
    def crop_ROI(self, roi_rect_list):
        if self.img_crop is not None and self.img_crop.size > 0:
            for idx, roi_rect in enumerate(roi_rect_list):
                if isinstance(roi_rect, (list, tuple)):
                    x, y, w, h, _ = roi_rect
                roi_crop = self.img_crop[y : y + h, x : x + w]
                # Xoay 90 độ theo chiều kim đồng hồ
                roi_crop_rotated = cv2.rotate(roi_crop, cv2.ROTATE_90_CLOCKWISE)

                now = datetime.now()
                current_time = (
                    now.strftime("%Y_%m_%d_%H_%M_%S")
                    + f"_{now.microsecond // 1000:03d}"
                )
                roi_crop_name = f"{current_time}_{idx}.bmp"
                os.makedirs(f"{self.drive}/Crop Image", exist_ok=True)
                save_path = os.path.join(f"{self.drive}/Crop Image", roi_crop_name)
                cv2.imwrite(save_path, roi_crop_rotated)

    @catch_errors
    def OCR_detect(self):
        # if not initialize_secure_dongle():
        # signal.show_error_message_main.emit("[OCR_detect] License key not found!")
        # signal.live_camera.emit(False)
        # signal.disconnect_camera.emit()
        # signal.disconnect_PLC.emit()
        # return
        # check_dongle_and_log()
        start_time = time.time()
        if self.roi_rect_list is None:
            return
        if not hasattr(self, "img_crop") or self.img_crop is None:
            return
        for roi_rect in self.roi_rect_list:
            if not isinstance(roi_rect, (list, tuple)):
                continue
            x, y, w, h, _ = roi_rect
            roi_crop = self.img_crop[y : y + h, x : x + w]
            # Xoay 90 độ theo chiều kim đồng hồ
            roi_crop_rotated = cv2.rotate(roi_crop, cv2.ROTATE_90_CLOCKWISE)
            if self.GUI.real_time_status:
                # Cho phép predict
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, 100]
                _, buffer = cv2.imencode(".jpg", roi_crop_rotated, encode_params)
                img_ocr_binary = buffer.tobytes()
                with self._inference_lock:
                    start_time = time.time()
                    result = self.api_client.ws_predict(img_ocr_binary)
                    processing_time = time.time() - start_time
                    print(f"OCR processing time: {processing_time:.3f} seconds")
                # _, Text2, _, error = result
                Text2 = result.get("text")
                error = result.get("error")
                if error == "exception: stack overflow":
                    # signal.show_error_message_main.emit(f"OCR Error: {error}")
                    self.thread_OCR_detect = False
                    QTimer.singleShot(
                        1000, lambda: setattr(self, "thread_OCR_detect", True)
                    )
                    # Ghi log lỗi stack overflow
                    try:
                        log_path = os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            "stack_overflow_log.txt",
                        )
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        log_line = f"[{timestamp}] OCR Error: {error}\n"
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(log_line)
                    except:
                        pass
                    return

                # Text2 = result
                if Text2 == None:
                    Text2 = ""
                if len(self.single_OCR_text) < 5:
                    self.single_OCR_text.append(Text2)

    def OCR_detect_continuous(self):
        while self.thread_OCR_detect:
            self.OCR_detect()
            if self.GUI.live_camera_status:
                # self.update_OCR_text.emit()
                # Cập nhật text mới
                self.continuous_OCR_text = self.single_OCR_text.copy()
            else:
                # self.continuous_OCR_text.clear()
                self.continuous_OCR_text = [""] * 5
            # Xóa text cũ
            self.single_OCR_text.clear()
            # print(self.continuous_OCR_text)
            # print(self.GUI.live_camera_status)

            time.sleep(0.005)

    def save_pixmap_image(self, pixmap, result):
        qimg_rgba = pixmap.toImage().convertToFormat(QImage.Format_ARGB32)
        ptr = qimg_rgba.bits()
        ptr.setsize(qimg_rgba.byteCount())
        image_arr = np.array(ptr).reshape(
            (qimg_rgba.height(), qimg_rgba.width(), 4)
        )  # lay ra anh numpy
        now = datetime.now()
        current_time = (
            now.strftime("%Y_%m_%d_%H_%M_%S") + f"_{now.microsecond // 1000:03d}"
        )
        img_name = f"{result}_{self.GUI.current_product}_{current_time}.bmp"
        os.makedirs(
            f"{self.drive}/DRB Metalcore Text Result/{now.strftime('%d_%m_%Y')}/{result}",
            exist_ok=True,
        )
        # save_path_1 = os.path.join(f"{self.drive}/DRB Metalcore Text Result", img_name)
        save_path_2 = os.path.join(
            f"{self.drive}/DRB Metalcore Text Result/{now.strftime('%d_%m_%Y')}/{result}",
            img_name,
        )
        # cv2.imwrite(save_path_1, image_arr)
        cv2.imwrite(save_path_2, image_arr)

    def current_drive(self):
        # Thu muc chua file python hien tai
        if getattr(sys, "frozen", False):
            # Neu chay tu file exe
            base_dir = os.path.dirname(sys.executable)
        else:
            # Neu chay tu file python
            base_dir = os.path.dirname(os.path.abspath(__file__))
        # Lấy ổ đĩa (C:\, D:\, E:\ ...)
        self.drive = os.path.splitdrive(base_dir)[0]
