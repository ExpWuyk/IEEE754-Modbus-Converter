"""
国际化模块 - 多语言支持
"""
from typing import Dict, Optional


class I18n:
    """国际化管理器"""

    _instance: Optional['I18n'] = None
    _current_lang: str = "zh_CN"

    # 语言包
    _translations: Dict[str, Dict[str, str]] = {
        "zh_CN": {
            # 窗口标题
            "app_title": "Modbus RTU 数据转换工具",
            "version": "版本",

            # 菜单
            "menu_file": "文件",
            "menu_edit": "编辑",
            "menu_settings": "设置",
            "menu_help": "帮助",
            "menu_import": "导入批量报文",
            "menu_export": "导出批量结果",
            "menu_clear_history": "清空历史记录",
            "menu_exit": "退出",
            "menu_reset": "恢复默认设置",
            "menu_theme": "主题设置",
            "menu_language": "语言",
            "menu_usage": "使用说明",
            "menu_byte_order": "字节序说明",
            "menu_shortcuts": "快捷键",
            "menu_about": "关于",
            "menu_view_log": "查看日志",

            # 输入区域
            "input_title": "单条报文输入",
            "input_label": "Modbus RTU十六进制报文（支持带空格/分隔符）：",
            "input_unit": "单位：",
            "btn_clear": "清空",
            "btn_example": "示例报文",
            "btn_format": "规整格式",

            # 解析区域
            "parse_title": "报文解析",
            "slave_addr": "从机地址",
            "func_code": "功能码",
            "data_len": "数据长度",
            "data_hex": "数据部分",
            "input_crc": "输入CRC",
            "calc_crc": "计算CRC",
            "crc_check": "CRC校验",
            "crc_pass": "通过",
            "crc_fail": "失败",

            # 转换配置
            "convert_title": "转换配置",
            "byte_order": "字节序规则：",
            "data_type": "数据类型：",
            "btn_convert": "单条转换",
            "order_1": "规则1：B A D C",
            "order_2": "规则2：C D A B（推荐）",
            "order_3": "规则3：A B C D",
            "order_4": "规则4：D C B A",

            # 结果区域
            "result_title": "转换结果",
            "result_waiting": "等待转换...",
            "result_success": "转换结果：",
            "result_fail": "转换失败！",
            "btn_copy": "复制结果",

            # 批量处理
            "batch_title": "批量处理",
            "btn_import": "导入TXT/CSV",
            "btn_batch_convert": "批量转换",
            "btn_stop": "停止转换",
            "btn_export": "导出结果",
            "btn_clear_list": "清空列表",
            "col_hex": "原始报文",
            "col_status": "状态",
            "col_result": "转换结果",
            "col_crc": "CRC校验",
            "progress": "转换进度：",

            # 串口通信
            "serial_title": "串口通信",
            "serial_port": "串口：",
            "serial_baudrate": "波特率：",
            "serial_parity": "校验位：",
            "serial_stopbits": "停止位：",
            "btn_connect": "连接",
            "btn_disconnect": "断开",
            "btn_refresh": "刷新",
            "btn_send": "发送",
            "serial_connected": "已连接",
            "serial_disconnected": "未连接",

            # 历史记录
            "history_title": "历史记录",
            "history_select": "选择历史记录：",
            "history_empty": "暂无历史记录",

            # 消息
            "msg_success": "成功",
            "msg_error": "错误",
            "msg_warning": "警告",
            "msg_info": "提示",
            "msg_confirm": "确认",
            "msg_copied": "已复制到剪贴板！",
            "msg_no_result": "暂无可复制的结果！",
            "msg_import_success": "已导入 {count} 条报文！",
            "msg_export_success": "已导出到：{path}",
            "msg_convert_complete": "批量转换完成！\n成功：{success} 条\n失败：{fail} 条",
            "msg_clear_confirm": "是否清空所有记录？",
            "msg_convert_confirm": "是否转换当前 {count} 条报文？",
            "msg_input_empty": "请输入Modbus十六进制报文！",
            "msg_no_data": "暂无数据！",

            # 单位
            "unit_none": "",
            "unit_m3s": "立方米/秒",
            "unit_ms": "米/秒",
            "unit_m": "米",
            "unit_hour": "台时",
            "unit_custom": "自定义",
        },

        "en_US": {
            "app_title": "Modbus RTU Data Converter",
            "version": "Version",
            "menu_file": "File",
            "menu_edit": "Edit",
            "menu_settings": "Settings",
            "menu_help": "Help",
            "menu_import": "Import Batch",
            "menu_export": "Export Results",
            "menu_clear_history": "Clear History",
            "menu_exit": "Exit",
            "menu_reset": "Reset Settings",
            "menu_theme": "Theme",
            "menu_language": "Language",
            "menu_usage": "User Guide",
            "menu_byte_order": "Byte Order",
            "menu_shortcuts": "Shortcuts",
            "menu_about": "About",
            "menu_view_log": "View Log",
            "input_title": "Single Packet Input",
            "input_label": "Modbus RTU Hex Packet (spaces/separators allowed):",
            "input_unit": "Unit:",
            "btn_clear": "Clear",
            "btn_example": "Example",
            "btn_format": "Format",
            "parse_title": "Packet Parse",
            "slave_addr": "Slave Address",
            "func_code": "Function Code",
            "data_len": "Data Length",
            "data_hex": "Data Hex",
            "input_crc": "Input CRC",
            "calc_crc": "Calc CRC",
            "crc_check": "CRC Check",
            "crc_pass": "Pass",
            "crc_fail": "Fail",
            "convert_title": "Convert Settings",
            "byte_order": "Byte Order:",
            "data_type": "Data Type:",
            "btn_convert": "Convert",
            "order_1": "Rule 1: B A D C",
            "order_2": "Rule 2: C D A B (Recommended)",
            "order_3": "Rule 3: A B C D",
            "order_4": "Rule 4: D C B A",
            "result_title": "Result",
            "result_waiting": "Waiting...",
            "result_success": "Result:",
            "result_fail": "Convert Failed!",
            "btn_copy": "Copy",
            "batch_title": "Batch Processing",
            "btn_import": "Import",
            "btn_batch_convert": "Batch Convert",
            "btn_stop": "Stop",
            "btn_export": "Export",
            "btn_clear_list": "Clear List",
            "col_hex": "Hex Packet",
            "col_status": "Status",
            "col_result": "Result",
            "col_crc": "CRC",
            "progress": "Progress:",
            "serial_title": "Serial Communication",
            "serial_port": "Port:",
            "serial_baudrate": "Baudrate:",
            "serial_parity": "Parity:",
            "serial_stopbits": "Stop Bits:",
            "btn_connect": "Connect",
            "btn_disconnect": "Disconnect",
            "btn_refresh": "Refresh",
            "btn_send": "Send",
            "serial_connected": "Connected",
            "serial_disconnected": "Disconnected",
            "history_title": "History",
            "history_select": "Select History:",
            "history_empty": "No History",
            "msg_success": "Success",
            "msg_error": "Error",
            "msg_warning": "Warning",
            "msg_info": "Info",
            "msg_confirm": "Confirm",
            "msg_copied": "Copied to clipboard!",
            "msg_no_result": "No result to copy!",
            "msg_import_success": "Imported {count} packets!",
            "msg_export_success": "Exported to: {path}",
            "msg_convert_complete": "Batch complete!\nSuccess: {success}\nFailed: {fail}",
            "msg_clear_confirm": "Clear all records?",
            "msg_convert_confirm": "Convert {count} packets?",
            "msg_input_empty": "Please enter Modbus hex packet!",
            "msg_no_data": "No data!",
            "unit_none": "",
            "unit_m3s": "m³/s",
            "unit_ms": "m/s",
            "unit_m": "m",
            "unit_hour": "hours",
            "unit_custom": "Custom",
        }
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_language(self, lang: str):
        """设置语言"""
        if lang in self._translations:
            self._current_lang = lang

    def get_language(self) -> str:
        """获取当前语言"""
        return self._current_lang

    def get_available_languages(self) -> list:
        """获取可用语言列表"""
        return list(self._translations.keys())

    def t(self, key: str, **kwargs) -> str:
        """获取翻译文本"""
        text = self._translations.get(self._current_lang, {}).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except KeyError:
                pass
        return text

    def __call__(self, key: str, **kwargs) -> str:
        """快捷调用"""
        return self.t(key, **kwargs)


# 全局国际化实例
i18n = I18n()
t = i18n.t  # 快捷函数
