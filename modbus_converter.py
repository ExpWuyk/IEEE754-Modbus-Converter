import struct
import tkinter as tk
from tkinter import messagebox, ttk, Menu, filedialog, simpledialog
import configparser
import os
import binascii
import csv
from datetime import datetime
import json
import threading
from tkinter.ttk import Progressbar

# -------------------------- 全局配置 --------------------------
# 日志文件夹路径
LOG_DIR = "modbus_converter_logs"
# 最近记录保存路径
RECENT_RECORDS_PATH = "modbus_recent_records.json"
# 最近记录最大条数
MAX_RECENT_RECORDS = 20

# 创建必要文件夹
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# -------------------------- 核心工具函数 --------------------------
def calculate_crc16(modbus_hex):
    """计算Modbus RTU CRC16校验码（返回大写十六进制字符串）"""
    try:
        # 清洗并转换为字节串
        clean_hex = ''.join([c for c in modbus_hex if c in '0123456789ABCDEFabcdef'])
        data = bytes.fromhex(clean_hex[:-4])  # 去掉最后2字节CRC
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        # 转换为2字节十六进制（小端序）
        crc_hex = f"{crc:04X}"
        # Modbus CRC是低字节在前，高字节在后，所以交换顺序
        crc_hex = crc_hex[2:] + crc_hex[:2]
        return crc_hex
    except Exception as e:
        return f"计算失败: {str(e)}"

def modbus_hex_to_value(hex_str, byte_order_rule, data_type):
    """
    核心转换函数：支持多字节序、多数据类型
    :param hex_str: 原始Modbus十六进制字符串
    :param byte_order_rule: 字节序规则（1-4）
    :param data_type: 数据类型（float32/int16/uint16/float64）
    :return: (转换结果, 报文解析字典, CRC校验结果, 错误信息)
    """
    error_msg = ""
    try:
        # 1. 清洗输入
        clean_hex = ''.join([c for c in hex_str if c in '0123456789ABCDEFabcdef']).upper()
        if not clean_hex:
            raise ValueError("输入为空或无有效十六进制字符")
        
        # 2. 校验最小长度
        min_lengths = {
            "float32": 18,  # 9字节：地址1+功能码1+长度1+数据4+CRC2
            "int16": 14,    # 7字节：地址1+功能码1+长度1+数据2+CRC2
            "uint16": 14,
            "float64": 26   # 13字节：地址1+功能码1+长度1+数据8+CRC2
        }
        if len(clean_hex) < min_lengths[data_type]:
            raise ValueError(
                f"报文长度不足！{data_type}类型需至少{min_lengths[data_type]}字符（{min_lengths[data_type]//2}字节），当前{len(clean_hex)}字符"
            )
        
        # 3. 解析报文字段
        parse_result = {
            "slave_addr": clean_hex[0:2],          # 从机地址（1字节）
            "func_code": clean_hex[2:4],           # 功能码（1字节）
            "data_len": clean_hex[4:6],            # 数据长度（1字节）
            "data_hex": "",                        # 数据部分
            "input_crc": clean_hex[-4:],           # 用户输入的CRC
            "calc_crc": calculate_crc16(clean_hex) # 计算的CRC
        }
        # 校验功能码
        if parse_result["func_code"] not in ["03", "04"]:
            raise ValueError(f"仅支持功能码03/04！当前功能码为{parse_result['func_code']}")
        
        # 4. 提取对应长度的数据部分
        data_len_int = int(parse_result["data_len"], 16)
        data_type_lengths = {
            "float32": 4, "int16": 2, "uint16": 2, "float64": 8
        }
        if data_len_int != data_type_lengths[data_type]:
            raise ValueError(
                f"{data_type}类型需{data_type_lengths[data_type]}字节数据！当前数据长度为{data_len_int}字节"
            )
        parse_result["data_hex"] = clean_hex[6:6 + data_len_int*2]
        
        # 5. CRC校验结果
        crc_check = "通过" if parse_result["calc_crc"] == parse_result["input_crc"] and not parse_result["calc_crc"].startswith("计算失败") else "失败"
        
        # 6. 按数据类型转换
        value = None
        data_bytes = bytes.fromhex(parse_result["data_hex"])
        
        # 6.1 16位整数（int16/uint16）
        if data_type in ["int16", "uint16"]:
            if data_type == "int16":
                value = int.from_bytes(data_bytes, byteorder='big', signed=True)
            else:
                value = int.from_bytes(data_bytes, byteorder='big', signed=False)
        
        # 6.2 32位浮点数（float32）- 替换为A/B/C/D命名
        elif data_type == "float32":
            # 拆分4个字节（A=寄存器1高, B=寄存器1低, C=寄存器2高, D=寄存器2低）
            A, B, C, D = parse_result["data_hex"][0:2], parse_result["data_hex"][2:4], parse_result["data_hex"][4:6], parse_result["data_hex"][6:8]
            # 字节序规则映射（工业常见4种，标识符改为A/B/C/D）
            order_mapping = {
                1: B + A + D + C,    # 规则1：B A D C
                2: C + D + A + B,    # 规则2：C D A B（你的规则）
                3: A + B + C + D,    # 规则3：A B C D
                4: D + C + B + A     # 规则4：D C B A
            }
            ieee_hex = order_mapping[byte_order_rule]
            ieee_bytes = bytes.fromhex(ieee_hex)
            value = struct.unpack('!f', ieee_bytes)[0]
            value = round(value, 4)  # 保留4位小数
        
        # 6.3 64位浮点数（float64）- 同步替换命名
        elif data_type == "float64":
            # 拆分8个字节
            bytes_list = [parse_result["data_hex"][i:i+2] for i in range(0, 16, 2)]
            A, B, C, D, E, F, G, H = bytes_list  # 扩展命名保持一致性
            # 按规则2扩展的字节序（适配工业场景）
            ieee_hex = E + F + G + H + A + B + C + D
            ieee_bytes = bytes.fromhex(ieee_hex)
            value = struct.unpack('!d', ieee_bytes)[0]
            value = round(value, 6)
        
        return value, parse_result, crc_check, error_msg
    except ValueError as e:
        error_msg = str(e)
        return None, {}, "", error_msg
    except Exception as e:
        error_msg = str(e)
        return None, {}, "", error_msg

