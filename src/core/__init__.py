"""
核心转换模块 - Modbus RTU 数据转换引擎
支持多种数据类型和字节序规则
"""
import struct
from typing import Tuple, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """数据类型枚举"""
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    INT16 = "int16"
    UINT16 = "uint16"
    INT32 = "int32"
    UINT32 = "uint32"
    BCD = "bcd"
    STRING = "string"


class ByteOrder(Enum):
    """字节序规则枚举"""
    BADC = 1  # 规则1：B A D C
    CDAB = 2  # 规则2：C D A B（通用工业规则）
    ABCD = 3  # 规则3：A B C D
    DCBA = 4  # 规则4：D C B A


@dataclass
class ParseResult:
    """报文解析结果"""
    slave_addr: str = ""
    func_code: str = ""
    data_len: str = ""
    data_hex: str = ""
    input_crc: str = ""
    calc_crc: str = ""
    crc_valid: bool = False


@dataclass
class ConvertResult:
    """转换结果"""
    success: bool
    value: Optional[Any]
    parse_result: Optional[ParseResult]
    error_msg: str = ""
