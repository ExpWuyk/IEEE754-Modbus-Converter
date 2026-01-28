"""
CustomTkinter 主题配置 - VS Code 深色风格
"""
import customtkinter as ctk

# VS Code 深色主题颜色
COLORS = {
    "bg_dark": "#1e1e1e",
    "bg_secondary": "#252526",
    "bg_input": "#3c3c3c",
    "accent": "#0078d4",
    "success": "#4ec9b0",
    "error": "#f14c4c",
    "warning": "#cca700",
    "text": "#cccccc",
    "text_secondary": "#808080",
    "border": "#3c3c3c",
}


class ThemeManager:
    """主题管理器"""

    @staticmethod
    def setup_theme():
        """配置 CustomTkinter 主题"""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

    @staticmethod
    def get_color(name: str) -> str:
        """获取颜色值"""
        return COLORS.get(name, "#ffffff")
