import threading
import time
from abc import ABC, abstractmethod

from pymodbus.client import ModbusTcpClient, ModbusSerialClient
import pymcprotocol
from PyQt5.QtCore import QTimer, QThread

from Global import signal, catch_errors


# =============================================================================
# Abstract Base Class for PLC Protocol
# =============================================================================
class PLCProtocol(ABC):
    """Interface chung cho tất cả giao thức PLC"""

    @abstractmethod
    def connect(self, **kwargs) -> bool:
        """Kết nối với PLC. Trả về True nếu thành công."""
        pass

    @abstractmethod
    def disconnect(self):
        """Ngắt kết nối PLC."""
        pass

    @abstractmethod
    def read_coils(self, address: int, count: int):
        """Đọc coils từ PLC."""
        pass

    @abstractmethod
    def write_coil(self, address: int, value: bool):
        """Ghi coil vào PLC."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Kiểm tra trạng thái kết nối."""
        pass


# =============================================================================
# Modbus TCP Protocol Implementation
# =============================================================================
class ModbusTCPProtocol(PLCProtocol):
    """Giao thức Modbus TCP"""

    # Offset để chuyển địa chỉ logic (M0, M1...) sang địa chỉ Modbus
    # M0 = 8192, M1 = 8193, ...
    COIL_OFFSET = 8192

    def __init__(self):
        self.client = None
        self._connected = False

    def connect(self, ip="192.168.0.250", port=502, **kwargs) -> bool:
        self.client = ModbusTcpClient(ip, port=port)
        self._connected = self.client.connect()
        return self._connected

    def disconnect(self):
        if self.client:
            self.client.close()
            self._connected = False

    def read_coils(self, address: int, count: int):
        if self.client:
            return self.client.read_coils(
                address=address + self.COIL_OFFSET, count=count
            )
        return None

    def write_coil(self, address: int, value: bool):
        if self.client:
            return self.client.write_coil(
                address=address + self.COIL_OFFSET, value=value
            )
        return None

    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# Modbus RTU Protocol Implementation
# =============================================================================
class ModbusRTUProtocol(PLCProtocol):
    """Giao thức Modbus RTU (Serial)"""

    # Offset để chuyển địa chỉ logic (M0, M1...) sang địa chỉ Modbus
    COIL_OFFSET = 8192

    def __init__(self):
        self.client = None
        self._connected = False
        self.slave_id = 1

    def connect(
        self,
        port="COM1",
        baudrate=9600,
        parity="N",
        stopbits=1,
        bytesize=8,
        slave_id=1,
        **kwargs,
    ) -> bool:
        self.slave_id = slave_id
        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
        )
        self._connected = self.client.connect()
        return self._connected

    def disconnect(self):
        if self.client:
            self.client.close()
            self._connected = False

    def read_coils(self, address: int, count: int):
        if self.client:
            return self.client.read_coils(
                address=address + self.COIL_OFFSET, count=count, slave=self.slave_id
            )
        return None

    def write_coil(self, address: int, value: bool):
        if self.client:
            return self.client.write_coil(
                address=address + self.COIL_OFFSET, value=value, slave=self.slave_id
            )
        return None

    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# SLMP Protocol Implementation (Mitsubishi MC Protocol)
# =============================================================================
class SLMPReadResult:
    """Wrapper để tương thích với interface Modbus read result"""

    def __init__(self, bits: list = None, error: bool = False):
        self.bits = bits or []
        self._error = error

    def isError(self) -> bool:
        return self._error


class SLMPWriteResult:
    """Wrapper để tương thích với interface Modbus write result"""

    def __init__(self, error: bool = False):
        self._error = error

    def isError(self) -> bool:
        return self._error


