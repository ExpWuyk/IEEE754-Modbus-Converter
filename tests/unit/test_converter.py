"""
单元测试 - Modbus 转换器核心功能测试
"""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import DataType, ByteOrder
from src.core.converter import ModbusConverter


class TestModbusConverter(unittest.TestCase):
    """Modbus 转换器测试类"""

    def test_clean_hex_string(self):
        """测试十六进制字符串清洗"""
        self.assertEqual(ModbusConverter.clean_hex_string("02 03 04"), "020304")
        self.assertEqual(ModbusConverter.clean_hex_string("02-03-04"), "020304")
        self.assertEqual(ModbusConverter.clean_hex_string("02\t03\n04"), "020304")
        self.assertEqual(ModbusConverter.clean_hex_string("abcdef"), "ABCDEF")
        self.assertEqual(ModbusConverter.clean_hex_string("xyz123"), "123")

    def test_calculate_crc16(self):
        """测试 CRC16 计算"""
        # 测试数据: 02 03 04 05 1F 42 C9
        data = bytes.fromhex("020304051F42C9")
        crc = ModbusConverter.calculate_crc16(data)
        # CRC 应该是 08CF (小端序)
        self.assertEqual(crc, 0xCF08)

    def test_calculate_crc16_hex(self):
        """测试 CRC16 十六进制输出"""
        hex_str = "020304051F42C908CF"
        crc_hex = ModbusConverter.calculate_crc16_hex(hex_str)
        self.assertEqual(crc_hex, "08CF")

    def test_parse_packet_float32(self):
        """测试 float32 报文解析"""
        hex_str = "020304051F42C908CF"
        result, error = ModbusConverter.parse_packet(hex_str, DataType.FLOAT32)

        self.assertEqual(error, "")
        self.assertEqual(result.slave_addr, "02")
        self.assertEqual(result.func_code, "03")
        self.assertEqual(result.data_len, "04")
        self.assertEqual(result.data_hex, "051F42C9")
        self.assertEqual(result.input_crc, "08CF")
        self.assertTrue(result.crc_valid)

    def test_parse_packet_invalid_func_code(self):
        """测试无效功能码"""
        hex_str = "020104051F42C908CF"  # 功能码 01
        result, error = ModbusConverter.parse_packet(hex_str, DataType.FLOAT32)
        self.assertIn("功能码", error)

    def test_parse_packet_length_error(self):
        """测试长度不足"""
        hex_str = "020304"  # 太短
        result, error = ModbusConverter.parse_packet(hex_str, DataType.FLOAT32)
        self.assertIn("长度不足", error)

    def test_convert_float32(self):
        """测试 float32 转换"""
        hex_str = "020304051F42C908CF"
        result = ModbusConverter.convert(hex_str, ByteOrder.CDAB, DataType.FLOAT32)

        self.assertTrue(result.success)
        self.assertIsNotNone(result.value)
        # 验证转换结果（根据字节序规则2: CDAB）
        # 数据: 05 1F 42 C9 -> 重排为 42 C9 05 1F -> IEEE 754 float
        self.assertAlmostEqual(result.value, 100.51, places=2)

    def test_convert_int16(self):
        """测试 int16 转换"""
        # 构造一个 int16 报文: 地址02 功能码03 长度02 数据0064 CRC
        hex_str = "0203020064B9C4"
        result = ModbusConverter.convert(hex_str, ByteOrder.CDAB, DataType.INT16)

        self.assertTrue(result.success)
        self.assertEqual(result.value, 100)  # 0x0064 = 100

    def test_convert_uint16(self):
        """测试 uint16 转换"""
        hex_str = "020302FFFF79C4"  # 0xFFFF = 65535
        result = ModbusConverter.convert(hex_str, ByteOrder.CDAB, DataType.UINT16)

        self.assertTrue(result.success)
        self.assertEqual(result.value, 65535)

    def test_reorder_bytes_float32(self):
        """测试 32 位字节重排"""
        data_hex = "AABBCCDD"

        # 规则1: BADC
        self.assertEqual(ModbusConverter.reorder_bytes_float32(data_hex, ByteOrder.BADC), "BBAADDCC")
        # 规则2: CDAB
        self.assertEqual(ModbusConverter.reorder_bytes_float32(data_hex, ByteOrder.CDAB), "CCDDAABB")
        # 规则3: ABCD
        self.assertEqual(ModbusConverter.reorder_bytes_float32(data_hex, ByteOrder.ABCD), "AABBCCDD")
        # 规则4: DCBA
        self.assertEqual(ModbusConverter.reorder_bytes_float32(data_hex, ByteOrder.DCBA), "DDCCBBAA")

    def test_batch_convert(self):
        """测试批量转换"""
        hex_list = [
            "020304051F42C908CF",
            "020304051F42C908CF",
        ]
        results = ModbusConverter.batch_convert(hex_list, ByteOrder.CDAB, DataType.FLOAT32)

        self.assertEqual(len(results), 2)
        for result in results:
            self.assertTrue(result.success)


class TestCRCValidation(unittest.TestCase):
    """CRC 校验测试"""

    def test_valid_crc(self):
        """测试有效 CRC"""
        hex_str = "020304051F42C908CF"
        result = ModbusConverter.convert(hex_str, ByteOrder.CDAB, DataType.FLOAT32)
        self.assertTrue(result.parse_result.crc_valid)

    def test_invalid_crc(self):
        """测试无效 CRC"""
        hex_str = "020304051F42C90000"  # 错误的 CRC
        result = ModbusConverter.convert(hex_str, ByteOrder.CDAB, DataType.FLOAT32)
        self.assertFalse(result.parse_result.crc_valid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
