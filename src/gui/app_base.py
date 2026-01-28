"""
CustomTkinter 基础应用框架
"""
import customtkinter as ctk
from src.gui.themes import ThemeManager, COLORS


class BaseApp(ctk.CTk):
    """基础应用窗口"""

    def __init__(self, title: str = "Modbus 数据转换工具", width: int = 1100, height: int = 750):
        super().__init__()

        # 配置主题
        ThemeManager.setup_theme()

        # 窗口设置
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(900, 600)

        # 配置颜色
        self.configure(fg_color=COLORS["bg_dark"])

    def run(self):
        """启动应用"""
        self.mainloop()