def log_error(content):
    """记录错误日志"""
    log_file = os.path.join(LOG_DIR, f"error_log_{datetime.now().strftime('%Y%m%d')}.txt")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {content}\n")

# -------------------------- 最近记录管理 --------------------------
def load_recent_records():
    """加载最近转换记录"""
    if os.path.exists(RECENT_RECORDS_PATH):
        try:
            with open(RECENT_RECORDS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_recent_records(records):
    """保存最近转换记录（限制最大条数）"""
    # 去重 + 限制条数
    unique_records = []
    seen = set()
    for record in records:
        if record["hex_str"] not in seen:
            seen.add(record["hex_str"])
            unique_records.append(record)
    if len(unique_records) > MAX_RECENT_RECORDS:
        unique_records = unique_records[:MAX_RECENT_RECORDS]
    
    try:
        with open(RECENT_RECORDS_PATH, 'w', encoding='utf-8') as f:
            json.dump(unique_records, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"保存最近记录失败：{str(e)}")

def add_recent_record(hex_str, byte_order, data_type, result):
    """添加最近转换记录"""
    records = load_recent_records()
    records.insert(0, {
        "hex_str": hex_str,
        "byte_order": byte_order,
        "data_type": data_type,
        "result": result,
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })
    save_recent_records(records)

# -------------------------- GUI界面与交互 --------------------------
class ModbusConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modbus RTU 数据转换工具 V2.1")
        self.root.geometry("900x750")
        self.root.minsize(900, 750)
        
        # 配置文件路径
        self.config_path = "modbus_converter_config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()
        
        # 初始化变量
        self.byte_order_var = tk.IntVar(value=self.config.getint("Settings", "default_byte_order"))
        self.data_type_var = tk.StringVar(value=self.config.get("Settings", "default_data_type"))
        self.unit_var = tk.StringVar(value="")  # 单位变量
        self.last_result = ""  # 最后转换结果
        self.batch_data = []  # 批量数据列表
        
        # 加载最近记录
        self.recent_records = load_recent_records()
        
        # 构建界面
        self.create_menu()
        self.create_input_area()
        self.create_recent_area()
        self.create_parse_area()
        self.create_convert_area()
        self.create_result_area()
        self.create_batch_area()
        
        # 输入框实时校验
        self.entry_hex.bind('<KeyRelease>', self.on_input_change)

        # 键盘快捷键绑定
        self.root.bind('<Control-Return>', lambda e: self.on_convert())  # Ctrl+Enter 执行转换
        self.root.bind('<Control-v>', self.on_paste_clean)  # Ctrl+V 粘贴并清理格式
        self.root.bind('<Control-c>', self.on_copy_shortcut)  # Ctrl+C 复制结果
        self.root.bind('<F5>', lambda e: self.on_convert())  # F5 执行转换
        self.root.bind('<Escape>', lambda e: self.clear_input())  # Esc 清空输入

        # 拖拽文件支持（需要安装 tkinterdnd2，这里使用简化方案）
        self.setup_drag_drop()

    def load_config(self):
        """加载用户配置"""
        if os.path.exists(self.config_path):
            self.config.read(self.config_path, encoding="utf-8")
        else:
            # 默认配置
            self.config["Settings"] = {
                "default_byte_order": 2,  # 你的规则为默认
                "default_data_type": "float32"
            }
            self.save_config()

    def save_config(self):
        """保存用户配置"""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def create_menu(self):
        """创建菜单"""
        menubar = Menu(self.root)
        
        # 文件菜单
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="导入批量报文", command=self.import_batch_file)
        file_menu.add_command(label="导出批量结果", command=self.export_batch_result)
        file_menu.add_separator()
        file_menu.add_command(label="清空最近记录", command=self.clear_recent_records)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        # 设置菜单
        setting_menu = Menu(menubar, tearoff=0)
        setting_menu.add_command(label="恢复默认设置", command=self.reset_settings)
        menubar.add_cascade(label="设置", menu=setting_menu)
        
        # 帮助菜单
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="字节序规则说明", command=self.show_byte_order_help)
        help_menu.add_command(label="快捷键说明", command=self.show_shortcuts_help)
        help_menu.add_separator()
        help_menu.add_command(label="查看错误日志", command=self.view_log)
        menubar.add_cascade(label="帮助", menu=help_menu)
        
        self.root.config(menu=menubar)

    def create_input_area(self):
        """创建输入区域"""
        frame = ttk.LabelFrame(self.root, text="单条报文输入")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 输入标签
        ttk.Label(frame, text="Modbus RTU十六进制报文（支持带空格/分隔符）：").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # 输入框
        self.entry_hex = ttk.Entry(frame, width=90)
        self.entry_hex.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        # 示例报文
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")
        
        # 单位选择
        ttk.Label(frame, text="单位：").grid(row=1, column=4, sticky=tk.E, padx=5, pady=5)
        unit_options = ["", "立方米/秒", "米/秒", "米", "台时", "自定义"]
        self.unit_combobox = ttk.Combobox(frame, textvariable=self.unit_var, values=unit_options, width=10)
        self.unit_combobox.grid(row=1, column=5, padx=5, pady=5)
        self.unit_combobox.bind('<<ComboboxSelected>>', self.on_unit_select)
        
        # 非法字符提示
        self.label_input_warn = ttk.Label(frame, text="", foreground="red")
        self.label_input_warn.grid(row=2, column=0, columnspan=6, sticky=tk.W, padx=5)
        
        # 快捷按钮
        ttk.Button(frame, text="清空", command=self.clear_input).grid(row=1, column=6, padx=5)
        ttk.Button(frame, text="示例报文", command=self.insert_example).grid(row=1, column=7, padx=5)
        ttk.Button(frame, text="规整格式", command=self.format_hex).grid(row=1, column=8, padx=5)

    def create_recent_area(self):
        """创建最近记录区域"""
        frame = ttk.LabelFrame(self.root, text="最近转换记录")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 最近记录下拉框
        ttk.Label(frame, text="选择历史记录：").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.recent_combobox = ttk.Combobox(frame, width=80)
        self.recent_combobox.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        self.recent_combobox.bind('<<ComboboxSelected>>', self.on_recent_selected)
        # 加载最近记录到下拉框
        self.update_recent_combobox()
        
        # 清空按钮
        ttk.Button(frame, text="清空记录", command=self.clear_recent_records).grid(row=0, column=4, padx=5, pady=5)

    def create_parse_area(self):
        """创建报文解析区域"""
        frame = ttk.LabelFrame(self.root, text="单条报文解析")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 解析字段显示（网格布局）
        fields = [
            ("从机地址", "slave_addr"), ("功能码", "func_code"),
            ("数据长度", "data_len"), ("数据部分", "data_hex"),
            ("输入CRC", "input_crc"), ("计算CRC", "calc_crc"),
            ("CRC校验", "crc_check")
        ]
        self.parse_labels = {}
        for i, (label_text, key) in enumerate(fields):
            ttk.Label(frame, text=f"{label_text}：").grid(row=i//4, column=(i%4)*2, sticky=tk.E, padx=5, pady=3)
            lbl = ttk.Label(frame, text="--", foreground="blue" if key != "crc_check" else "green")
            lbl.grid(row=i//4, column=(i%4)*2+1, sticky=tk.W, padx=5, pady=3)
            self.parse_labels[key] = lbl

    def create_convert_area(self):
        """创建转换配置区域"""
        frame = ttk.LabelFrame(self.root, text="转换配置")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 字节序规则
        ttk.Label(frame, text="字节序规则：").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        order_options = [
            (1, "规则1：B A D C"),
            (2, "规则2：C D A B（推荐）"),
            (3, "规则3：A B C D"),
            (4, "规则4：D C B A")
        ]
        for val, text in order_options:
            ttk.Radiobutton(frame, text=text, variable=self.byte_order_var, value=val).grid(
                row=0, column=val, sticky=tk.W, padx=2, pady=5
            )
        
        # 数据类型
        ttk.Label(frame, text="数据类型：").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        type_options = [("32位浮点数(float32)", "float32"), ("16位有符号整数(int16)", "int16"),
                        ("16位无符号整数(uint16)", "uint16"), ("64位浮点数(float64)", "float64")]
        for i, (text, val) in enumerate(type_options):
            ttk.Radiobutton(frame, text=text, variable=self.data_type_var, value=val).grid(
                row=1, column=i+1, sticky=tk.W, padx=2, pady=5
            )
        
        # 转换按钮
        ttk.Button(frame, text="单条转换", command=self.on_convert).grid(row=2, column=0, columnspan=5, pady=10)

    def create_result_area(self):
        """创建结果显示区域"""
        frame = ttk.LabelFrame(self.root, text="单条转换结果")
        frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 结果显示
        self.label_result = ttk.Label(frame, text="等待转换...", font=("Arial", 12, "bold"))
        self.label_result.grid(row=0, column=0, padx=5, pady=10)
        
        # 复制按钮
        ttk.Button(frame, text="复制结果", command=self.copy_result).grid(row=0, column=1, padx=10, pady=10)

    def create_batch_area(self):
        """创建批量处理区域"""
        frame = ttk.LabelFrame(self.root, text="批量处理")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 批量按钮区域
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="导入TXT/CSV", command=self.import_batch_file).pack(side=tk.LEFT, padx=5)
        self.batch_convert_btn = ttk.Button(btn_frame, text="批量转换", command=self.batch_convert)
        self.batch_convert_btn.pack(side=tk.LEFT, padx=5)
        self.batch_stop_btn = ttk.Button(btn_frame, text="停止转换", command=self.stop_batch_convert, state=tk.DISABLED)
        self.batch_stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="导出结果", command=self.export_batch_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="清空列表", command=self.clear_batch_list).pack(side=tk.LEFT, padx=5)

        # 进度条区域
        progress_frame = ttk.Frame(frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(progress_frame, text="转换进度：").pack(side=tk.LEFT, padx=5)
        self.batch_progress = Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.batch_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.batch_progress_label = ttk.Label(progress_frame, text="0/0")
        self.batch_progress_label.pack(side=tk.LEFT, padx=5)

        # 批量转换控制变量
        self.batch_converting = False
        self.batch_stop_flag = False
        
        # 批量列表区域
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 批量列表（表格）
        self.batch_tree = ttk.Treeview(frame, yscrollcommand=scrollbar.set, columns=("hex", "status", "result", "crc"), show="headings")
        self.batch_tree.heading("hex", text="原始报文")
        self.batch_tree.heading("status", text="状态")
        self.batch_tree.heading("result", text="转换结果")
        self.batch_tree.heading("crc", text="CRC校验")
        
        # 设置列宽
        self.batch_tree.column("hex", width=400)
        self.batch_tree.column("status", width=80)
        self.batch_tree.column("result", width=150)
        self.batch_tree.column("crc", width=80)
        
        self.batch_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.batch_tree.yview)

    # -------------------------- 交互函数 --------------------------
    def setup_drag_drop(self):
        """设置拖拽文件支持（简化方案：通过监听剪贴板）"""
        # 注：完整拖拽支持需要 tkinterdnd2 库
        # 这里提供一个简化的替代方案：双击批量区域打开文件选择
        pass

    def on_paste_clean(self, event):
        """粘贴并自动清理格式"""
        try:
            # 获取剪贴板内容
            clipboard = self.root.clipboard_get()
            # 清理格式
            clean_hex = ''.join([c for c in clipboard if c in '0123456789ABCDEFabcdef']).upper()
            if clean_hex:
                # 清空并插入清理后的内容
                self.entry_hex.delete(0, tk.END)
                self.entry_hex.insert(0, clean_hex)
                self.on_input_change(None)
                return "break"  # 阻止默认粘贴行为
        except tk.TclError:
            pass  # 剪贴板为空或无法访问

    def on_copy_shortcut(self, event):
        """Ctrl+C 快捷键：如果有选中文本则复制选中，否则复制转换结果"""
        try:
            # 检查是否有选中的文本
            widget = self.root.focus_get()
            if widget and hasattr(widget, 'selection_get'):
                try:
                    widget.selection_get()
                    return  # 有选中文本，使用默认复制行为
                except tk.TclError:
                    pass
            # 没有选中文本，复制转换结果
            if self.last_result:
                self.root.clipboard_clear()
                self.root.clipboard_append(self.last_result)
        except Exception:
            pass

    def on_input_change(self, event):
        """输入框内容变化时的校验"""
        input_str = self.entry_hex.get()
        # 检查非法字符
        illegal_chars = [c for c in input_str if c not in '0123456789ABCDEFabcdef \t-']
        # 计算有效十六进制字符数
        clean_hex = ''.join([c for c in input_str if c in '0123456789ABCDEFabcdef'])
        hex_len = len(clean_hex)
        byte_len = hex_len // 2

        # 构建提示信息
        warn_parts = []
        if illegal_chars:
            warn_parts.append(f"非法字符：{''.join(set(illegal_chars))}")

        # 长度提示
        data_type = self.data_type_var.get()
        min_bytes = {"float32": 9, "int16": 7, "uint16": 7, "float64": 13}
        required = min_bytes.get(data_type, 9)
        if byte_len < required:
            warn_parts.append(f"当前{byte_len}字节，{data_type}需至少{required}字节")
        else:
            # 显示当前长度信息（非警告）
            self.label_input_warn.config(
                text=f"当前：{hex_len}字符 / {byte_len}字节",
                foreground="gray"
            )
            if not illegal_chars:
                return

        if warn_parts:
            self.label_input_warn.config(text=" | ".join(warn_parts), foreground="red")

    def clear_input(self):
        """清空输入框"""
        self.entry_hex.delete(0, tk.END)
        self.label_input_warn.config(text="")
        self.unit_var.set("")

    def insert_example(self):
        """插入示例报文"""
        self.entry_hex.delete(0, tk.END)
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

    def format_hex(self):
        """规整报文格式（去除空格/分隔符，转为大写）"""
        input_str = self.entry_hex.get()
        clean_hex = ''.join([c for c in input_str if c in '0123456789ABCDEFabcdef']).upper()
        self.entry_hex.delete(0, tk.END)
        self.entry_hex.insert(0, clean_hex)

    def on_unit_select(self, event):
        """单位选择事件"""
        if self.unit_var.get() == "自定义":
            custom_unit = simpledialog.askstring("自定义单位", "请输入自定义单位：")
            if custom_unit:
                self.unit_var.set(custom_unit)
                # 添加到下拉框（去重）
                values = list(self.unit_combobox['values'])
                if custom_unit not in values:
                    values.insert(-1, custom_unit)
                    self.unit_combobox['values'] = values

    def update_recent_combobox(self):
        """更新最近记录下拉框"""
        self.recent_records = load_recent_records()
        if self.recent_records:
            display_list = [f"{r['time']} | {r['hex_str']} | 结果：{r['result']}" for r in self.recent_records]
            self.recent_combobox['values'] = display_list
        else:
            self.recent_combobox['values'] = ["暂无最近记录"]

    def on_recent_selected(self, event):
        """选择最近记录事件"""
        selected = self.recent_combobox.get()
        if not selected or selected == "暂无最近记录":
            return
        # 找到对应的记录
        for record in self.recent_records:
            display_text = f"{record['time']} | {record['hex_str']} | 结果：{record['result']}"
            if display_text == selected:
                # 填充到输入框
                self.entry_hex.delete(0, tk.END)
                self.entry_hex.insert(0, record['hex_str'])
                # 恢复配置
                self.byte_order_var.set(record['byte_order'])
                self.data_type_var.set(record['data_type'])
                break

    def clear_recent_records(self):
        """清空最近记录"""
        if messagebox.askyesno("确认", "是否清空所有最近转换记录？"):
            save_recent_records([])
            self.update_recent_combobox()
            messagebox.showinfo("提示", "最近记录已清空！")

    def on_convert(self):
        """执行单条转换"""
        # 保存当前配置
        self.config["Settings"]["default_byte_order"] = str(self.byte_order_var.get())
        self.config["Settings"]["default_data_type"] = self.data_type_var.get()
        self.save_config()
        
        # 获取输入
        input_str = self.entry_hex.get().strip()
        if not input_str:
            messagebox.showwarning("提示", "请输入Modbus十六进制报文！")
            return
        
        try:
            # 执行转换
            value, parse_result, crc_check, error_msg = modbus_hex_to_value(
                input_str,
                self.byte_order_var.get(),
                self.data_type_var.get()
            )
            
            if error_msg:
                raise ValueError(error_msg)
            
            # 更新解析区域
            for key, lbl in self.parse_labels.items():
                if key == "crc_check":
                    lbl.config(text=crc_check, foreground="green" if crc_check == "通过" else "red")
                else:
                    lbl.config(text=parse_result.get(key, "--"))
            
            # 更新结果区域（添加单位）
            unit = self.unit_var.get()
            result_text = f"转换结果：{value} {unit}" if unit else f"转换结果：{value}"
            self.label_result.config(text=result_text, foreground="green")
            self.last_result = str(value)  # 保存最后结果用于复制
            
            # 添加到最近记录
            add_recent_record(input_str, self.byte_order_var.get(), self.data_type_var.get(), value)
            self.update_recent_combobox()
            
        except ValueError as e:
            self.label_result.config(text="转换失败！", foreground="red")
            log_error(f"单条转换失败：{str(e)} | 输入：{input_str}")
            messagebox.showerror("输入错误", str(e))
        except Exception as e:
            self.label_result.config(text="转换失败！", foreground="red")
            log_error(f"单条转换系统错误：{str(e)} | 输入：{input_str}")
            messagebox.showerror("系统错误", f"转换出错：{str(e)}\n请检查输入格式或联系开发者")

    def copy_result(self):
        """复制结果到剪贴板"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_result)
            messagebox.showinfo("成功", "结果已复制到剪贴板！")
        except AttributeError:
            messagebox.showwarning("提示", "暂无可复制的结果！")
        except Exception as e:
            log_error(f"复制结果失败：{str(e)}")
            messagebox.showerror("错误", f"复制失败：{str(e)}")

    def reset_settings(self):
        """恢复默认设置"""
        self.config["Settings"]["default_byte_order"] = "2"
        self.config["Settings"]["default_data_type"] = "float32"
        self.save_config()
        self.byte_order_var.set(2)
        self.data_type_var.set("float32")
        self.unit_var.set("")
        messagebox.showinfo("提示", "已恢复默认设置！")

    # -------------------------- 批量处理函数 --------------------------
    def import_batch_file(self):
        """导入批量报文文件（TXT/CSV）"""
        file_path = filedialog.askopenfilename(
            title="选择批量报文文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not file_path:
            return
        
        try:
            self.batch_data = []
            # 清空表格
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.csv'):
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            hex_str = row[0].strip()
                            self.batch_data.append({"hex": hex_str, "status": "未转换", "result": "", "crc": ""})
                else:
                    for line in f:
                        hex_str = line.strip()
                        if hex_str:
                            self.batch_data.append({"hex": hex_str, "status": "未转换", "result": "", "crc": ""})
            
            # 填充表格
            for idx, data in enumerate(self.batch_data):
                self.batch_tree.insert("", tk.END, iid=idx, values=(data["hex"], data["status"], data["result"], data["crc"]))
            
            messagebox.showinfo("成功", f"已导入{len(self.batch_data)}条报文！")
        except Exception as e:
            log_error(f"批量导入失败：{str(e)} | 文件：{file_path}")
            messagebox.showerror("错误", f"导入失败：{str(e)}")

    def stop_batch_convert(self):
        """停止批量转换"""
        self.batch_stop_flag = True

    def batch_convert(self):
        """批量转换"""
        if not self.batch_data:
            messagebox.showwarning("提示", "请先导入批量报文！")
            return

        if self.batch_converting:
            messagebox.showwarning("提示", "正在转换中，请等待完成或点击停止！")
            return

        if messagebox.askyesno("确认", f"是否转换当前{len(self.batch_data)}条报文？"):
            # 启动多线程转换
            self.batch_converting = True
            self.batch_stop_flag = False
            self.batch_convert_btn.config(state=tk.DISABLED)
            self.batch_stop_btn.config(state=tk.NORMAL)
            self.batch_progress['value'] = 0
            self.batch_progress['maximum'] = len(self.batch_data)

            # 在新线程中执行转换
            thread = threading.Thread(target=self._batch_convert_thread, daemon=True)
            thread.start()

    def _batch_convert_thread(self):
        """批量转换线程"""
        total = len(self.batch_data)
        success_count = 0
        fail_count = 0

        for idx, data in enumerate(self.batch_data):
            # 检查停止标志
            if self.batch_stop_flag:
                self.root.after(0, lambda: messagebox.showinfo("提示", f"转换已停止！已完成 {idx}/{total} 条"))
                break

            hex_str = data["hex"]
            try:
                value, parse_result, crc_check, error_msg = modbus_hex_to_value(
                    hex_str,
                    self.byte_order_var.get(),
                    self.data_type_var.get()
                )

                if error_msg:
                    raise ValueError(error_msg)

                # 更新数据
                self.batch_data[idx]["status"] = "成功"
                self.batch_data[idx]["result"] = str(value)
                self.batch_data[idx]["crc"] = crc_check
                success_count += 1

                # 在主线程更新UI
                self.root.after(0, lambda i=idx, h=hex_str, v=value, c=crc_check:
                    self.batch_tree.item(i, values=(h, "成功", str(v), c)))
            except Exception as e:
                self.batch_data[idx]["status"] = "失败"
                self.batch_data[idx]["result"] = str(e)
                self.batch_data[idx]["crc"] = ""
                fail_count += 1
                self.root.after(0, lambda i=idx, h=hex_str, err=str(e):
                    self.batch_tree.item(i, values=(h, "失败", err, "")))
                log_error(f"批量转换失败：{str(e)} | 输入：{hex_str}")

            # 更新进度条
            self.root.after(0, lambda i=idx+1, t=total: self._update_batch_progress(i, t))

        # 转换完成
        self.root.after(0, lambda: self._batch_convert_complete(success_count, fail_count, total))

    def _update_batch_progress(self, current, total):
        """更新批量转换进度"""
        self.batch_progress['value'] = current
        self.batch_progress_label.config(text=f"{current}/{total}")

    def _batch_convert_complete(self, success, fail, total):
        """批量转换完成回调"""
        self.batch_converting = False
        self.batch_convert_btn.config(state=tk.NORMAL)
        self.batch_stop_btn.config(state=tk.DISABLED)
        if not self.batch_stop_flag:
            messagebox.showinfo("完成", f"批量转换已完成！\n成功：{success} 条\n失败：{fail} 条\n总计：{total} 条")

    def export_batch_result(self):
        """导出批量结果"""
        if not self.batch_data:
            messagebox.showwarning("提示", "暂无批量数据可导出！")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存批量结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # 写入表头
                writer.writerow(["原始报文", "转换状态", "转换结果", "CRC校验"])
                # 写入数据
                for data in self.batch_data:
                    writer.writerow([data["hex"], data["status"], data["result"], data["crc"]])
            
            messagebox.showinfo("成功", f"批量结果已导出到：{file_path}")
        except Exception as e:
            log_error(f"批量导出失败：{str(e)} | 文件：{file_path}")
            messagebox.showerror("错误", f"导出失败：{str(e)}")

    def clear_batch_list(self):
        """清空批量列表"""
        if messagebox.askyesno("确认", "是否清空批量列表？"):
            self.batch_data = []
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)
            messagebox.showinfo("提示", "批量列表已清空！")

    # -------------------------- 帮助与日志函数 --------------------------
    def show_help(self):
        """显示使用说明"""
        help_text = """
        Modbus RTU数据转换工具 V2.0 使用说明：
        一、单条转换
        1. 输入：支持带空格/分隔符(-)的十六进制报文，如"02 03 04 05 1F 42 C9 08 CF"
        2. 配置：
           - 字节序规则：选择适配你的设备的规则（规则2为通用工业规则）
           - 数据类型：根据实际需求选择（默认float32）
           - 单位：可选常用单位或自定义，转换结果会显示单位
        3. 转换：点击「单条转换」，下方会显示解析结果和转换值
        4. 复制：转换成功后可点击「复制结果」将数值复制到剪贴板
        
        二、批量转换
        1. 导入：点击「导入TXT/CSV」，支持每行1条报文的TXT或CSV文件
        2. 转换：点击「批量转换」，自动转换所有导入的报文
        3. 导出：点击「导出结果」，将转换结果保存为CSV文件
        
        三、其他功能
        1. 最近记录：自动保存最近20条转换记录，可直接选择复用
        2. 错误日志：转换失败会自动记录，可在「帮助」→「查看错误日志」中查看
        3. CRC校验：自动计算并校验CRC，失败时请检查报文是否完整
        
        常见问题：
        - 转换结果不对？→ 切换字节序规则重试
        - CRC校验失败？→ 检查报文是否少输/多输字符
        - 长度不足？→ 确认数据类型与报文长度匹配
        """
        messagebox.showinfo("使用说明", help_text)

    def show_byte_order_help(self):
        """显示字节序规则说明（同步更新为A/B/C/D）"""
        order_help = """
        Modbus浮点数字节序规则说明（以4字节数据A B C D为例）：
        A=寄存器1高字节 | B=寄存器1低字节 | C=寄存器2高字节 | D=寄存器2低字节
        
        规则1（B A D C）：部分国产小厂设备
        规则2（C D A B）：通用工业规则（西门子/施耐德等）
        规则3（A B C D）：三菱/欧姆龙部分设备
        规则4（D C B A）：极少厂商使用
        
        若转换结果不符，依次切换规则重试即可！
        """
        messagebox.showinfo("字节序规则说明", order_help)

    def show_shortcuts_help(self):
        """显示快捷键说明"""
        shortcuts_help = """
        快捷键说明：

        Ctrl + Enter    执行单条转换
        F5              执行单条转换
        Ctrl + V        粘贴并自动清理格式
        Ctrl + C        复制转换结果（无选中文本时）
        Esc             清空输入框

        提示：粘贴时会自动去除空格和分隔符，转为大写格式
        """
        messagebox.showinfo("快捷键说明", shortcuts_help)

    def view_log(self):
        """查看错误日志"""
        log_files = [f for f in os.listdir(LOG_DIR) if f.startswith("error_log_") and f.endswith(".txt")]
        if not log_files:
            messagebox.showinfo("提示", "暂无错误日志！")
            return
        
        # 选择日志文件
        log_file = filedialog.askopenfilename(
            title="选择错误日志文件",
            initialdir=LOG_DIR,
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if not log_file:
            return
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # 新建窗口显示日志
            log_window = tk.Toplevel(self.root)
            log_window.title("错误日志")
            log_window.geometry("800x600")
            
            text = tk.Text(log_window)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text.insert(tk.END, content)
            text.config(state=tk.DISABLED)  # 只读
        except Exception as e:
            messagebox.showerror("错误", f"打开日志失败：{str(e)}")

# -------------------------- 程序入口 --------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = ModbusConverterApp(root)
    root.mainloop()