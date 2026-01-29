"""批量处理页面"""
import threading
import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from src.gui.themes import COLORS
from src.gui.components import CardFrame
from src.core import DataType, ByteOrder
from src.core.converter import ModbusConverter


class BatchPage(ctk.CTkFrame):
    """批量处理页面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.data_list = []
        self.is_running = False
        self.stop_flag = False
        self.current_thread = None

        # 默认配置
        self.data_type = DataType.FLOAT32
        self.byte_order = ByteOrder.CDAB

        self._create_toolbar()
        self._create_config_section()
        self._create_progress()
        self._create_table()

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=8)
        toolbar.pack(fill="x", padx=10, pady=5)

        # 导入按钮
        ctk.CTkButton(
            toolbar,
            text="导入文件",
            width=100,
            fg_color=COLORS["accent"],
            hover_color="#106ebe",
            command=self._import_file
        ).pack(side="left", padx=10, pady=10)

        # 开始转换按钮
        self.start_btn = ctk.CTkButton(
            toolbar,
            text="开始转换",
            width=100,
            fg_color=COLORS["success"],
            hover_color="#3da890",
            command=self._start_convert
        )
        self.start_btn.pack(side="left", padx=5, pady=10)

        # 停止按钮
        self.stop_btn = ctk.CTkButton(
            toolbar,
            text="停止",
            width=80,
            fg_color=COLORS["error"],
            hover_color="#d43c3c",
            command=self._stop_convert,
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5, pady=10)

        # 导出按钮
        ctk.CTkButton(
            toolbar,
            text="导出结果",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["bg_input"],
            command=self._export_result
        ).pack(side="left", padx=5, pady=10)

        # 清空按钮
        ctk.CTkButton(
            toolbar,
            text="清空",
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["bg_input"],
            command=self._clear_list
        ).pack(side="left", padx=5, pady=10)

    def _create_config_section(self):
        """创建配置区域"""
        config_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=8)
        config_frame.pack(fill="x", padx=10, pady=5)

        # 数据类型选择
        ctk.CTkLabel(config_frame, text="数据类型:", text_color=COLORS["text"]).pack(side="left", padx=(15, 5), pady=10)
        self.type_combo = ctk.CTkComboBox(
            config_frame,
            values=["float32", "float64", "int16", "uint16", "int32", "uint32"],
            width=100,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            command=self._on_type_change
        )
        self.type_combo.set("float32")
        self.type_combo.pack(side="left", padx=(0, 20), pady=10)

        # 字节序选择
        ctk.CTkLabel(config_frame, text="字节序:", text_color=COLORS["text"]).pack(side="left", padx=(0, 5), pady=10)
        self.order_combo = ctk.CTkComboBox(
            config_frame,
            values=["BADC (规则1)", "CDAB (规则2)", "ABCD (规则3)", "DCBA (规则4)"],
            width=120,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            command=self._on_order_change
        )
        self.order_combo.set("CDAB (规则2)")
        self.order_combo.pack(side="left", pady=10)

    def _create_progress(self):
        """创建进度条区域"""
        progress_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=8)
        progress_frame.pack(fill="x", padx=10, pady=5)

        # 进度标签
        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="就绪",
            text_color=COLORS["text"]
        )
        self.progress_label.pack(side="left", padx=15, pady=10)

        # 进度条
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=400,
            height=15,
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=10)
        self.progress_bar.set(0)

    def _create_table(self):
        """创建数据表格"""
        table_card = CardFrame(self, title="批量数据")
        table_card.pack(fill="both", expand=True, padx=10, pady=5)

        # 创建表格容器
        table_frame = ctk.CTkFrame(table_card.content_frame, fg_color="transparent")
        table_frame.pack(fill="both", expand=True)

        # 配置 Treeview 样式
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Batch.Treeview",
            background=COLORS["bg_input"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["bg_input"],
            rowheight=28
        )
        style.configure(
            "Batch.Treeview.Heading",
            background=COLORS["bg_secondary"],
            foreground=COLORS["text"],
            font=("Microsoft YaHei UI", 10, "bold")
        )
        style.map("Batch.Treeview", background=[("selected", COLORS["accent"])])

        # 创建 Treeview
        columns = ("原始报文", "状态", "结果", "CRC")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Batch.Treeview"
        )

        # 设置列
        self.tree.heading("原始报文", text="原始报文")
        self.tree.heading("状态", text="状态")
        self.tree.heading("结果", text="结果")
        self.tree.heading("CRC", text="CRC")

        self.tree.column("原始报文", width=350, minwidth=200)
        self.tree.column("状态", width=80, minwidth=60, anchor="center")
        self.tree.column("结果", width=150, minwidth=100, anchor="center")
        self.tree.column("CRC", width=100, minwidth=80, anchor="center")

        # 滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ========== 配置变更处理 ==========

    def _on_type_change(self, value: str):
        """数据类型变更"""
        type_map = {
            "float32": DataType.FLOAT32,
            "float64": DataType.FLOAT64,
            "int16": DataType.INT16,
            "uint16": DataType.UINT16,
            "int32": DataType.INT32,
            "uint32": DataType.UINT32,
        }
        self.data_type = type_map.get(value, DataType.FLOAT32)

    def _on_order_change(self, value: str):
        """字节序变更"""
        order_map = {
            "BADC (规则1)": ByteOrder.BADC,
            "CDAB (规则2)": ByteOrder.CDAB,
            "ABCD (规则3)": ByteOrder.ABCD,
            "DCBA (规则4)": ByteOrder.DCBA,
        }
        self.byte_order = order_map.get(value, ByteOrder.CDAB)

    # ========== 事件处理方法 ==========

    def _import_file(self):
        """导入文件"""
        file_path = filedialog.askopenfilename(
            title="选择数据文件",
            filetypes=[("文本文件", "*.txt"), ("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            count = 0
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.data_list.append(line)
                    self.tree.insert("", "end", values=(line, "待处理", "", ""))
                    count += 1

            self.progress_label.configure(text=f"已导入 {count} 条数据")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def _start_convert(self):
        """开始转换"""
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("警告", "请先导入数据")
            return

        self.is_running = True
        self.stop_flag = False
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        # 启动转换线程
        self.current_thread = threading.Thread(target=self._convert_thread, daemon=True)
        self.current_thread.start()

    def _convert_thread(self):
        """转换线程"""
        items = self.tree.get_children()
        total = len(items)

        for i, item in enumerate(items):
            if self.stop_flag:
                break

            values = self.tree.item(item, "values")
            hex_str = values[0]

            # 更新状态为处理中
            self.tree.item(item, values=(hex_str, "处理中", "", ""))

            # 执行转换
            result = ModbusConverter.convert(hex_str, self.byte_order, self.data_type)

            if result.success:
                status = "成功"
                value_str = str(result.value)
                crc_str = "OK" if result.parse_result.crc_valid else "错误"
            else:
                status = "失败"
                value_str = result.error_msg[:20] if result.error_msg else "未知错误"
                crc_str = "-"

            # 更新表格
            self.tree.item(item, values=(hex_str, status, value_str, crc_str))

            # 更新进度
            progress = (i + 1) / total
            self.progress_bar.set(progress)
            self.progress_label.configure(text=f"处理中: {i + 1}/{total}")

        # 完成
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if self.stop_flag:
            self.progress_label.configure(text="已停止")
        else:
            self.progress_label.configure(text=f"完成: 共 {total} 条")

    def _stop_convert(self):
        """停止转换"""
        self.stop_flag = True

    def _export_result(self):
        """导出结果"""
        items = self.tree.get_children()
        if not items:
            messagebox.showwarning("警告", "没有数据可导出")
            return

        file_path = filedialog.asksaveasfilename(
            title="导出结果",
            defaultextension=".csv",
            filetypes=[("CSV文件", "*.csv"), ("文本文件", "*.txt")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("原始报文,状态,结果,CRC\n")
                for item in items:
                    values = self.tree.item(item, "values")
                    f.write(",".join(str(v) for v in values) + "\n")
            messagebox.showinfo("成功", f"已导出到: {file_path}")
        except Exception as e:
            messagebox.showerror("导出失败", str(e))

    def _clear_list(self):
        """清空列表"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.data_list.clear()
        self.progress_bar.set(0)
        self.progress_label.configure(text="就绪")