class SLMPProtocol(PLCProtocol):
    """
    Giao thức SLMP/MC Protocol cho PLC Mitsubishi.
    Sử dụng thư viện pymcprotocol.
    Hỗ trợ PLC series: Q, L, QnA, iQ-L, iQ-R
    """

    def __init__(self):
        self.client = None
        self._connected = False

    def connect(
        self, ip="192.168.0.250", port=5000, plc_type="Q", comm_type="binary", **kwargs
    ) -> bool:
        """
        Kết nối với PLC Mitsubishi qua SLMP.

        Args:
            ip: Địa chỉ IP của PLC
            port: Cổng MC Protocol (thường là 5000 hoặc 5001)
            plc_type: Loại PLC ("Q", "L", "QnA", "iQ-L", "iQ-R")
            comm_type: Kiểu giao tiếp ("binary" hoặc "ascii")
        """
        self.client = pymcprotocol.Type3E(plctype=plc_type)

        if comm_type == "ascii":
            self.client.setaccessopt(commtype="ascii")

        try:
            self.client.connect(ip, int(port))
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False

    def disconnect(self):
        if self.client and self._connected:
            try:
                self.client.close()
            except Exception:
                pass
            self._connected = False

    def read_coils(self, address: int, count: int):
        """Đọc bit M từ PLC Mitsubishi."""
        if not self.client or not self._connected:
            return SLMPReadResult(error=True)

        try:
            values = self.client.batchread_bitunits(
                headdevice=f"M{address}", readsize=count
            )
            bits = [bool(v) for v in values]
            return SLMPReadResult(bits=bits, error=False)
        except Exception:
            return SLMPReadResult(error=True)

    def write_coil(self, address: int, value: bool):
        """Ghi bit M vào PLC Mitsubishi."""
        if not self.client or not self._connected:
            return SLMPWriteResult(error=True)

        try:
            self.client.batchwrite_bitunits(
                headdevice=f"M{address}", values=[1 if value else 0]
            )
            return SLMPWriteResult(error=False)
        except Exception:
            return SLMPWriteResult(error=True)

    def is_connected(self) -> bool:
        return self._connected


