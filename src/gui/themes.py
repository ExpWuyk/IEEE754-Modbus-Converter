"""
主题管理模块
"""
from typing import Dict


class ThemeManager:
    """主题管理器"""

    THEMES: Dict[str, Dict[str, str]] = {
        "light": {
            "bg": "#FFFFFF",
            "fg": "#333333",
            "accent": "#0078D4",
            "success": "#28A745",
            "error": "#DC3545",
            "warning": "#FFC107",
            "border": "#E0E0E0",
            "input_bg": "#FFFFFF",
            "button_bg": "#F0F0F0",
            "button_hover": "#E0E0E0",
            "frame_bg": "#F5F5F5",
            "highlight": "#E3F2FD",
        },
        "dark": {
            "bg": "#1E1E1E",
            "fg": "#E0E0E0",
            "accent": "#4FC3F7",
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800",
            "border": "#424242",
            "input_bg": "#2D2D2D",
            "button_bg": "#3D3D3D",
            "button_hover": "#4D4D4D",
            "frame_bg": "#252525",
            "highlight": "#37474F",
        },
        "blue": {
            "bg": "#E3F2FD",
            "fg": "#1565C0",
            "accent": "#1976D2",
            "success": "#43A047",
            "error": "#E53935",
            "warning": "#FB8C00",
            "border": "#90CAF9",
            "input_bg": "#FFFFFF",
            "button_bg": "#BBDEFB",
            "button_hover": "#90CAF9",
            "frame_bg": "#E3F2FD",
            "highlight": "#BBDEFB",
        }
    }

    _current_theme: str = "light"

    @classmethod
    def set_theme(cls, theme_name: str):
        """设置主题"""
        if theme_name in cls.THEMES:
            cls._current_theme = theme_name

    @classmethod
    def get_theme(cls) -> Dict[str, str]:
        """获取当前主题"""
        return cls.THEMES.get(cls._current_theme, cls.THEMES["light"])

    @classmethod
    def get_color(cls, key: str) -> str:
        """获取颜色"""
        return cls.get_theme().get(key, "#000000")

    @classmethod
    def get_available_themes(cls) -> list:
        """获取可用主题列表"""
        return list(cls.THEMES.keys())
