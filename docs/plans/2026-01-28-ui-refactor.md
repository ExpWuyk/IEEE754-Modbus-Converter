# UI 重构实现计划 - CustomTkinter 迁移

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将 Modbus 数据转换工具的 Tkinter 界面迁移到 CustomTkinter，实现 VS Code 风格的深色主题。

**Architecture:** 渐进式迁移，保留现有业务逻辑，逐步替换 GUI 组件。先替换根窗口和基础框架，再逐页面重构布局。

**Tech Stack:** Python 3.10+, CustomTkinter 5.2+, 现有 core/utils 模块保持不变

---

## Task 1: 添加 CustomTkinter 依赖

**Files:**
- Modify: `requirements.txt`

**Step 1: 更新 requirements.txt**

在文件末尾添加：
```
customtkinter>=5.2.0
```

**Step 2: 安装依赖**

Run: `pip install customtkinter>=5.2.0`
Expected: Successfully installed customtkinter-5.x.x

**Step 3: 验证安装**

Run: `python -c "import customtkinter; print(customtkinter.__version__)"`
Expected: 5.2.x

**Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add customtkinter dependency"
```

---

## Task 2: 创建主题配置模块

**Files:**
- Rewrite: `src/gui/themes.py`

**Step 1: 重写 themes.py**

```python
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
```

**Step 2: 验证模块可导入**

Run: `python -c "from src.gui.themes import ThemeManager, COLORS; print(COLORS['accent'])"`
Expected: #0078d4

**Step 3: Commit**

```bash
git add src/gui/themes.py
git commit -m "refactor: rewrite themes.py for CustomTkinter"
```

---

## Task 3: 创建基础应用框架

**Files:**
- Create: `src/gui/app_base.py`

**Step 1: 创建基础应用类**

```python
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
```

**Step 2: 验证基础框架**

Run: `python -c "from src.gui.app_base import BaseApp; print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add src/gui/app_base.py
git commit -m "feat: add CustomTkinter base app framework"
```

---

## Task 4: 创建可复用 UI 组件

**Files:**
- Create: `src/gui/components/__init__.py`
- Create: `src/gui/components/card_frame.py`
- Create: `src/gui/components/collapsible_frame.py`

**Step 1: 创建组件包初始化文件**

```python
"""GUI 组件包"""
from .card_frame import CardFrame
from .collapsible_frame import CollapsibleFrame

__all__ = ["CardFrame", "CollapsibleFrame"]
```

**Step 2: 创建卡片框架组件**

```python
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
```

**Step 3: 创建可折叠框架组件**

```python
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
```

**Step 4: 验证组件可导入**

Run: `python -c "from src.gui.components import CardFrame, CollapsibleFrame; print('OK')"`
Expected: OK

**Step 5: Commit**

```bash
git add src/gui/components/
git commit -m "feat: add reusable UI components (CardFrame, CollapsibleFrame)"
```

---

## Task 5: 重构数据转换页面

**Files:**
- Create: `src/gui/pages/__init__.py`
- Create: `src/gui/pages/convert_page.py`

**Step 1: 创建页面包初始化文件**

```python
"""GUI 页面包"""
from .convert_page import ConvertPage

__all__ = ["ConvertPage"]
```

**Step 2: 创建数据转换页面（第一部分 - 输入区和配置区）**

```python
"""数据转换页面"""
import customtkinter as ctk
from tkinter import messagebox
from src.gui.themes import COLORS
from src.gui.components import CardFrame, CollapsibleFrame
from src.core import DataType, ByteOrder
from src.core.converter import ModbusConverter


