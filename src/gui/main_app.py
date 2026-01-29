"""Modbus RTU 数据转换工具 V4.0 - CustomTkinter 版本"""
import customtkinter as ctk
from src.gui.themes import ThemeManager, COLORS
from src.gui.pages import ConvertPage, SerialPage, BatchPage
from src.utils.config_manager import config_manager
from src.utils.logger import log


class ModbusConverterApp(ctk.CTk):
    """主应用程序"""

    VERSION = "4.0.0"

    def __init__(self):
        super().__init__()

        ThemeManager.setup_theme()
        self._setup_window()
        self._create_tabview()
        self._bind_shortcuts()

        log.info(f"应用启动 - 版本 {self.VERSION}")

    def _setup_window(self):
        """设置窗口"""
        self.title(f"Modbus 数据转换工具 V{self.VERSION}")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_tabview(self):
        """创建标签页"""
        self.tabview = ctk.CTkTabview(self, fg_color=COLORS["bg_dark"],
                                      segmented_button_fg_color=COLORS["bg_secondary"],
                                      segmented_button_selected_color=COLORS["accent"])
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # 添加页面
        self.tabview.add("数据转换")
        self.tabview.add("串口通信")
        self.tabview.add("批量处理")

        # 创建页面内容
        self.convert_page = ConvertPage(self.tabview.tab("数据转换"), config_manager)
        self.convert_page.pack(fill="both", expand=True)

        self.serial_page = SerialPage(self.tabview.tab("串口通信"))
        self.serial_page.pack(fill="both", expand=True)

        self.batch_page = BatchPage(self.tabview.tab("批量处理"))
        self.batch_page.pack(fill="both", expand=True)

    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.bind("<Control-Return>", lambda e: self.convert_page._on_convert())
        self.bind("<F5>", lambda e: self.convert_page._on_convert())
        self.bind("<Escape>", lambda e: self.convert_page._clear_input())

    def _on_closing(self):
        """关闭事件"""
        if hasattr(self, 'serial_page') and self.serial_page.serial.is_connected():
            self.serial_page.serial.disconnect()
        log.info("应用关闭")
        self.destroy()


def main():
    """主函数"""
    app = ModbusConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