# =============================================================================
# PLC Controller (Main Class)
# =============================================================================
class PLCController:
    """
    Controller quản lý giao tiếp PLC.
    Hỗ trợ chuyển đổi giữa các protocol (TCP/RTU/SLMP) trong lúc chạy.
    """

    def __init__(self):
        super().__init__()
        self.set_value()
        self.set_event()
        # self.set_state()

    # Setup ==================================================================
    def set_event(self):
        signal.connect_PLC.connect(self.on_PLC_connect)
        signal.disconnect_PLC.connect(self.on_PLC_disconnect)
        signal.auto_read_PLC.connect(self.start_thread_read_PLC)
        signal.light_PLC.connect(self.control_light_PLC)
        signal.send_error_PLC.connect(self.send_error)

    def set_value(self):
        self.protocol = None
        self.thread_read_PLC = False
        self.PLC_status = False

    # def set_state(self):
    #     # Kết nối mặc định với TCP
    #     self.on_PLC_connect({"protocol_type": "tcp"})
    #     self.control_light_PLC(True)

    # Execute ================================================================
    @catch_errors
    def on_PLC_connect(self, params):
        """
        Kết nối PLC với protocol được chỉ định.

        params: dict chứa các tham số:
            - protocol_type: "TCP", "RTU", hoặc "SLMP"
            - tries: số lần thử kết nối (mặc định 1)

            Cho Modbus TCP:
                - ip: địa chỉ IP (mặc định "192.168.0.250")
                - port: cổng (mặc định 502)

            Cho Modbus RTU:
                - port: cổng COM (vd: "COM1", "COM3")
                - baudrate: tốc độ baud (mặc định 9600)
                - parity: "N", "E", "O" (mặc định "N")
                - stopbits: 1 hoặc 2 (mặc định 1)
                - bytesize: 7 hoặc 8 (mặc định 8)
                - slave_id: ID của slave (mặc định 1)

            Cho SLMP (Mitsubishi):
                - ip: địa chỉ IP của PLC
                - port: cổng MC Protocol (mặc định 5000)
                - plc_type: loại PLC ("Q", "L", "QnA", "iQ-L", "iQ-R")
                - comm_type: "binary" hoặc "ascii" (mặc định "binary")
        """
        # Xử lý backward compatibility: nếu params là tuple (ip, tries) cũ
        if isinstance(params, tuple):
            params = {"protocol_type": "TCP", "ip": params[0], "tries": params[1]}

        # Nếu params là string (chỉ có IP)
        if isinstance(params, str):
            params = {"protocol_type": "TCP", "ip": params, "tries": 1}

        protocol_type = params.get("protocol_type", "TCP")
        tries = params.get("tries", 1)

        # Ngắt kết nối protocol cũ nếu có
        if self.protocol and self.PLC_status:
            self.on_PLC_disconnect()

        # Tạo protocol mới
        if protocol_type == "TCP":
            self.protocol = ModbusTCPProtocol()
        elif protocol_type == "RTU":
            self.protocol = ModbusRTUProtocol()
        elif protocol_type == "SLMP":
            self.protocol = SLMPProtocol()
        else:
            return

        # Thử kết nối
        for _ in range(tries):
            if self.protocol.connect(**params):
                self.PLC_status = True
                signal.PLC_connected.emit()
                return
            else:
                QThread.msleep(5)

    def on_PLC_disconnect(self):
        if self.PLC_status:
            self.start_thread_read_PLC(False)
            signal.PLC_disconnected.emit()
            if self.protocol:
                self.protocol.disconnect()
            self.PLC_status = False

    @catch_errors
    def start_thread_read_PLC(self, status):
        if self.protocol is not None:
            if status:
                # Nếu đã có thread đang chạy thì không tạo thêm
                if hasattr(self, "thread_PLC") and self.thread_PLC.is_alive():
                    return

                self.thread_read_PLC = True
                self.thread_PLC = threading.Thread(
                    target=self.read_M_continuos, daemon=True
                )
                self.thread_PLC.start()
            else:
                self.thread_read_PLC = False

    @catch_errors
    def control_light_PLC(self, value):
        if self.protocol is not None and self.PLC_status:
            write_on = self.protocol.write_coil(address=100, value=value)  # M100
            if write_on is None or write_on.isError():
                return False

    @catch_errors
    def send_error(self):
        if self.protocol is not None and self.PLC_status:
            write_on = self.protocol.write_coil(address=101, value=True)  # M101
            if write_on is None or write_on.isError():
                return False
            # Dùng QTimer single-shot (ms)
            QTimer.singleShot(
                500, lambda: self.protocol.write_coil(address=101, value=False)
            )
            return True

    # Function ===============================================================
    @catch_errors
    def read_M_continuos(self):
        previous_value_0 = False
        previous_value_1 = False
        previous_value_2 = False
        # Debounce: thời điểm emit gần nhất (giây)
        last_emit_time_0 = 0
        last_emit_time_1 = 0
        last_emit_time_2 = 0
        DEBOUNCE_TIME = 1  # 1s - bỏ qua tín hiệu lặp trong khoảng này

        if self.protocol is not None:
            while self.thread_read_PLC:
                read_value = self.protocol.read_coils(address=0, count=3)  # M0, M1, M2
                if read_value is not None and not read_value.isError():
                    current_time = time.time()

                    # Tín hiệu chốt (M0)
                    current_value_0 = read_value.bits[0]
                    if current_value_0 and not previous_value_0:
                        # Chỉ emit nếu đã qua thời gian debounce
                        if current_time - last_emit_time_0 > DEBOUNCE_TIME:
                            signal.PLC_grab_image.emit()
                            last_emit_time_0 = current_time
                    previous_value_0 = current_value_0

                    # Tín hiệu dừng máy (M1)
                    current_value_1 = read_value.bits[1]
                    if current_value_1 and not previous_value_1:
                        if current_time - last_emit_time_1 > DEBOUNCE_TIME:
                            signal.PLC_stop.emit()
                            last_emit_time_1 = current_time
                    previous_value_1 = current_value_1

                    # Tín hiệu chạy máy (M2)
                    current_value_2 = read_value.bits[2]
                    if current_value_2 and not previous_value_2:
                        if current_time - last_emit_time_2 > DEBOUNCE_TIME:
                            signal.light_PLC.emit(True)
                            signal.PLC_start.emit()
                            last_emit_time_2 = current_time
                    previous_value_2 = current_value_2

                    time.sleep(0.002)


# Backward compatibility alias
PLCModbus = PLCController


if __name__ == "__main__":
    PLCController()
