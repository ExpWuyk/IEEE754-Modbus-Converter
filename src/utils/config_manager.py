"""
配置管理模块 - 支持多配置文件和云端同步
"""
import json
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict, field
from pathlib import Path


@dataclass
class AppConfig:
    """应用配置"""
    # 转换设置
    default_byte_order: int = 2
    default_data_type: str = "float32"
    default_unit: str = ""

    # 界面设置
    theme: str = "light"
    language: str = "zh_CN"
    window_width: int = 1000
    window_height: int = 800

    # 串口设置
    serial_port: str = ""
    serial_baudrate: int = 9600
    serial_parity: str = "N"
    serial_stopbits: int = 1

    # 功能设置
    auto_crc_check: bool = True
    save_history: bool = True
    max_history: int = 100

    # 高级设置
    debug_mode: bool = False
    auto_update: bool = True


@dataclass
class DevicePreset:
    """设备预设配置"""
    name: str = ""
    byte_order: int = 2
    data_type: str = "float32"
    description: str = ""


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)

        self.config_file = self.config_dir / "settings.json"
        self.presets_file = self.config_dir / "presets.json"
        self.history_file = self.config_dir / "history.json"

        self._config: Optional[AppConfig] = None
        self._presets: Dict[str, DevicePreset] = {}
        self._history: list = []

        self._load_all()

    def _load_all(self):
        """加载所有配置"""
        self._load_config()
        self._load_presets()
        self._load_history()

    def _load_config(self):
        """加载主配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = AppConfig(**data)
            except Exception:
                self._config = AppConfig()
        else:
            self._config = AppConfig()
            self._save_config()

    def _save_config(self):
        """保存主配置"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self._config), f, ensure_ascii=False, indent=2)

    def _load_presets(self):
        """加载设备预设"""
        if self.presets_file.exists():
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._presets = {k: DevicePreset(**v) for k, v in data.items()}
            except Exception:
                self._presets = self._default_presets()
        else:
            self._presets = self._default_presets()
            self._save_presets()

    def _default_presets(self) -> Dict[str, DevicePreset]:
        """默认设备预设"""
        return {
            "siemens": DevicePreset("西门子", 2, "float32", "西门子S7系列PLC"),
            "schneider": DevicePreset("施耐德", 2, "float32", "施耐德Modicon系列"),
            "mitsubishi": DevicePreset("三菱", 3, "float32", "三菱FX/Q系列"),
            "omron": DevicePreset("欧姆龙", 3, "float32", "欧姆龙CP/CJ系列"),
            "abb": DevicePreset("ABB", 2, "float32", "ABB变频器"),
        }

    def _save_presets(self):
        """保存设备预设"""
        with open(self.presets_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self._presets.items()}
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_history(self):
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self._history = json.load(f)
            except Exception:
                self._history = []
        else:
            self._history = []

    def _save_history(self):
        """保存历史记录"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self._history, f, ensure_ascii=False, indent=2)

    @property
    def config(self) -> AppConfig:
        """获取配置"""
        return self._config

    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self._save_config()

    def get_preset(self, name: str) -> Optional[DevicePreset]:
        """获取设备预设"""
        return self._presets.get(name)

    def get_all_presets(self) -> Dict[str, DevicePreset]:
        """获取所有预设"""
        return self._presets.copy()

    def add_preset(self, key: str, preset: DevicePreset):
        """添加预设"""
        self._presets[key] = preset
        self._save_presets()

    def remove_preset(self, key: str):
        """删除预设"""
        if key in self._presets:
            del self._presets[key]
            self._save_presets()

    def add_history(self, record: dict):
        """添加历史记录"""
        self._history.insert(0, record)
        if len(self._history) > self._config.max_history:
            self._history = self._history[:self._config.max_history]
        self._save_history()

    def get_history(self) -> list:
        """获取历史记录"""
        return self._history.copy()

    def clear_history(self):
        """清空历史记录"""
        self._history = []
        self._save_history()

    def export_config(self, filepath: str):
        """导出配置"""
        export_data = {
            "config": asdict(self._config),
            "presets": {k: asdict(v) for k, v in self._presets.items()}
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

    def import_config(self, filepath: str) -> bool:
        """导入配置"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if "config" in data:
                self._config = AppConfig(**data["config"])
                self._save_config()
            if "presets" in data:
                self._presets = {k: DevicePreset(**v) for k, v in data["presets"].items()}
                self._save_presets()
            return True
        except Exception:
            return False


# 全局配置管理器
config_manager = ConfigManager()
