"""可折叠框架组件"""
import customtkinter as ctk
from src.gui.themes import COLORS


class CollapsibleFrame(ctk.CTkFrame):
    """可折叠框架"""

    def __init__(self, master, title: str = "", collapsed: bool = False, **kwargs):
        super().__init__(master, fg_color=COLORS["bg_secondary"], corner_radius=8, **kwargs)

        self._collapsed = collapsed

        # 标题栏
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=10, pady=5)

        self.toggle_btn = ctk.CTkButton(
            self.header,
            text="▼" if not collapsed else "▶",
            width=24,
            height=24,
            fg_color="transparent",
            hover_color=COLORS["bg_input"],
            command=self.toggle
        )
        self.toggle_btn.pack(side="left")

        self.title_label = ctk.CTkLabel(
            self.header,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text"]
        )
        self.title_label.pack(side="left", padx=5)

        # 内容区
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        if not collapsed:
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def toggle(self):
        """切换折叠状态"""
        self._collapsed = not self._collapsed
        if self._collapsed:
            self.content_frame.pack_forget()
            self.toggle_btn.configure(text="▶")
        else:
            self.content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.toggle_btn.configure(text="▼")

    def expand(self):
        """展开"""
        if self._collapsed:
            self.toggle()

    def collapse(self):
        """折叠"""
        if not self._collapsed:
            self.toggle()
