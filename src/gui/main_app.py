"""
Modbus RTU 数据转换工具 V3.0
主应用程序 - 现代化界面
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import csv
from datetime import datetime
from typing import Optional

# 导入自定义模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import DataType, ByteOrder, ConvertResult
from src.core.converter import ModbusConverter
from src.core.serial_comm import SerialCommunicator, SerialConfig
from src.utils.logger import log
from src.utils.config_manager import config_manager
from src.i18n import i18n, t
from src.gui.themes import ThemeManager


class ModbusConverterApp:
    """Modbus RTU 数据转换工具主应用"""

    VERSION = "3.0.0"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = config_manager.config

        # 初始化国际化
        i18n.set_language(self.config.language)

        # 初始化主题
        ThemeManager.set_theme(self.config.theme)

        # 设置窗口
        self._setup_window()

        # 初始化变量
        self._init_variables()

        # 初始化串口
        self.serial = SerialCommunicator()

        # 构建界面
        self._create_menu()
        self._create_notebook()

        # 绑定快捷键
        self._bind_shortcuts()

        # 加载历史记录
        self._load_history()

        log.info(f"应用启动 - 版本 {self.VERSION}")

    def _setup_window(self):
        """设置窗口"""
        self.root.title(f"{t('app_title')} V{self.VERSION}")
        self.root.geometry(f"{self.config.window_width}x{self.config.window_height}")
        self.root.minsize(900, 700)

        # 设置图标（如果存在）
        icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "icons", "app.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)

        # 窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _init_variables(self):
        """初始化变量"""
        self.byte_order_var = tk.IntVar(value=self.config.default_byte_order)
        self.data_type_var = tk.StringVar(value=self.config.default_data_type)
        self.unit_var = tk.StringVar(value=self.config.default_unit)
        self.last_result = ""
        self.batch_data = []
        self.batch_converting = False
        self.batch_stop_flag = False
        self.history_records = []

    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<Control-Return>', lambda e: self._on_convert())
        self.root.bind('<F5>', lambda e: self._on_convert())
        self.root.bind('<Control-v>', self._on_paste_clean)
        self.root.bind('<Escape>', lambda e: self._clear_input())

    def _on_closing(self):
        """窗口关闭事件"""
        # 保存窗口大小
        config_manager.update_config(
            window_width=self.root.winfo_width(),
            window_height=self.root.winfo_height()
        )
        # 断开串口
        if self.serial.is_connected():
            self.serial.disconnect()
        log.info("应用关闭")
        self.root.destroy()

    def _create_menu(self):
        """创建菜单"""
        menubar = tk.Menu(self.root)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label=t("menu_import"), command=self._import_batch_file)
        file_menu.add_command(label=t("menu_export"), command=self._export_batch_result)
        file_menu.add_separator()
        file_menu.add_command(label=t("menu_clear_history"), command=self._clear_history)
        file_menu.add_separator()
        file_menu.add_command(label=t("menu_exit"), command=self._on_closing)
        menubar.add_cascade(label=t("menu_file"), menu=file_menu)

        # 设置菜单
        settings_menu = tk.Menu(menubar, tearoff=0)

        # 主题子菜单
        theme_menu = tk.Menu(settings_menu, tearoff=0)
        for theme in ThemeManager.get_available_themes():
            theme_menu.add_command(label=theme.capitalize(),
                                   command=lambda th=theme: self._change_theme(th))
        settings_menu.add_cascade(label=t("menu_theme"), menu=theme_menu)

        # 语言子菜单
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        lang_names = {"zh_CN": "中文", "en_US": "English"}
        for lang in i18n.get_available_languages():
            lang_menu.add_command(label=lang_names.get(lang, lang),
                                  command=lambda l=lang: self._change_language(l))
        settings_menu.add_cascade(label=t("menu_language"), menu=lang_menu)

        settings_menu.add_separator()
        settings_menu.add_command(label=t("menu_reset"), command=self._reset_settings)
        menubar.add_cascade(label=t("menu_settings"), menu=settings_menu)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label=t("menu_usage"), command=self._show_help)
        help_menu.add_command(label=t("menu_byte_order"), command=self._show_byte_order_help)
        help_menu.add_command(label=t("menu_shortcuts"), command=self._show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label=t("menu_view_log"), command=self._view_log)
        help_menu.add_separator()
        help_menu.add_command(label=t("menu_about"), command=self._show_about)
        menubar.add_cascade(label=t("menu_help"), menu=help_menu)

        self.root.config(menu=menubar)

    def _create_notebook(self):
        """创建选项卡界面"""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 转换页面
        self.convert_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.convert_frame, text="数据转换")
        self._create_convert_page()

        # 串口通信页面
        self.serial_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.serial_frame, text="串口通信")
        self._create_serial_page()

        # 批量处理页面
        self.batch_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.batch_frame, text="批量处理")
        self._create_batch_page()

    def _create_convert_page(self):
        """创建转换页面"""
        # 输入区域
        input_frame = ttk.LabelFrame(self.convert_frame, text=t("input_title"))
        input_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(input_frame, text=t("input_label")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.entry_hex = ttk.Entry(input_frame, width=80)
        self.entry_hex.grid(row=1, column=0, columnspan=4, padx=5, pady=5, sticky=tk.EW)
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")
        self.entry_hex.bind('<KeyRelease>', self._on_input_change)

        ttk.Label(input_frame, text=t("input_unit")).grid(row=1, column=4, sticky=tk.E, padx=5)
        units = ["", "立方米/秒", "米/秒", "米", "台时", "自定义"]
        self.unit_combo = ttk.Combobox(input_frame, textvariable=self.unit_var, values=units, width=10)
        self.unit_combo.grid(row=1, column=5, padx=5)
        self.unit_combo.bind('<<ComboboxSelected>>', self._on_unit_select)

        self.input_warn_label = ttk.Label(input_frame, text="", foreground="gray")
        self.input_warn_label.grid(row=2, column=0, columnspan=6, sticky=tk.W, padx=5)

        btn_frame = ttk.Frame(input_frame)
        btn_frame.grid(row=1, column=6, columnspan=3, padx=5)
        ttk.Button(btn_frame, text=t("btn_clear"), command=self._clear_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text=t("btn_example"), command=self._insert_example).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text=t("btn_format"), command=self._format_hex).pack(side=tk.LEFT, padx=2)

        # 历史记录区域
        history_frame = ttk.LabelFrame(self.convert_frame, text=t("history_title"))
        history_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(history_frame, text=t("history_select")).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.history_combo = ttk.Combobox(history_frame, width=80)
        self.history_combo.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.EW)
        self.history_combo.bind('<<ComboboxSelected>>', self._on_history_selected)

        # 解析区域
        parse_frame = ttk.LabelFrame(self.convert_frame, text=t("parse_title"))
        parse_frame.pack(fill=tk.X, padx=10, pady=5)

        fields = [
            ("slave_addr", t("slave_addr")), ("func_code", t("func_code")),
            ("data_len", t("data_len")), ("data_hex", t("data_hex")),
            ("input_crc", t("input_crc")), ("calc_crc", t("calc_crc")),
            ("crc_check", t("crc_check"))
        ]
        self.parse_labels = {}
        for i, (key, label_text) in enumerate(fields):
            ttk.Label(parse_frame, text=f"{label_text}：").grid(row=i//4, column=(i%4)*2, sticky=tk.E, padx=5, pady=3)
            lbl = ttk.Label(parse_frame, text="--", foreground="blue")
            lbl.grid(row=i//4, column=(i%4)*2+1, sticky=tk.W, padx=5, pady=3)
            self.parse_labels[key] = lbl

        # 转换配置区域
        config_frame = ttk.LabelFrame(self.convert_frame, text=t("convert_title"))
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(config_frame, text=t("byte_order")).grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        orders = [(1, t("order_1")), (2, t("order_2")), (3, t("order_3")), (4, t("order_4"))]
        for val, text in orders:
            ttk.Radiobutton(config_frame, text=text, variable=self.byte_order_var, value=val).grid(
                row=0, column=val, sticky=tk.W, padx=2)

        ttk.Label(config_frame, text=t("data_type")).grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        types = [("float32", "32位浮点数"), ("float64", "64位浮点数"),
                 ("int16", "16位有符号整数"), ("uint16", "16位无符号整数"),
                 ("int32", "32位有符号整数"), ("uint32", "32位无符号整数")]
        for i, (val, text) in enumerate(types):
            ttk.Radiobutton(config_frame, text=text, variable=self.data_type_var, value=val).grid(
                row=1, column=i+1, sticky=tk.W, padx=2)

        ttk.Button(config_frame, text=t("btn_convert"), command=self._on_convert).grid(
            row=2, column=0, columnspan=7, pady=10)

        # 结果区域
        result_frame = ttk.LabelFrame(self.convert_frame, text=t("result_title"))
        result_frame.pack(fill=tk.X, padx=10, pady=5)

        self.result_label = ttk.Label(result_frame, text=t("result_waiting"), font=("Arial", 14, "bold"))
        self.result_label.grid(row=0, column=0, padx=10, pady=15)
        ttk.Button(result_frame, text=t("btn_copy"), command=self._copy_result).grid(row=0, column=1, padx=10)

    def _create_serial_page(self):
        """创建串口通信页面"""
        # 串口配置区域
        config_frame = ttk.LabelFrame(self.serial_frame, text=t("serial_title"))
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # 串口选择
        ttk.Label(config_frame, text=t("serial_port")).grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(config_frame, textvariable=self.port_var, width=15)
        self.port_combo.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(config_frame, text=t("btn_refresh"), command=self._refresh_ports).grid(row=0, column=2, padx=5)

        # 波特率
        ttk.Label(config_frame, text=t("serial_baudrate")).grid(row=0, column=3, sticky=tk.E, padx=5)
        self.baudrate_var = tk.StringVar(value="9600")
        baudrates = ["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"]
        ttk.Combobox(config_frame, textvariable=self.baudrate_var, values=baudrates, width=10).grid(row=0, column=4, padx=5)

        # 校验位
        ttk.Label(config_frame, text=t("serial_parity")).grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        self.parity_var = tk.StringVar(value="N")
        ttk.Combobox(config_frame, textvariable=self.parity_var, values=["N", "E", "O"], width=5).grid(row=1, column=1, padx=5)

        # 停止位
        ttk.Label(config_frame, text=t("serial_stopbits")).grid(row=1, column=3, sticky=tk.E, padx=5)
        self.stopbits_var = tk.StringVar(value="1")
        ttk.Combobox(config_frame, textvariable=self.stopbits_var, values=["1", "2"], width=5).grid(row=1, column=4, padx=5)

        # 连接按钮
        btn_frame = ttk.Frame(config_frame)
        btn_frame.grid(row=0, column=5, rowspan=2, padx=20)
        self.connect_btn = ttk.Button(btn_frame, text=t("btn_connect"), command=self._toggle_serial)
        self.connect_btn.pack(pady=5)
        self.serial_status_label = ttk.Label(btn_frame, text=t("serial_disconnected"), foreground="red")
        self.serial_status_label.pack()

        # 发送区域
        send_frame = ttk.LabelFrame(self.serial_frame, text="发送数据")
        send_frame.pack(fill=tk.X, padx=10, pady=5)

        self.send_entry = ttk.Entry(send_frame, width=80)
        self.send_entry.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        ttk.Button(send_frame, text=t("btn_send"), command=self._send_serial_data).pack(side=tk.LEFT, padx=5)

        # 接收区域
        recv_frame = ttk.LabelFrame(self.serial_frame, text="接收数据")
        recv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.recv_text = tk.Text(recv_frame, height=15, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(recv_frame, command=self.recv_text.yview)
        self.recv_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.recv_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_frame2 = ttk.Frame(recv_frame)
        btn_frame2.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame2, text="清空", command=self._clear_recv).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame2, text="转换选中", command=self._convert_selected).pack(side=tk.LEFT, padx=5)

        # 刷新串口列表
        self._refresh_ports()

    def _create_batch_page(self):
        """创建批量处理页面"""
        # 按钮区域
        btn_frame = ttk.Frame(self.batch_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text=t("btn_import"), command=self._import_batch_file).pack(side=tk.LEFT, padx=5)
        self.batch_convert_btn = ttk.Button(btn_frame, text=t("btn_batch_convert"), command=self._batch_convert)
        self.batch_convert_btn.pack(side=tk.LEFT, padx=5)
        self.batch_stop_btn = ttk.Button(btn_frame, text=t("btn_stop"), command=self._stop_batch, state=tk.DISABLED)
        self.batch_stop_btn.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn_export"), command=self._export_batch_result).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=t("btn_clear_list"), command=self._clear_batch_list).pack(side=tk.LEFT, padx=5)

        # 进度条
        progress_frame = ttk.Frame(self.batch_frame)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(progress_frame, text=t("progress")).pack(side=tk.LEFT, padx=5)
        self.batch_progress = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.batch_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.progress_label = ttk.Label(progress_frame, text="0/0")
        self.progress_label.pack(side=tk.LEFT, padx=5)

        # 数据表格
        tree_frame = ttk.Frame(self.batch_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.batch_tree = ttk.Treeview(tree_frame, yscrollcommand=scrollbar.set,
                                        columns=("hex", "status", "result", "crc"), show="headings")
        self.batch_tree.heading("hex", text=t("col_hex"))
        self.batch_tree.heading("status", text=t("col_status"))
        self.batch_tree.heading("result", text=t("col_result"))
        self.batch_tree.heading("crc", text=t("col_crc"))
        self.batch_tree.column("hex", width=400)
        self.batch_tree.column("status", width=80)
        self.batch_tree.column("result", width=150)
        self.batch_tree.column("crc", width=80)
        self.batch_tree.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.batch_tree.yview)

    # ==================== 事件处理方法 ====================

    def _on_input_change(self, event):
        """输入变化事件"""
        input_str = self.entry_hex.get()
        clean_hex = ModbusConverter.clean_hex_string(input_str)
        hex_len = len(clean_hex)
        byte_len = hex_len // 2

        # 检查非法字符
        illegal = [c for c in input_str if c not in '0123456789ABCDEFabcdef \t-']
        if illegal:
            self.input_warn_label.config(text=f"非法字符：{''.join(set(illegal))}", foreground="red")
        else:
            self.input_warn_label.config(text=f"当前：{hex_len}字符 / {byte_len}字节", foreground="gray")

    def _on_paste_clean(self, event):
        """粘贴并清理"""
        try:
            clipboard = self.root.clipboard_get()
            clean_hex = ModbusConverter.clean_hex_string(clipboard)
            if clean_hex:
                self.entry_hex.delete(0, tk.END)
                self.entry_hex.insert(0, clean_hex)
                self._on_input_change(None)
                return "break"
        except tk.TclError:
            pass

    def _clear_input(self):
        """清空输入"""
        self.entry_hex.delete(0, tk.END)
        self.input_warn_label.config(text="")

    def _insert_example(self):
        """插入示例"""
        self.entry_hex.delete(0, tk.END)
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

    def _format_hex(self):
        """格式化十六进制"""
        input_str = self.entry_hex.get()
        clean_hex = ModbusConverter.clean_hex_string(input_str)
        self.entry_hex.delete(0, tk.END)
        self.entry_hex.insert(0, clean_hex)

    def _on_unit_select(self, event):
        """单位选择"""
        if self.unit_var.get() == "自定义":
            custom = simpledialog.askstring("自定义单位", "请输入单位：")
            if custom:
                self.unit_var.set(custom)

    def _on_convert(self):
        """执行转换"""
        input_str = self.entry_hex.get().strip()
        if not input_str:
            messagebox.showwarning(t("msg_warning"), t("msg_input_empty"))
            return

        try:
            # 获取配置
            byte_order = ByteOrder(self.byte_order_var.get())
            data_type = DataType(self.data_type_var.get())

            # 执行转换
            result = ModbusConverter.convert(input_str, byte_order, data_type)

            if result.success:
                # 更新解析区域
                pr = result.parse_result
                self.parse_labels["slave_addr"].config(text=pr.slave_addr)
                self.parse_labels["func_code"].config(text=pr.func_code)
                self.parse_labels["data_len"].config(text=pr.data_len)
                self.parse_labels["data_hex"].config(text=pr.data_hex)
                self.parse_labels["input_crc"].config(text=pr.input_crc)
                self.parse_labels["calc_crc"].config(text=pr.calc_crc)
                crc_text = t("crc_pass") if pr.crc_valid else t("crc_fail")
                crc_color = "green" if pr.crc_valid else "red"
                self.parse_labels["crc_check"].config(text=crc_text, foreground=crc_color)

                # 更新结果
                unit = self.unit_var.get()
                result_text = f"{t('result_success')} {result.value} {unit}"
                self.result_label.config(text=result_text, foreground="green")
                self.last_result = str(result.value)

                # 保存历史
                self._add_history(input_str, result.value)
                log.info(f"转换成功: {input_str} -> {result.value}")
            else:
                self.result_label.config(text=t("result_fail"), foreground="red")
                messagebox.showerror(t("msg_error"), result.error_msg)
                log.error(f"转换失败: {result.error_msg}")

        except Exception as e:
            self.result_label.config(text=t("result_fail"), foreground="red")
            messagebox.showerror(t("msg_error"), str(e))
            log.exception(f"转换异常: {e}")

    def _copy_result(self):
        """复制结果"""
        if self.last_result:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_result)
            messagebox.showinfo(t("msg_success"), t("msg_copied"))
        else:
            messagebox.showwarning(t("msg_warning"), t("msg_no_result"))

    # ==================== 历史记录方法 ====================

    def _load_history(self):
        """加载历史记录"""
        self.history_records = config_manager.get_history()
        self._update_history_combo()

    def _add_history(self, hex_str: str, result):
        """添加历史记录"""
        record = {
            "hex_str": hex_str,
            "byte_order": self.byte_order_var.get(),
            "data_type": self.data_type_var.get(),
            "result": str(result),
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        config_manager.add_history(record)
        self._load_history()

    def _update_history_combo(self):
        """更新历史下拉框"""
        if self.history_records:
            display = [f"{r['time']} | {r['hex_str']} -> {r['result']}" for r in self.history_records]
            self.history_combo['values'] = display
        else:
            self.history_combo['values'] = [t("history_empty")]

    def _on_history_selected(self, event):
        """选择历史记录"""
        idx = self.history_combo.current()
        if idx >= 0 and idx < len(self.history_records):
            record = self.history_records[idx]
            self.entry_hex.delete(0, tk.END)
            self.entry_hex.insert(0, record['hex_str'])
            self.byte_order_var.set(record['byte_order'])
            self.data_type_var.set(record['data_type'])

    def _clear_history(self):
        """清空历史"""
        if messagebox.askyesno(t("msg_confirm"), t("msg_clear_confirm")):
            config_manager.clear_history()
            self._load_history()

    # ==================== 串口通信方法 ====================

    def _refresh_ports(self):
        """刷新串口列表"""
        ports = self.serial.list_ports()
        self.port_combo['values'] = ports if ports else ["无可用串口"]
        if ports:
            self.port_combo.current(0)

    def _toggle_serial(self):
        """切换串口连接"""
        if self.serial.is_connected():
            self.serial.disconnect()
            self.connect_btn.config(text=t("btn_connect"))
            self.serial_status_label.config(text=t("serial_disconnected"), foreground="red")
        else:
            config = SerialConfig(
                port=self.port_var.get(),
                baudrate=int(self.baudrate_var.get()),
                parity=self.parity_var.get(),
                stopbits=int(self.stopbits_var.get())
            )
            success, msg = self.serial.connect(config)
            if success:
                self.connect_btn.config(text=t("btn_disconnect"))
                self.serial_status_label.config(text=t("serial_connected"), foreground="green")
                self.serial.set_callbacks(on_data=self._on_serial_data)
                self.serial.start_listening()
            else:
                messagebox.showerror(t("msg_error"), msg)

    def _on_serial_data(self, data: bytes):
        """串口数据接收回调"""
        hex_str = data.hex().upper()
        formatted = ' '.join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.root.after(0, lambda: self._append_recv(f"[{timestamp}] {formatted}\n"))

    def _append_recv(self, text: str):
        """追加接收数据"""
        self.recv_text.config(state=tk.NORMAL)
        self.recv_text.insert(tk.END, text)
        self.recv_text.see(tk.END)
        self.recv_text.config(state=tk.DISABLED)

    def _clear_recv(self):
        """清空接收区"""
        self.recv_text.config(state=tk.NORMAL)
        self.recv_text.delete(1.0, tk.END)
        self.recv_text.config(state=tk.DISABLED)

    def _send_serial_data(self):
        """发送串口数据"""
        if not self.serial.is_connected():
            messagebox.showwarning(t("msg_warning"), "串口未连接")
            return
        hex_str = self.send_entry.get()
        success, msg = self.serial.send_hex(hex_str)
        if not success:
            messagebox.showerror(t("msg_error"), msg)

    def _convert_selected(self):
        """转换选中的接收数据"""
        try:
            selected = self.recv_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            # 提取十六进制部分
            hex_part = ''.join(c for c in selected if c in '0123456789ABCDEFabcdef ')
            if hex_part:
                self.entry_hex.delete(0, tk.END)
                self.entry_hex.insert(0, hex_part.strip())
                self.notebook.select(0)  # 切换到转换页面
        except tk.TclError:
            messagebox.showwarning(t("msg_warning"), "请先选中要转换的数据")

    # ==================== 批量处理方法 ====================

    def _import_batch_file(self):
        """导入批量文件"""
        filepath = filedialog.askopenfilename(
            title="选择批量报文文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            self.batch_data = []
            for item in self.batch_tree.get_children():
                self.batch_tree.delete(item)

            with open(filepath, 'r', encoding='utf-8') as f:
                if filepath.endswith('.csv'):
                    reader = csv.reader(f)
                    for row in reader:
                        if row:
                            self.batch_data.append({"hex": row[0].strip(), "status": "待转换", "result": "", "crc": ""})
                else:
                    for line in f:
                        hex_str = line.strip()
                        if hex_str:
                            self.batch_data.append({"hex": hex_str, "status": "待转换", "result": "", "crc": ""})

            for idx, data in enumerate(self.batch_data):
                self.batch_tree.insert("", tk.END, iid=idx, values=(data["hex"], data["status"], data["result"], data["crc"]))

            messagebox.showinfo(t("msg_success"), t("msg_import_success", count=len(self.batch_data)))
        except Exception as e:
            messagebox.showerror(t("msg_error"), str(e))
            log.exception(f"批量导入失败: {e}")

    def _batch_convert(self):
        """批量转换"""
        if not self.batch_data:
            messagebox.showwarning(t("msg_warning"), t("msg_no_data"))
            return

        if self.batch_converting:
            return

        if not messagebox.askyesno(t("msg_confirm"), t("msg_convert_confirm", count=len(self.batch_data))):
            return

        self.batch_converting = True
        self.batch_stop_flag = False
        self.batch_convert_btn.config(state=tk.DISABLED)
        self.batch_stop_btn.config(state=tk.NORMAL)
        self.batch_progress['value'] = 0
        self.batch_progress['maximum'] = len(self.batch_data)

        thread = threading.Thread(target=self._batch_convert_thread, daemon=True)
        thread.start()

    def _batch_convert_thread(self):
        """批量转换线程"""
        total = len(self.batch_data)
        success_count = 0
        fail_count = 0
        byte_order = ByteOrder(self.byte_order_var.get())
        data_type = DataType(self.data_type_var.get())

        for idx, data in enumerate(self.batch_data):
            if self.batch_stop_flag:
                break

            hex_str = data["hex"]
            result = ModbusConverter.convert(hex_str, byte_order, data_type)

            if result.success:
                self.batch_data[idx]["status"] = "成功"
                self.batch_data[idx]["result"] = str(result.value)
                self.batch_data[idx]["crc"] = t("crc_pass") if result.parse_result.crc_valid else t("crc_fail")
                success_count += 1
            else:
                self.batch_data[idx]["status"] = "失败"
                self.batch_data[idx]["result"] = result.error_msg
                fail_count += 1

            self.root.after(0, lambda i=idx, d=self.batch_data[idx]:
                self.batch_tree.item(i, values=(d["hex"], d["status"], d["result"], d["crc"])))
            self.root.after(0, lambda i=idx+1: self._update_progress(i, total))

        self.root.after(0, lambda: self._batch_complete(success_count, fail_count))

    def _update_progress(self, current, total):
        """更新进度"""
        self.batch_progress['value'] = current
        self.progress_label.config(text=f"{current}/{total}")

    def _batch_complete(self, success, fail):
        """批量完成"""
        self.batch_converting = False
        self.batch_convert_btn.config(state=tk.NORMAL)
        self.batch_stop_btn.config(state=tk.DISABLED)
        if not self.batch_stop_flag:
            messagebox.showinfo(t("msg_success"), t("msg_convert_complete", success=success, fail=fail))

    def _stop_batch(self):
        """停止批量转换"""
        self.batch_stop_flag = True

    def _clear_batch_list(self):
        """清空批量列表"""
        self.batch_data = []
        for item in self.batch_tree.get_children():
            self.batch_tree.delete(item)
        self.batch_progress['value'] = 0
        self.progress_label.config(text="0/0")

    def _export_batch_result(self):
        """导出批量结果"""
        if not self.batch_data:
            messagebox.showwarning(t("msg_warning"), t("msg_no_data"))
            return

        filepath = filedialog.asksaveasfilename(
            title="保存批量结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not filepath:
            return

        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["原始报文", "状态", "结果", "CRC"])
                for data in self.batch_data:
                    writer.writerow([data["hex"], data["status"], data["result"], data["crc"]])
            messagebox.showinfo(t("msg_success"), t("msg_export_success", path=filepath))
        except Exception as e:
            messagebox.showerror(t("msg_error"), str(e))

    # ==================== 设置方法 ====================

    def _change_theme(self, theme: str):
        """切换主题"""
        ThemeManager.set_theme(theme)
        config_manager.update_config(theme=theme)
        messagebox.showinfo(t("msg_info"), "主题已更改，重启后生效")

    def _change_language(self, lang: str):
        """切换语言"""
        i18n.set_language(lang)
        config_manager.update_config(language=lang)
        messagebox.showinfo(t("msg_info"), "语言已更改，重启后生效")

    def _reset_settings(self):
        """重置设置"""
        config_manager.update_config(
            default_byte_order=2,
            default_data_type="float32",
            theme="light",
            language="zh_CN"
        )
        self.byte_order_var.set(2)
        self.data_type_var.set("float32")
        messagebox.showinfo(t("msg_success"), "设置已重置")

    # ==================== 帮助方法 ====================

    def _show_help(self):
        """显示帮助"""
        help_text = """