class ConvertPage(ctk.CTkFrame):
    """数据转换页面"""

    def __init__(self, master, config_manager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.config_manager = config_manager
        self.last_result = ""

        self._init_variables()
        self._create_input_section()
        self._create_config_section()
        self._create_result_section()
        self._create_history_section()

    def _init_variables(self):
        """初始化变量"""
        config = self.config_manager.config
        self.byte_order_var = ctk.IntVar(value=config.default_byte_order)
        self.data_type_var = ctk.StringVar(value=config.default_data_type)
        self.unit_var = ctk.StringVar(value=config.default_unit)

    def _create_input_section(self):
        """创建输入区"""
        input_card = CardFrame(self, title="输入报文")
        input_card.pack(fill="x", padx=10, pady=5)

        # 输入行
        input_row = ctk.CTkFrame(input_card.content_frame, fg_color="transparent")
        input_row.pack(fill="x", pady=5)

        self.entry_hex = ctk.CTkEntry(
            input_row,
            placeholder_text="输入 Modbus RTU 十六进制报文...",
            height=40,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.entry_hex.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

        # 单位选择
        self.unit_combo = ctk.CTkComboBox(
            input_row,
            values=["", "立方米/秒", "米/秒", "米", "台时"],
            variable=self.unit_var,
            width=100,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"]
        )
        self.unit_combo.pack(side="left", padx=(0, 10))

        # 转换按钮
        self.convert_btn = ctk.CTkButton(
            input_row,
            text="转换 (F5)",
            width=100,
            height=40,
            fg_color=COLORS["accent"],
            hover_color="#106ebe",
            command=self._on_convert
        )
        self.convert_btn.pack(side="left")

        # 工具按钮行
        tool_row = ctk.CTkFrame(input_card.content_frame, fg_color="transparent")
        tool_row.pack(fill="x", pady=(5, 0))

        for text, cmd in [("清空", self._clear_input), ("示例", self._insert_example), ("格式化", self._format_hex)]:
            ctk.CTkButton(
                tool_row, text=text, width=60, height=28,
                fg_color="transparent", border_width=1, border_color=COLORS["border"],
                hover_color=COLORS["bg_input"], command=cmd
            ).pack(side="left", padx=(0, 5))

        # 状态标签
        self.input_status = ctk.CTkLabel(
            tool_row, text="", text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(size=11)
        )
        self.input_status.pack(side="right")

        # 绑定输入事件
        self.entry_hex.bind("<KeyRelease>", self._on_input_change)

    def _create_config_section(self):
        """创建配置区"""
        config_card = CardFrame(self, title="转换配置")
        config_card.pack(fill="x", padx=10, pady=5)

        # 数据类型行
        type_row = ctk.CTkFrame(config_card.content_frame, fg_color="transparent")
        type_row.pack(fill="x", pady=5)

        ctk.CTkLabel(type_row, text="数据类型:", text_color=COLORS["text"]).pack(side="left", padx=(0, 10))

        types = [("Float32", "float32"), ("Float64", "float64"), ("Int16", "int16"),
                 ("UInt16", "uint16"), ("Int32", "int32"), ("UInt32", "uint32")]
        for label, value in types:
            ctk.CTkRadioButton(
                type_row, text=label, variable=self.data_type_var, value=value,
                fg_color=COLORS["accent"], hover_color=COLORS["accent"]
            ).pack(side="left", padx=5)

        # 字节序行
        order_row = ctk.CTkFrame(config_card.content_frame, fg_color="transparent")
        order_row.pack(fill="x", pady=5)

        ctk.CTkLabel(order_row, text="字节序:", text_color=COLORS["text"]).pack(side="left", padx=(0, 10))

        orders = [("BADC (规则1)", 1), ("CDAB (规则2)", 2), ("ABCD (规则3)", 3), ("DCBA (规则4)", 4)]
        for label, value in orders:
            ctk.CTkRadioButton(
                order_row, text=label, variable=self.byte_order_var, value=value,
                fg_color=COLORS["accent"], hover_color=COLORS["accent"]
            ).pack(side="left", padx=5)

    def _create_result_section(self):
        """创建结果区 - 左右分栏"""
        result_container = ctk.CTkFrame(self, fg_color="transparent")
        result_container.pack(fill="both", expand=True, padx=10, pady=5)
        result_container.grid_columnconfigure(0, weight=1)
        result_container.grid_columnconfigure(1, weight=1)

        # 左侧：解析结果
        parse_card = CardFrame(result_container, title="报文解析")
        parse_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.parse_labels = {}
        fields = [("slave_addr", "从站地址"), ("func_code", "功能码"),
                  ("data_len", "数据长度"), ("data_hex", "数据内容"),
                  ("input_crc", "报文CRC"), ("calc_crc", "计算CRC"), ("crc_check", "校验结果")]

        for key, label in fields:
            row = ctk.CTkFrame(parse_card.content_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{label}:", width=80, anchor="e",
                        text_color=COLORS["text_secondary"]).pack(side="left")
            lbl = ctk.CTkLabel(row, text="--", text_color=COLORS["text"])
            lbl.pack(side="left", padx=10)
            self.parse_labels[key] = lbl

        # 右侧：转换结果
        value_card = CardFrame(result_container, title="转换结果")
        value_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        self.result_value = ctk.CTkLabel(
            value_card.content_frame,
            text="等待转换...",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text"]
        )
        self.result_value.pack(pady=20)

        self.result_unit = ctk.CTkLabel(
            value_card.content_frame, text="",
            font=ctk.CTkFont(size=14), text_color=COLORS["text_secondary"]
        )
        self.result_unit.pack()

        ctk.CTkButton(
            value_card.content_frame, text="复制结果", width=100,
            fg_color=COLORS["accent"], command=self._copy_result
        ).pack(pady=15)

    def _create_history_section(self):
        """创建历史记录区（可折叠）"""
        self.history_frame = CollapsibleFrame(self, title="历史记录", collapsed=True)
        self.history_frame.pack(fill="x", padx=10, pady=5)

        self.history_list = ctk.CTkTextbox(
            self.history_frame.content_frame, height=100,
            fg_color=COLORS["bg_input"], text_color=COLORS["text"]
        )
        self.history_list.pack(fill="x", pady=5)

    # ========== 事件处理方法 ==========

    def _on_input_change(self, event):
        text = self.entry_hex.get()
        clean = ModbusConverter.clean_hex_string(text)
        self.input_status.configure(text=f"{len(clean)}字符 / {len(clean)//2}字节")

    def _clear_input(self):
        self.entry_hex.delete(0, "end")
        self.input_status.configure(text="")

    def _insert_example(self):
        self.entry_hex.delete(0, "end")
        self.entry_hex.insert(0, "02 03 04 05 1F 42 C9 08 CF")

    def _format_hex(self):
        text = self.entry_hex.get()
        clean = ModbusConverter.clean_hex_string(text)
        self.entry_hex.delete(0, "end")
        self.entry_hex.insert(0, clean)

    def _on_convert(self):
        hex_str = self.entry_hex.get().strip()
        if not hex_str:
            messagebox.showwarning("警告", "请输入报文数据")
            return

        byte_order = ByteOrder(self.byte_order_var.get())
        data_type = DataType(self.data_type_var.get())
        result = ModbusConverter.convert(hex_str, byte_order, data_type)

        if result.success:
            pr = result.parse_result
            self.parse_labels["slave_addr"].configure(text=pr.slave_addr)
            self.parse_labels["func_code"].configure(text=pr.func_code)
            self.parse_labels["data_len"].configure(text=pr.data_len)
            self.parse_labels["data_hex"].configure(text=pr.data_hex)
            self.parse_labels["input_crc"].configure(text=pr.input_crc)
            self.parse_labels["calc_crc"].configure(text=pr.calc_crc)

            crc_text = "✓ 通过" if pr.crc_valid else "✗ 失败"
            crc_color = COLORS["success"] if pr.crc_valid else COLORS["error"]
            self.parse_labels["crc_check"].configure(text=crc_text, text_color=crc_color)

            self.result_value.configure(text=str(result.value), text_color=COLORS["success"])
            self.result_unit.configure(text=self.unit_var.get())
            self.last_result = str(result.value)
        else:
            self.result_value.configure(text="转换失败", text_color=COLORS["error"])
            messagebox.showerror("错误", result.error_msg)

    def _copy_result(self):
        if self.last_result:
            self.clipboard_clear()
            self.clipboard_append(self.last_result)
            messagebox.showinfo("成功", "已复制到剪贴板")
```

**Step 3: Commit**

```bash
git add src/gui/pages/
git commit -m "feat: add ConvertPage with modern UI layout"
```

---

## Task 6: 重构串口通信页面

**Files:**
- Modify: `src/gui/pages/__init__.py`
- Create: `src/gui/pages/serial_page.py`

**Step 1: 更新页面包**

在 `__init__.py` 添加 SerialPage 导入。

**Step 2: 创建串口通信页面**

创建 `serial_page.py`，包含：
- 状态栏（连接状态醒目显示）
- 可折叠配置面板
- 发送/接收区

**Step 3: Commit**

```bash
git add src/gui/pages/
git commit -m "feat: add SerialPage with collapsible config"
```

---

## Task 7: 重构批量处理页面

**Files:**
- Modify: `src/gui/pages/__init__.py`
- Create: `src/gui/pages/batch_page.py`

**Step 1: 更新页面包**

在 `__init__.py` 添加 BatchPage 导入。

**Step 2: 创建批量处理页面**

创建 `batch_page.py`，包含：
- 工具栏按钮
- 进度条
- 数据表格（使用 ttk.Treeview）

**Step 3: Commit**

```bash
git add src/gui/pages/
git commit -m "feat: add BatchPage with progress bar"
```

---

## Task 8: 重写主应用程序

**Files:**
- Rewrite: `src/gui/main_app.py`

**Step 1: 重写 main_app.py**

使用 CTkTabview 整合三个页面，配置快捷键和关闭事件。

**Step 2: 验证**

Run: `python main.py`
Expected: 应用正常启动

**Step 3: Commit**

```bash
git add src/gui/main_app.py
git commit -m "refactor: rewrite main_app.py with CustomTkinter"
```

---

## Task 9: 最终测试与验证

**Step 1: 运行单元测试**

Run: `python -m pytest tests/ -v`
Expected: All tests pass

**Step 2: 功能验证**

- [ ] 数据转换：输入、配置、转换、复制
- [ ] 串口通信：连接、发送、接收
- [ ] 批量处理：导入、转换、导出
- [ ] 快捷键：F5、Esc

**Step 3: 最终提交**

```bash
git add .
git commit -m "feat: complete UI refactor to CustomTkinter v4.0"
```
