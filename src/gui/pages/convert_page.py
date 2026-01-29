"""数据转换页面"""
import customtkinter as ctk
from tkinter import messagebox
from src.gui.themes import COLORS
from src.gui.components import CardFrame, CollapsibleFrame
from src.core import DataType, ByteOrder
from src.core.converter import ModbusConverter


class ConvertPage(ctk.CTkFrame):
    """数据转换页面"""

    def __init__(self, master, config_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.last_result = ""

        self._init_variables()
        self._create_input_section()
        self._create_config_section()
        self._create_result_section()
        self._create_history_section()

    def _init_variables(self):
        """初始化变量"""
        config = self.config_manager.config
        self.byte_order_var = ctk.IntVar(value=config.default_byte_order)
        self.data_type_var = ctk.StringVar(value=config.default_data_type)
        self.unit_var = ctk.StringVar(value=config.default_unit)

    def _create_input_section(self):
        """创建输入区"""
        input_card = CardFrame(self, title="输入报文")
        input_card.pack(fill="x", padx=10, pady=5)

        # 输入行
        input_row = ctk.CTkFrame(input_card.content_frame, fg_color="transparent")
        input_row.pack(fill="x", pady=5)

        self.entry_hex = ctk.CTkEntry(
            input_row,
            placeholder_text="输入 Modbus RTU 十六进制报文...",
            height=40,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.entry_hex.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

        # 单位选择
        self.unit_combo = ctk.CTkComboBox(
            input_row,
            values=["", "立方米/秒", "米/秒", "米", "台时"],
            variable=self.unit_var,
            width=100,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.unit_combo.pack(side="left", padx=(0, 10))

        # 转换按钮
        self.convert_btn = ctk.CTkButton(
            input_row,
            text="转换 (F5)",
            width=100,
            height=40,
            fg_color=COLORS["accent"],
            hover_color="#106ebe",
            command=self._on_convert
        )
        self.convert_btn.pack(side="left")

        # 工具按钮行
        tool_row = ctk.CTkFrame(input_card.content_frame, fg_color="transparent")
        tool_row.pack(fill="x", pady=(5, 0))

        for text, cmd in [("清空", self._clear_input), ("示例", self._insert_example), ("格式化", self._format_hex)]:
            ctk.CTkButton(
                tool_row, text=text, width=60, height=28,
                fg_color="transparent", border_width=1, border_color=COLORS["border"],
                hover_color=COLORS["bg_input"], command=cmd
            ).pack(side="left", padx=(0, 5))

        # 状态标签
        self.input_status = ctk.CTkLabel(
            tool_row, text="", text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=11)
        )
        self.input_status.pack(side="right")

        # 绑定输入事件
        self.entry_hex.bind("<KeyRelease>", self._on_input_change)

    def _create_config_section(self):
        """创建配置区"""
        config_card = CardFrame(self, title="转换配置")
        config_card.pack(fill="x", padx=10, pady=5)

        # 数据类型行
        type_row = ctk.CTkFrame(config_card.content_frame, fg_color="transparent")
        type_row.pack(fill="x", pady=5)

        ctk.CTkLabel(type_row, text="数据类型:", text_color=COLORS["text"]).pack(side="left", padx=(0, 10))

        types = [("Float32", "float32"), ("Float64", "float64"), ("Int16", "int16"),
                 ("UInt16", "uint16"), ("Int32", "int32"), ("UInt32", "uint32")]
        for label, value in types:
            ctk.CTkRadioButton(
                type_row, text=label, variable=self.data_type_var, value=value,
                fg_color=COLORS["accent"], hover_color=COLORS["accent"]
            ).pack(side="left", padx=5)

        # 字节序行
        order_row = ctk.CTkFrame(config_card.content_frame, fg_color="transparent")
        order_row.pack(fill="x", pady=5)

        ctk.CTkLabel(order_row, text="字节序:", text_color=COLORS["text"]).pack(side="left", padx=(0, 10))

        orders = [("BADC (规则1)", 1), ("CDAB (规则2)", 2), ("ABCD (规则3)", 3), ("DCBA (规则4)", 4)]
        for label, value in orders:
            ctk.CTkRadioButton(
                order_row, text=label, variable=self.byte_order_var, value=value,
                fg_color=COLORS["accent"], hover_color=COLORS["accent"]
            ).pack(side="left", padx=5)

    def _create_result_section(self):
        """创建结果区 - 左右分栏"""
        result_container = ctk.CTkFrame(self, fg_color="transparent")
        result_container.pack(fill="both", expand=True, padx=10, pady=5)
        result_container.grid_columnconfigure(0, weight=1)
        result_container.grid_columnconfigure(1, weight=1)

        # 左侧：解析结果
        parse_card = CardFrame(result_container, title="报文解析")
        parse_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.parse_labels = {}
        fields = [("slave_addr", "从站地址"), ("func_code", "功能码"),
                  ("data_len", "数据长度"), ("data_hex", "数据内容"),
                  ("input_crc", "报文CRC"), ("calc_crc", "计算CRC"), ("crc_check", "校验结果")]

        for key, label in fields:
            row = ctk.CTkFrame(parse_card.content_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label}:", width=80, anchor="e",
                        text_color=COLORS["text_secondary"]).pack(side="left")
            lbl = ctk.CTkLabel(row, text="--", text_color=COLORS["text"])
            lbl.pack(side="left", padx=10)
            self.parse_labels[key] = lbl

        # 右侧：转换结果
        value_card = CardFrame(result_container, title="转换结果")
        value_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # 结果行（数值和单位在同一行）
        result_row = ctk.CTkFrame(value_card.content_frame, fg_color="transparent")
        result_row.pack(pady=20)

        self.result_value = ctk.CTkLabel(
            result_row,
            text="等待转换...",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"]
        )
        self.result_value.pack(side="left")

        self.result_unit = ctk.CTkLabel(
            result_row, text="",
            font=ctk.CTkFont(size=18), text_color=COLORS["text_secondary"]
        )
        self.result_unit.pack(side="left", padx=(10, 0))

        ctk.CTkButton(
            value_card.content_frame, text="复制结果", width=100,
            fg_color=COLORS["accent"], command=self._copy_result
        ).pack(pady=15)

    def _create_history_section(self):
        """创建历史记录区（可折叠）"""
        self.history_frame = CollapsibleFrame(self, title="历史记录", collapsed=True)
        self.history_frame.pack(fill="x", padx=10, pady=5)

        self.history_list = ctk.CTkTextbox(
            self.history_frame.content_frame, height=100,
            fg_color=COLORS["bg_input"], text_color=COLORS["text"]
        )
        self.history_list.pack(fill="x", pady=5)

    # ========== 事件处理方法 ==========

    def _on_input_change(self, event):
        text = self.entry_hex.get()
        clean = ModbusConverter.clean_hex_string(text)
        self.input_status.configure(text=f"{len(clean)}字符 / {len(clean)//2}字节")

    def _clear_input(self):
        self.entry_hex.delete(0, "end")
        self.input_status.configure(text="")

    def _insert_example(self):
        self.entry_hex.delete(0, "end")
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

    def _format_hex(self):
        text = self.entry_hex.get()
        clean = ModbusConverter.clean_hex_string(text)
        self.entry_hex.delete(0, "end")
        self.entry_hex.insert(0, clean)

    def _on_convert(self):
        hex_str = self.entry_hex.get().strip()
        if not hex_str:
            messagebox.showwarning("警告", "请输入报文数据")
            return

        byte_order = ByteOrder(self.byte_order_var.get())
        data_type = DataType(self.data_type_var.get())
        result = ModbusConverter.convert(hex_str, byte_order, data_type)

        if result.success:
            pr = result.parse_result
            self.parse_labels["slave_addr"].configure(text=pr.slave_addr)
            self.parse_labels["func_code"].configure(text=pr.func_code)
            self.parse_labels["data_len"].configure(text=pr.data_len)
            self.parse_labels["data_hex"].configure(text=pr.data_hex)
            self.parse_labels["input_crc"].configure(text=pr.input_crc)
            self.parse_labels["calc_crc"].configure(text=pr.calc_crc)

            crc_text = "✓ 通过" if pr.crc_valid else "✗ 失败"
            crc_color = COLORS["success"] if pr.crc_valid else COLORS["error"]
            self.parse_labels["crc_check"].configure(text=crc_text, text_color=crc_color)

            self.result_value.configure(text=str(result.value), text_color=COLORS["success"])
            self.result_unit.configure(text=self.unit_var.get())
            self.last_result = str(result.value)
        else:
            self.result_value.configure(text="转换失败", text_color=COLORS["error"])
            messagebox.showerror("错误", result.error_msg)

    def _copy_result(self):
        if self.last_result:
            self.clipboard_clear()
            self.clipboard_append(self.last_result)
            messagebox.showinfo("成功", "已复制到剪贴板")
