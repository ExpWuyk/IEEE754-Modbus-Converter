"""
串口通信模块 - Modbus RTU 串口通信
"""
import threading
import time
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


class Parity(Enum):
    NONE = 'N'
    EVEN = 'E'
    ODD = 'O'


class StopBits(Enum):
    ONE = 1
    TWO = 2


@dataclass
class SerialConfig:
    """串口配置"""
    port: str = ""
    baudrate: int = 9600
    bytesize: int = 8
    parity: str = 'N'
    stopbits: int = 1
    timeout: float = 1.0


class SerialCommunicator:
    """串口通信类"""

    def __init__(self):
        self._serial: Optional['serial.Serial'] = None
        self._is_connected = False
        self._read_thread: Optional[threading.Thread] = None
        self._stop_flag = False
        self._on_data_received: Optional[Callable[[bytes], None]] = None
        self._on_error: Optional[Callable[[str], None]] = None

    @staticmethod
    def is_available() -> bool:
        """检查串口库是否可用"""
        return SERIAL_AVAILABLE

    @staticmethod
    def list_ports() -> List[str]:
        """列出可用串口"""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    @staticmethod
    def get_port_info() -> List[dict]:
        """获取串口详细信息"""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer
            }
            for port in ports
        ]

    def connect(self, config: SerialConfig) -> tuple[bool, str]:
        """连接串口"""
        if not SERIAL_AVAILABLE:
            return False, "串口库未安装，请运行: pip install pyserial"

        try:
            self._serial = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=config.timeout
            )
            self._is_connected = True
            return True, "连接成功"
        except serial.SerialException as e:
            return False, f"连接失败: {str(e)}"
        except Exception as e:
            return False, f"未知错误: {str(e)}"

    def disconnect(self) -> None:
        """断开连接"""
        self._stop_flag = True
        if self._read_thread and self._read_thread.is_alive():
            self._read_thread.join(timeout=2)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._is_connected = False

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self._is_connected and self._serial and self._serial.is_open

    def send(self, data: bytes) -> tuple[bool, str]:
        """发送数据"""
        if not self.is_connected():
            return False, "串口未连接"
        try:
            self._serial.write(data)
            return True, ""
        except Exception as e:
            return False, str(e)

    def send_hex(self, hex_str: str) -> tuple[bool, str]:
        """发送十六进制字符串"""
        try:
            clean_hex = ''.join(c for c in hex_str if c in '0123456789ABCDEFabcdef')
            data = bytes.fromhex(clean_hex)
            return self.send(data)
        except ValueError as e:
            return False, f"无效的十六进制: {str(e)}"

    def read(self, size: int = 1024) -> bytes:
        """读取数据"""
        if not self.is_connected():
            return b''
        try:
            return self._serial.read(size)
        except Exception:
            return b''

    def read_until_timeout(self, timeout: float = 1.0) -> bytes:
        """读取数据直到超时"""
        if not self.is_connected():
            return b''
        data = b''
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._serial.in_waiting > 0:
                data += self._serial.read(self._serial.in_waiting)
                start_time = time.time()  # 重置超时
            time.sleep(0.01)
        return data

    def set_callbacks(self, on_data: Callable[[bytes], None] = None,
                      on_error: Callable[[str], None] = None) -> None:
        """设置回调函数"""
        self._on_data_received = on_data
        self._on_error = on_error

    def start_listening(self) -> None:
        """开始监听数据"""
        if not self.is_connected():
            return
        self._stop_flag = False
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

    def stop_listening(self) -> None:
        """停止监听"""
        self._stop_flag = True

    def _read_loop(self) -> None:
        """读取循环"""
        while not self._stop_flag and self.is_connected():
            try:
                if self._serial.in_waiting > 0:
                    data = self._serial.read(self._serial.in_waiting)
                    if data and self._on_data_received:
                        self._on_data_received(data)
            except Exception as e:
                if self._on_error:
                    self._on_error(str(e))
            time.sleep(0.01)