Modbus RTU 数据转换工具 V3.0 使用说明

【数据转换】
1. 输入 Modbus RTU 十六进制报文
2. 选择字节序规则和数据类型
3. 点击"单条转换"或按 Ctrl+Enter

【串口通信】
1. 选择串口和参数
2. 点击"连接"
3. 发送/接收数据
4. 选中接收数据后点击"转换选中"

【批量处理】
1. 导入 TXT/CSV 文件（每行一条报文）
2. 点击"批量转换"
3. 导出结果

【快捷键】
Ctrl+Enter / F5 - 执行转换
Ctrl+V - 粘贴并清理格式
Esc - 清空输入
        """
        messagebox.showinfo(t("menu_usage"), help_text)

    def _show_byte_order_help(self):
        """显示字节序帮助"""
        help_text = """
Modbus 浮点数字节序规则说明

以 4 字节数据 A B C D 为例：
A=寄存器1高字节 | B=寄存器1低字节
C=寄存器2高字节 | D=寄存器2低字节

规则1 (B A D C): 部分国产设备
规则2 (C D A B): 西门子/施耐德（推荐）
规则3 (A B C D): 三菱/欧姆龙
规则4 (D C B A): 极少使用

若结果不对，请依次尝试不同规则！
        """
        messagebox.showinfo(t("menu_byte_order"), help_text)

    def _show_shortcuts(self):
        """显示快捷键"""
        help_text = """
快捷键说明

Ctrl + Enter    执行单条转换
F5              执行单条转换
Ctrl + V        粘贴并自动清理格式
Esc             清空输入框
        """
        messagebox.showinfo(t("menu_shortcuts"), help_text)

    def _view_log(self):
        """查看日志"""
        log_dir = "logs"
        if os.path.exists(log_dir):
            os.startfile(log_dir) if os.name == 'nt' else os.system(f'open "{log_dir}"')
        else:
            messagebox.showinfo(t("msg_info"), "暂无日志文件")

    def _show_about(self):
        """显示关于"""
        about_text = f"""
Modbus RTU 数据转换工具

版本: {self.VERSION}
作者: Modbus Converter Team

功能特性:
• 支持多种数据类型转换
• 支持多种字节序规则
• 串口实时通信
• 批量数据处理
• 多语言支持
• 主题切换

© 2024 All Rights Reserved
        """
        messagebox.showinfo(t("menu_about"), about_text)


def main():
    """主函数"""
    root = tk.Tk()
    app = ModbusConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
