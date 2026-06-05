import threading
import time

from pypylon import pylon

from Global import signal, global_vars, catch_errors


class CameraController:
    def __init__(self):
        super().__init__()
        # self.set_variable()
        self.cam: pylon.InstantCamera = None
        self.converter = pylon.ImageFormatConverter()
        self.converter.OutputPixelFormat = pylon.PixelType_RGB8packed
        self.converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self.set_event()
        self.set_value()

    def set_event(self):
        signal.connect_camera.connect(self.connect_camera)
        signal.disconnect_camera.connect(self.disconnect_camera)
        signal.grab_image.connect(self.grab_image)
        signal.live_camera.connect(self.start_thread_live_camera)
        signal.send_exposure.connect(self.change_exposure)
        signal.update_img_size.connect(self.set_image_size)

    def set_value(self):
        self.thread_live_camera = False
        self._grab_lock = threading.Lock()  # Lock đồng bộ các thao tác grab

    # Excecute=======================================================================
    @catch_errors
    def connect_camera(self):
        tlFactory = pylon.TlFactory.GetInstance()
        devices = tlFactory.EnumerateDevices()
        if len(devices) == 0:
            signal.show_error_message_main.emit("No camera found!")
            return
        self.cam = pylon.InstantCamera(tlFactory.CreateDevice(devices[0]))
        self.cam.Open()
        # self.cam.PixelFormat.SetValue("RGB8")  # Camera không hỗ trợ RGB8
        self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # self.cam.ExposureTimeAbs.SetValue(3000)
        node_map = self.cam.GetNodeMap()
        exposure_node = node_map.GetNode("ExposureTimeAbs")
        if exposure_node is not None:
            self.cam.ExposureTimeAbs.SetValue(3000)
        else:
            self.cam.ExposureTime.SetValue(3000)
        grab_result = self.cam.RetrieveResult(
            4000, pylon.TimeoutHandling_ThrowException
        )
        if grab_result.GrabSucceeded():
            grab_result.Release()  # Phải release buffer sau khi sử dụng
            # print("connect")
            signal.camera_connected.emit()
        else:
            grab_result.Release()
            signal.show_error_message_main.emit("Cannot connect camera!")

    @catch_errors
    def disconnect_camera(self):
        if self.cam is None or not self.cam.IsOpen():
            return
        # Dừng live thread trước khi đóng camera
        self.thread_live_camera = False
        if hasattr(self, "thread_camera") and self.thread_camera.is_alive():
            self.thread_camera.join(timeout=2)
        self.cam.StopGrabbing()
        self.cam.Close()
        # print("disconnect")
        signal.camera_disconnected.emit()

    @catch_errors
    def change_exposure(self, exposure_time):
        # self.cam.ExposureTimeAbs.SetValue(exposure_time)
        if self.cam is None or not self.cam.IsOpen():
            return
        node_map = self.cam.GetNodeMap()
        exposure_node = node_map.GetNode("ExposureTimeAbs")
        if exposure_node is not None:
            self.cam.ExposureTimeAbs.SetValue(exposure_time)
        else:
            self.cam.ExposureTime.SetValue(exposure_time)

    @catch_errors
    def set_image_size(self, x, y, w, h):
        if self.cam is None or not self.cam.IsOpen():
            return
        with self._grab_lock:
            self.cam.StopGrabbing()
            self.cam.OffsetX.SetValue(0)
            self.cam.OffsetY.SetValue(0)
            self.cam.Width.SetValue(w)
            self.cam.Height.SetValue(h)
            self.cam.OffsetX.SetValue(x)
            self.cam.OffsetY.SetValue(y)
            self.cam.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        if not self.thread_live_camera:
            self.grab_image()

    @catch_errors
    def grab_image(self):
        if self.cam is None or not self.cam.IsOpen():
            return
        img = None
        start_time = time.time()
        # Dùng lock để đồng bộ với grab_continuous
        with self._grab_lock:
            grab_result = self.cam.RetrieveResult(
                5000, pylon.TimeoutHandling_ThrowException
            )
            if grab_result.GrabSucceeded():
                img = self.converter.Convert(grab_result).GetArray()
                # img = grab_result.Array.copy()
                grab_result.Release()
                # print(type(img))
            else:
                grab_result.Release()

        end_time = time.time()
        processing_time = end_time - start_time
        # print("thoi gian chụp hinh", processing_time)
        global_vars.camera_frame = img
        global_vars.camera_time = processing_time
        signal.new_frame_ready.emit(False)  # False: không continuous

    @catch_errors
    def start_thread_live_camera(self, live_cam_status):
        # Nếu đã có thread đang chạy thì không tạo thêm
        if live_cam_status:
            if hasattr(self, "thread_camera") and self.thread_camera.is_alive():
                return

            self.thread_live_camera = True
            self.thread_camera = threading.Thread(
                target=self.grab_continuous, daemon=True
            )
            self.thread_camera.start()
        else:
            self.thread_live_camera = False

    # Function=======================================================================
    @catch_errors
    def grab_continuous(self):
        while self.thread_live_camera:
            # Dùng lock để đồng bộ với grab_image và set_image_size
            img = None
            start_time = None
            with self._grab_lock:
                if not self.thread_live_camera:
                    break
                if (
                    self.cam is None
                    or not self.cam.IsOpen()
                    or not self.cam.IsGrabbing()
                ):
                    break
                start_time = time.time()
                grab_result = self.cam.RetrieveResult(
                    5000, pylon.TimeoutHandling_ThrowException
                )
                if grab_result.GrabSucceeded():
                    img = self.converter.Convert(grab_result).GetArray()
                    # img = grab_result.Array.copy()
                    grab_result.Release()
                else:
                    grab_result.Release()
                end_time = time.time()
                processing_time = end_time - start_time
                # print("thoi gian camera tra hinh", processing_time)
            # Lưu frame mới nhất và emit signal nhẹ (không block)
            if img is not None and self.thread_live_camera:
                global_vars.camera_frame = img
                global_vars.camera_time = processing_time
                signal.new_frame_ready.emit(True)  # True: continuous
            time.sleep(0.001)


if __name__ == "__main__":
    CameraController()
