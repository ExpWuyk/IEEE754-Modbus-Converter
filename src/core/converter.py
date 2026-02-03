"""
Modbus 数据转换器核心类
"""
import struct
from typing import Tuple, Optional, Any, List
from . import DataType, ByteOrder, ParseResult, ConvertResult


class ModbusConverter:
    """Modbus RTU 数据转换器"""

    # 数据类型对应的字节长度
    DATA_TYPE_LENGTHS = {
        DataType.FLOAT32: 4,
        DataType.FLOAT64: 8,
        DataType.INT16: 2,
        DataType.UINT16: 2,
        DataType.INT32: 4,
        DataType.UINT32: 4,
    }

    # 最小报文长度（地址1+功能码1+长度1+数据N+CRC2）
    MIN_PACKET_LENGTHS = {
        DataType.FLOAT32: 18,
        DataType.FLOAT64: 26,
        DataType.INT16: 14,
        DataType.UINT16: 14,
        DataType.INT32: 18,
        DataType.UINT32: 18,
    }

    @staticmethod
    def clean_hex_string(hex_str: str) -> str:
        """清洗十六进制字符串，只保留有效字符"""
        return ''.join(c for c in hex_str if c in '0123456789ABCDEFabcdef').upper()

    @staticmethod
    def calculate_crc16(data: bytes) -> int:
        """计算 Modbus CRC16 校验码"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    @classmethod
    def calculate_crc16_hex(cls, modbus_hex: str) -> str:
        """计算CRC16并返回十六进制字符串（小端序）"""
        try:
            clean_hex = cls.clean_hex_string(modbus_hex)
            if len(clean_hex) < 4:
                return "错误"
            data = bytes.fromhex(clean_hex[:-4])
            crc = cls.calculate_crc16(data)
            # Modbus CRC 小端序：低字节在前
            return f"{crc & 0xFF:02X}{(crc >> 8) & 0xFF:02X}"
        except Exception as e:
            return f"计算失败: {str(e)}"

    @classmethod
    def parse_packet(cls, hex_str: str, data_type: DataType) -> Tuple[ParseResult, str]:
        """
        解析 Modbus RTU 报文
        返回: (解析结果, 错误信息)
        """
        error_msg = ""
        result = ParseResult()

        try:
            clean_hex = cls.clean_hex_string(hex_str)
            if not clean_hex:
                return result, "输入为空或无有效十六进制字符"

            # 检查最小长度
            min_len = cls.MIN_PACKET_LENGTHS.get(data_type, 18)
            if len(clean_hex) < min_len:
                return result, f"报文长度不足！{data_type.value}需至少{min_len}字符，当前{len(clean_hex)}字符"

            # 解析各字段
            result.slave_addr = clean_hex[0:2]
            result.func_code = clean_hex[2:4]
            result.data_len = clean_hex[4:6]
            result.input_crc = clean_hex[-4:]
            result.calc_crc = cls.calculate_crc16_hex(clean_hex)

            # 校验功能码
            if result.func_code not in ["03", "04"]:
                return result, f"仅支持功能码03/04！当前功能码为{result.func_code}"

            # 提取数据部分
            data_len_int = int(result.data_len, 16)
            expected_len = cls.DATA_TYPE_LENGTHS.get(data_type, 4)
            if data_len_int != expected_len:
                return result, f"{data_type.value}需{expected_len}字节数据！当前{data_len_int}字节"

            result.data_hex = clean_hex[6:6 + data_len_int * 2]
            result.crc_valid = (result.calc_crc == result.input_crc)

            return result, ""

        except Exception as e:
            return result, str(e)

    @classmethod
    def reorder_bytes_float32(cls, data_hex: str, byte_order: ByteOrder) -> str:
        """根据字节序规则重排32位数据"""
        if len(data_hex) != 8:
            return data_hex
        A, B, C, D = data_hex[0:2], data_hex[2:4], data_hex[4:6], data_hex[6:8]
        order_mapping = {
            ByteOrder.BADC: B + A + D + C,
            ByteOrder.CDAB: C + D + A + B,
            ByteOrder.ABCD: A + B + C + D,
            ByteOrder.DCBA: D + C + B + A,
        }
        return order_mapping.get(byte_order, A + B + C + D)

    @classmethod
    def reorder_bytes_float64(cls, data_hex: str, byte_order: ByteOrder) -> str:
        """根据字节序规则重排64位数据"""
        if len(data_hex) != 16:
            return data_hex
        bytes_list = [data_hex[i:i+2] for i in range(0, 16, 2)]
        A, B, C, D, E, F, G, H = bytes_list
        # 扩展的字节序规则
        order_mapping = {
            ByteOrder.BADC: B + A + D + C + F + E + H + G,
            ByteOrder.CDAB: E + F + G + H + A + B + C + D,
            ByteOrder.ABCD: A + B + C + D + E + F + G + H,
            ByteOrder.DCBA: H + G + F + E + D + C + B + A,
        }
        return order_mapping.get(byte_order, data_hex)

    @classmethod
    def convert(cls, hex_str: str, byte_order: ByteOrder, data_type: DataType) -> ConvertResult:
        """
        执行完整的 Modbus 数据转换
        """
        # 解析报文
        parse_result, error_msg = cls.parse_packet(hex_str, data_type)
        if error_msg:
            return ConvertResult(success=False, value=None, parse_result=parse_result, error_msg=error_msg)

        try:
            data_hex = parse_result.data_hex
            value = None

            # 16位整数
            if data_type == DataType.INT16:
                data_bytes = bytes.fromhex(data_hex)
                value = int.from_bytes(data_bytes, byteorder='big', signed=True)

            elif data_type == DataType.UINT16:
                data_bytes = bytes.fromhex(data_hex)
                value = int.from_bytes(data_bytes, byteorder='big', signed=False)

            # 32位整数
            elif data_type == DataType.INT32:
                reordered = cls.reorder_bytes_float32(data_hex, byte_order)
                data_bytes = bytes.fromhex(reordered)
                value = struct.unpack('!i', data_bytes)[0]

            elif data_type == DataType.UINT32:
                reordered = cls.reorder_bytes_float32(data_hex, byte_order)
                data_bytes = bytes.fromhex(reordered)
                value = struct.unpack('!I', data_bytes)[0]

            # 32位浮点数
            elif data_type == DataType.FLOAT32:
                reordered = cls.reorder_bytes_float32(data_hex, byte_order)
                data_bytes = bytes.fromhex(reordered)
                value = struct.unpack('!f', data_bytes)[0]
                value = round(value, 4)

            # 64位浮点数
            elif data_type == DataType.FLOAT64:
                reordered = cls.reorder_bytes_float64(data_hex, byte_order)
                data_bytes = bytes.fromhex(reordered)
                value = struct.unpack('!d', data_bytes)[0]
                value = round(value, 6)

            return ConvertResult(success=True, value=value, parse_result=parse_result)

        except Exception as e:
            return ConvertResult(success=False, value=None, parse_result=parse_result, error_msg=str(e))

    @classmethod
    def batch_convert(cls, hex_list: List[str], byte_order: ByteOrder,
                      data_type: DataType) -> List[ConvertResult]:
        """批量转换"""
        return [cls.convert(hex_str, byte_order, data_type) for hex_str in hex_list]
