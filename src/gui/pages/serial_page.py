"""串口通信页面"""
import customtkinter as ctk
from tkinter import messagebox
from src.gui.themes import COLORS
from src.gui.components import CardFrame, CollapsibleFrame
from src.core.serial_comm import SerialCommunicator, SerialConfig


class SerialPage(ctk.CTkFrame):
    """串口通信页面"""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.serial = SerialCommunicator()
        self.serial.set_callbacks(on_data=self._on_recv, on_error=self._on_error)

        self._create_status_bar()
        self._create_config_section()
        self._create_send_section()
        self._create_recv_section()

    def _create_status_bar(self):
        """创建状态栏"""
        status_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_secondary"], corner_radius=8)
        status_frame.pack(fill="x", padx=10, pady=5)

        # 连接状态指示器
        self.status_indicator = ctk.CTkLabel(
            status_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color=COLORS["error"]
        )
        self.status_indicator.pack(side="left", padx=(15, 5), pady=10)

        # 状态文本
        self.status_text = ctk.CTkLabel(
            status_frame,
            text="未连接",
            text_color=COLORS["text"]
        )
        self.status_text.pack(side="left", padx=5, pady=10)

        # 断开按钮
        self.disconnect_btn = ctk.CTkButton(
            status_frame,
            text="断开连接",
            width=100,
            fg_color=COLORS["error"],
            hover_color="#d43c3c",
            command=self._disconnect,
            state="disabled"
        )
        self.disconnect_btn.pack(side="right", padx=15, pady=10)

    def _create_config_section(self):
        """创建可折叠配置面板"""
        self.config_frame = CollapsibleFrame(self, title="串口配置", collapsed=False)
        self.config_frame.pack(fill="x", padx=10, pady=5)

        content = self.config_frame.content_frame

        # 第一行：端口和波特率
        row1 = ctk.CTkFrame(content, fg_color="transparent")
        row1.pack(fill="x", pady=5)

        # 端口选择
        ctk.CTkLabel(row1, text="端口:", text_color=COLORS["text"]).pack(side="left", padx=(0, 5))
        self.port_combo = ctk.CTkComboBox(
            row1,
            values=[],
            width=120,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.port_combo.pack(side="left", padx=(0, 10))

        # 刷新按钮
        ctk.CTkButton(
            row1,
            text="刷新",
            width=60,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["bg_input"],
            command=self._refresh_ports
        ).pack(side="left", padx=(0, 20))

        # 波特率
        ctk.CTkLabel(row1, text="波特率:", text_color=COLORS["text"]).pack(side="left", padx=(0, 5))
        self.baudrate_combo = ctk.CTkComboBox(
            row1,
            values=["9600", "19200", "38400", "57600", "115200"],
            width=100,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.baudrate_combo.set("9600")
        self.baudrate_combo.pack(side="left")

        # 第二行：校验和停止位
        row2 = ctk.CTkFrame(content, fg_color="transparent")
        row2.pack(fill="x", pady=5)

        # 校验位
        ctk.CTkLabel(row2, text="校验:", text_color=COLORS["text"]).pack(side="left", padx=(0, 5))
        self.parity_combo = ctk.CTkComboBox(
            row2,
            values=["无 (N)", "偶校验 (E)", "奇校验 (O)"],
            width=100,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.parity_combo.set("无 (N)")
        self.parity_combo.pack(side="left", padx=(0, 20))

        # 停止位
        ctk.CTkLabel(row2, text="停止位:", text_color=COLORS["text"]).pack(side="left", padx=(0, 5))
        self.stopbits_combo = ctk.CTkComboBox(
            row2,
            values=["1", "2"],
            width=80,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.stopbits_combo.set("1")
        self.stopbits_combo.pack(side="left", padx=(0, 20))

        # 连接按钮
        self.connect_btn = ctk.CTkButton(
            row2,
            text="连接",
            width=100,
            fg_color=COLORS["accent"],
            hover_color="#106ebe",
            command=self._connect
        )
        self.connect_btn.pack(side="right")

        # 初始刷新端口
        self._refresh_ports()

    def _create_send_section(self):
        """创建发送区"""
        send_card = CardFrame(self, title="发送数据")
        send_card.pack(fill="x", padx=10, pady=5)

        send_row = ctk.CTkFrame(send_card.content_frame, fg_color="transparent")
        send_row.pack(fill="x", pady=5)

        # 发送输入框
        self.send_entry = ctk.CTkEntry(
            send_row,
            placeholder_text="输入十六进制数据 (如: 01 03 00 00 00 02)",
            height=40,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.send_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # 发送按钮
        self.send_btn = ctk.CTkButton(
            send_row,
            text="发送",
            width=100,
            height=40,
            fg_color=COLORS["accent"],
            hover_color="#106ebe",
            command=self._send_data,
            state="disabled"
        )
        self.send_btn.pack(side="left")

    def _create_recv_section(self):
        """创建接收区"""
        recv_card = CardFrame(self, title="接收数据")
        recv_card.pack(fill="both", expand=True, padx=10, pady=5)

        # 接收文本框
        self.recv_text = ctk.CTkTextbox(
            recv_card.content_frame,
            height=200,
            font=ctk.CTkFont(family="Consolas", size=12),
            fg_color=COLORS["bg_input"],
            text_color=COLORS["text"]
        )
        self.recv_text.pack(fill="both", expand=True, pady=(0, 5))

        # 清空按钮
        ctk.CTkButton(
            recv_card.content_frame,
            text="清空",
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            hover_color=COLORS["bg_input"],
            command=self._clear_recv
        ).pack(anchor="e")

    # ========== 事件处理方法 ==========

    def _refresh_ports(self):
        """刷新可用端口列表"""
        ports = SerialCommunicator.list_ports()
        self.port_combo.configure(values=ports if ports else ["无可用端口"])
        if ports:
            self.port_combo.set(ports[0])
        else:
            self.port_combo.set("无可用端口")

    def _connect(self):
        """连接串口"""
        port = self.port_combo.get()
        if not port or port == "无可用端口":
            messagebox.showwarning("警告", "请选择有效的串口")
            return

        # 解析校验位
        parity_map = {"无 (N)": "N", "偶校验 (E)": "E", "奇校验 (O)": "O"}
        parity = parity_map.get(self.parity_combo.get(), "N")

        config = SerialConfig(
            port=port,
            baudrate=int(self.baudrate_combo.get()),
            parity=parity,
            stopbits=int(self.stopbits_combo.get())
        )

        success, msg = self.serial.connect(config)
        if success:
            self.serial.start_listening()
            self._update_ui_connected(True)
            self.status_text.configure(text=f"已连接: {port}")
        else:
            messagebox.showerror("连接失败", msg)

    def _disconnect(self):
        """断开连接"""
        self.serial.disconnect()
        self._update_ui_connected(False)
        self.status_text.configure(text="未连接")

    def _update_ui_connected(self, connected: bool):
        """更新 UI 连接状态"""
        if connected:
            self.status_indicator.configure(text_color=COLORS["success"])
            self.connect_btn.configure(state="disabled")
            self.disconnect_btn.configure(state="normal")
            self.send_btn.configure(state="normal")
        else:
            self.status_indicator.configure(text_color=COLORS["error"])
            self.connect_btn.configure(state="normal")
            self.disconnect_btn.configure(state="disabled")
            self.send_btn.configure(state="disabled")

    def _send_data(self):
        """发送数据"""
        hex_str = self.send_entry.get().strip()
        if not hex_str:
            messagebox.showwarning("警告", "请输入要发送的数据")
            return

        success, msg = self.serial.send_hex(hex_str)
        if not success:
            messagebox.showerror("发送失败", msg)

    def _on_recv(self, data: bytes):
        """接收数据回调"""
        hex_str = data.hex().upper()
        formatted = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
        self.recv_text.insert("end", f"[RX] {formatted}\n")
        self.recv_text.see("end")

    def _on_error(self, error: str):
        """错误回调"""
        self.recv_text.insert("end", f"[ERR] {error}\n")
        self.recv_text.see("end")

    def _clear_recv(self):
        """清空接收区"""
        self.recv_text.delete("1.0", "end")
