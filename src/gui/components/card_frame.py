"""卡片框架组件"""
import customtkinter as ctk
from src.gui.themes import COLORS


class CardFrame(ctk.CTkFrame):
    """卡片样式框架"""

    def __init__(self, master, title: str = "", **kwargs):
        super().__init__(
            master,
            fg_color=COLORS["bg_secondary"],
            corner_radius=8,
            **kwargs
        )

        if title:
            self.title_label = ctk.CTkLabel(
                self,
                text=title,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS["text"]
            )
            self.title_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
