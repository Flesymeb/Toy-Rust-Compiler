"""
Description  : Rust-like语言编译器GUI界面 (左右布局与树形AST)
Author       : Hyoung
Date         : 2025-08-19 17:50:09
LastEditTime : 2025-08-20 16:56:11
FilePath     : \\课程设计\\rust-like-compiler\\gui_final.py
"""

import sys
import os
import warnings

# 过滤PyQt5的警告信息
warnings.filterwarnings("ignore", category=DeprecationWarning, module="PyQt5.*")

# 添加当前目录到模块搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 添加PyQt5的DLL路径到系统路径中
pyqt_path = None
for path in sys.path:
    if "site-packages" in path and os.path.exists(os.path.join(path, "PyQt5")):
        pyqt_path = os.path.join(path, "PyQt5", "Qt5", "bin")
        if os.path.exists(pyqt_path):
            os.environ["PATH"] = pyqt_path + os.pathsep + os.environ["PATH"]
            print(f"Added PyQt5 DLL path: {pyqt_path}")

            # 设置Qt插件路径
            plugins_path = os.path.join(os.path.dirname(pyqt_path), "plugins")
            if os.path.exists(plugins_path):
                os.environ["QT_PLUGIN_PATH"] = plugins_path
                print(f"Added Qt plugin path: {plugins_path}")
            break

# 如果没有找到，尝试从conda环境中找
if not pyqt_path:
    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        pyqt_path = os.path.join(conda_prefix, "Library", "bin")
        if os.path.exists(pyqt_path):
            os.environ["PATH"] = pyqt_path + os.pathsep + os.environ["PATH"]
            print(f"Added Conda Library bin path: {pyqt_path}")

            # 设置Qt插件路径
            plugins_path = os.path.join(conda_prefix, "Library", "plugins")
            if os.path.exists(plugins_path):
                os.environ["QT_PLUGIN_PATH"] = plugins_path
                print(f"Added Qt plugin path: {plugins_path}")

try:
    from PyQt5.QtGui import QTextOption
    from PyQt5.QtWidgets import (
        QHeaderView,
        QApplication,
        QMainWindow,
        QMessageBox,
        QWidget,
        QTableWidgetItem,
        QFileDialog,
        QSplitter,
        QTabWidget,
        QVBoxLayout,
        QHBoxLayout,
        QPushButton,
        QTextEdit,
        QTableWidget,
        QLabel,
        QStyleFactory,
        QTreeWidget,
        QTreeWidgetItem,
        QFrame,
        QPlainTextEdit,
        QStatusBar,
    )
    from PyQt5.QtGui import (
        QColor,
        QPalette,
        QSyntaxHighlighter,
        QTextCharFormat,
        QFont,
        QTextCursor,
        QTextFormat,
        QPainter,
    )
    from PyQt5.QtCore import (
        Qt,
        QRegularExpression,
        QRect,
        QSize,
    )
except ImportError as e:
    print(f"PyQt5导入错误: {e}")
    print("当前Python路径:", sys.path)
    print("当前环境变量PATH:", os.environ.get("PATH"))
    sys.exit(1)

# 导入编译器相关模块
try:
    # 使用相对导入
    from lexer import Lexer

    # 明确使用本地的parser模块，避免与标准库冲突
    sys.modules.pop("parser", None)  # 移除可能已导入的标准库parser模块
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "myparser", os.path.join(current_dir, "parser.py")
    )
    myparser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(myparser)

    from ir_generator import IRGenerator
    from codegen2mips import MIPSCodeGenerator
    from parser_nodes import ASTNode  # 导入ASTNode基类
    from semantic_analyzer import SemanticAnalyzer  # 导入语义分析器

    print("编译器模块导入成功")
except ImportError as e:
    print(f"编译器模块导入错误: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"其他错误: {e}")
    import traceback

    traceback.print_exc()


def get_best_font_family():
    """获取最佳的中文字体组合"""
    # 代码编辑器用的等宽字体，支持中文
    code_fonts = [
        "JetBrains Mono",  # 现代编程字体
        "Fira Code",  # 支持连字的编程字体
        "Source Code Pro",  # Adobe开源编程字体
        "Consolas",  # Windows默认编程字体
        "Monaco",  # macOS默认编程字体
        "Menlo",  # macOS系统字体
        "DejaVu Sans Mono",  # Linux常用编程字体
        "monospace",  # 通用等宽字体
    ]

    # UI用的非等宽字体，优化中文显示
    ui_fonts = [
        "Microsoft YaHei UI",  # 微软雅黑UI版本（更现代）
        "Microsoft YaHei",  # 微软雅黑
        "PingFang SC",  # 苹果苹方字体
        "Hiragino Sans GB",  # 冬青黑体
        "Source Han Sans SC",  # 思源黑体
        "Noto Sans CJK SC",  # Google Noto字体
        "WenQuanYi Micro Hei",  # 文泉驿微米黑
        "SimHei",  # 黑体
        "Arial Unicode MS",  # 支持Unicode的Arial
        "sans-serif",  # 通用无衬线字体
    ]

    return code_fonts, ui_fonts


def setup_application_font(app):
    """设置应用程序全局字体"""
    _, ui_fonts = get_best_font_family()

    # 设置默认字体
    font = QFont()
    font.setFamily(", ".join(ui_fonts[:3]))  # 使用前三个字体作为fallback
    font.setPointSize(10)  # 增加字体大小以提高清晰度
    font.setHintingPreference(QFont.PreferFullHinting)  # 改善字体渲染
    font.setStyleStrategy(QFont.PreferAntialias)  # 启用抗锯齿

    app.setFont(font)
    return font
    sys.exit(1)


# 代码编辑器行号区域
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.editor.lineNumberAreaPaintEvent(event)


# 带行号的代码编辑器
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lineNumberArea = LineNumberArea(self)

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        # 设置字体
        code_fonts, _ = get_best_font_family()
        font = QFont()
        font.setFamily(", ".join(code_fonts[:3]))  # 使用前三个编程字体
        font.setPointSize(12)  # 增加代码字体大小，提高可读性
        font.setHintingPreference(QFont.PreferFullHinting)
        font.setStyleStrategy(QFont.PreferAntialias)  # 启用抗锯齿
        self.setFont(font)

        # 设置制表符宽度
        self.setTabStopWidth(4 * self.fontMetrics().width(" "))

        # 设置滚动行为
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)  # 禁用自动换行
        self.setWordWrapMode(QTextOption.NoWrap)  # 禁用词换行

    def lineNumberAreaWidth(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1

        space = 3 + self.fontMetrics().width("9") * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(
                0, rect.y(), self.lineNumberArea.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(
            QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height())
        )

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QColor(40, 42, 54))  # 行号区域背景色

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                painter.setPen(QColor(150, 150, 150))  # 行号颜色
                painter.drawText(
                    0,
                    int(top),  # 确保是整数
                    self.lineNumberArea.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            lineColor = QColor(
                80, 80, 100, 80
            )  # 更深的蓝灰色，半透明，更容易看清白色文字

            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)


# Rust语法高亮器
class RustHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 关键字格式
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "fn",
            "let",
            "mut",
            "if",
            "else",
            "while",
            "for",
            "in",
            "return",
            "break",
            "continue",
            "struct",
            "enum",
            "match",
            "pub",
            "impl",
            "use",
            "mod",
            "as",
            "const",
            "static",
            "trait",
            "where",
            "type",
            "unsafe",
            "true",
            "false",
        ]
        for word in keywords:
            pattern = QRegularExpression(r"\b" + word + r"\b")
            rule = (pattern, keyword_format)
            self.highlighting_rules.append(rule)

        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#bd93f9"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[0-9]+\b"), number_format)
        )

        # 字符串格式
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        self.highlighting_rules.append((QRegularExpression(r"//.*"), comment_format))

        # 函数调用格式
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#50fa7b"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[A-Za-z0-9_]+(?=\()"), function_format)
        )

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


# MIPS汇编高亮器
class MIPSHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # 指令格式
        instruction_format = QTextCharFormat()
        instruction_format.setForeground(QColor("#ff79c6"))
        instruction_format.setFontWeight(QFont.Bold)
        instructions = [
            "add",
            "addi",
            "sub",
            "mult",
            "div",
            "mflo",
            "mfhi",
            "and",
            "andi",
            "or",
            "ori",
            "xor",
            "xori",
            "nor",
            "sll",
            "srl",
            "sra",
            "sllv",
            "srlv",
            "srav",
            "slt",
            "slti",
            "sltu",
            "sltiu",
            "beq",
            "bne",
            "bgtz",
            "bgez",
            "bltz",
            "blez",
            "j",
            "jal",
            "jr",
            "jalr",
            "lb",
            "lbu",
            "lh",
            "lhu",
            "lw",
            "sb",
            "sh",
            "sw",
            "lui",
            "la",
            "li",
            "move",
            "syscall",
        ]
        for instr in instructions:
            pattern = QRegularExpression(r"\b" + instr + r"\b")
            rule = (pattern, instruction_format)
            self.highlighting_rules.append(rule)

        # 寄存器格式
        register_format = QTextCharFormat()
        register_format.setForeground(QColor("#50fa7b"))
        register_pattern = QRegularExpression(
            r"\$(zero|at|v[0-1]|a[0-3]|t[0-9]|s[0-7]|k[0-1]|gp|sp|fp|ra|[0-9]+)"
        )
        self.highlighting_rules.append((register_pattern, register_format))

        # 数字格式
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#bd93f9"))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[0-9]+\b"), number_format)
        )

        # 标签格式
        label_format = QTextCharFormat()
        label_format.setForeground(QColor("#f1fa8c"))
        self.highlighting_rules.append(
            (QRegularExpression(r"[a-zA-Z0-9_]+:"), label_format)
        )

        # 注释格式
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        self.highlighting_rules.append((QRegularExpression(r"#.*"), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


# 应用一体化暗色主题
def apply_modern_theme(app):
    """应用现代化一体化主题"""
    app.setStyle(QStyleFactory.create("Fusion"))

    # 设置现代化调色板
    dark_palette = QPalette()
    # 主要背景色 - 深灰蓝色
    dark_palette.setColor(QPalette.Window, QColor(32, 34, 42))
    dark_palette.setColor(QPalette.WindowText, QColor(248, 248, 242))

    # 输入框和编辑区域
    dark_palette.setColor(QPalette.Base, QColor(24, 26, 32))
    dark_palette.setColor(QPalette.AlternateBase, QColor(40, 42, 54))

    # 工具提示
    dark_palette.setColor(QPalette.ToolTipBase, QColor(40, 42, 54))
    dark_palette.setColor(QPalette.ToolTipText, QColor(248, 248, 242))

    # 文本
    dark_palette.setColor(QPalette.Text, QColor(248, 248, 242))

    # 按钮
    dark_palette.setColor(QPalette.Button, QColor(45, 47, 58))
    dark_palette.setColor(QPalette.ButtonText, QColor(248, 248, 242))

    # 高亮
    dark_palette.setColor(QPalette.BrightText, QColor(255, 85, 85))
    dark_palette.setColor(QPalette.Link, QColor(102, 217, 239))
    dark_palette.setColor(QPalette.Highlight, QColor(68, 71, 90))
    dark_palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))

    app.setPalette(dark_palette)

    # 现代化全局样式
    app.setStyleSheet(
        """
        /* 全局样式 */
        QMainWindow {
            background-color: #202228;
            color: #f8f8f2;
            border: 1px solid #363944;
        }
        
        /* 工具提示 */
        QToolTip { 
            color: #f8f8f2; 
            background-color: #363944;
            border: 1px solid #4a9eff;
            border-radius: 6px;
            padding: 8px;
            font-size: 12px;  /* 增加工具提示字体大小 */
        }
        
        /* 表格样式 */
        QTableWidget {
            background-color: #181b20;
            gridline-color: #363944;
            selection-background-color: #4a9eff;
            selection-color: #ffffff;
            border: 1px solid #363944;
            border-radius: 8px;
            font-size: 13px;  /* 增大表格字体 */
        }
        
        QTableWidget::item {
            padding: 8px;
            border-bottom: 1px solid #2d3038;
        }
        
        QTableWidget::item:selected {
            background-color: #4a9eff;
            color: #ffffff;
        }
        
        QTableWidget::item:hover {
            background-color: #363944;
        }
        
        /* 表头样式 */
        QHeaderView::section {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #4a4c58, stop: 1 #363944);
            color: #f8f8f2;
            padding: 10px;
            border: none;
            border-right: 1px solid #2d3038;
            border-bottom: 2px solid #4a9eff;
            font-weight: bold;
            font-size: 12px;  /* 增加字体大小 */
        }
        
        QHeaderView::section:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5c68, stop: 1 #464854);
        }
        
        /* 标签页样式 */
        QTabBar::tab {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #363944, stop: 1 #2d3038);
            border: 1px solid #2d3038;  /* 使用更暗的边框色 */
            border-bottom: none;  /* 移除底部边框 */
            padding: 12px 20px;
            margin-right: 0px;  /* 移除间距，消除白线 */
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            color: #a0a2a8;
            font-weight: 500;
            min-width: 80px;
        }
        
        QTabBar::tab:selected {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #4a9eff, stop: 1 #2563eb);
            color: #ffffff;
            border: 1px solid #2563eb;  /* 选中状态的边框 */
            border-bottom: none;
            font-weight: bold;
        }
        
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #464854, stop: 1 #3d3f4a);
            color: #f8f8f2;
            border: 1px solid #3d3f4a;  /* 悬停状态的边框 */
            border-bottom: none;
        }
        
        QTabWidget::pane {
            border: 1px solid #2d3038;  /* 使用更暗的边框色与选项卡匹配 */
            border-radius: 8px;
            background-color: #181b20;
            margin-top: -1px;  /* 确保与选项卡无缝连接 */
            border-top-left-radius: 0px;  /* 左上角不圆角，与选中选项卡连接 */
        }
        
        /* 分割器样式 */
        QSplitter::handle {
            background-color: #363944;
            border: 1px solid #4a4c58;
            border-radius: 3px;
        }
        
        QSplitter::handle:horizontal {
            width: 6px;
            margin: 2px 0;
        }
        
        QSplitter::handle:vertical {
            height: 6px;
            margin: 0 2px;
        }
        
        QSplitter::handle:hover {
            background-color: #4a9eff;
        }
        
        /* 滚动条样式 */
        QScrollBar:vertical {
            border: none;
            background: #2d3038;
            width: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:vertical {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #4a4c58, stop: 1 #363944);
            min-height: 20px;
            border-radius: 6px;
            border: 1px solid #2d3038;
        }
        
        QScrollBar::handle:vertical:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                       stop: 0 #4a9eff, stop: 1 #2563eb);
        }
        
        QScrollBar:horizontal {
            border: none;
            background: #2d3038;
            height: 12px;
            border-radius: 6px;
            margin: 0;
        }
        
        QScrollBar::handle:horizontal {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #4a4c58, stop: 1 #363944);
            min-width: 20px;
            border-radius: 6px;
            border: 1px solid #2d3038;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #4a9eff, stop: 1 #2563eb);
        }
        
        QScrollBar::add-line, QScrollBar::sub-line {
            border: none;
            background: none;
        }
        
        /* 按钮现代化样式 */
        QPushButton {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #4a4c58, stop: 1 #363944);
            border: 1px solid #4a4c58;
            border-radius: 8px;
            color: #f8f8f2;
            font-weight: 500;
            padding: 10px 16px;
            font-size: 12px;  /* 增加按钮字体大小 */
            min-width: 80px;
        }
        
        QPushButton:hover {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #5a5c68, stop: 1 #464854);
            border: 1px solid #4a9eff;
            color: #ffffff;
        }
        
        QPushButton:pressed {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                       stop: 0 #2d3038, stop: 1 #363944);
            border: 1px solid #2563eb;
        }
        
        QPushButton:disabled {
            background: #2d3038;
            border: 1px solid #2d3038;
            color: #6c6c6c;
        }
        
        /* 标签样式 */
        QLabel {
            color: #f8f8f2;
            font-size: 11px;  /* 标签字体调回合适大小 */
        }
        
        /* 文本编辑器增强 */
        QTextEdit, QPlainTextEdit {
            background-color: #181b20;
            border: 1px solid #363944;
            border-radius: 8px;
            color: #f8f8f2;
            selection-background-color: #4a9eff;
            selection-color: #ffffff;
            padding: 8px;
        }
        
        QTextEdit:focus, QPlainTextEdit:focus {
            border: 2px solid #4a9eff;
        }
    """
    )


# 自定义标题栏类
class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.initUI()

    def initUI(self):
        self.setFixedHeight(40)
        self.setStyleSheet(
            """
            CustomTitleBar {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #363944, stop: 1 #2d3038);
                border-bottom: 1px solid #4a9eff;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 10, 0)
        layout.setSpacing(0)

        # 应用图标和标题
        icon_label = QLabel("🦀")  # Rust图标
        icon_label.setStyleSheet("font-size: 18px; margin-right: 8px;")

        title_label = QLabel("Toy Rust Compiler")
        title_label.setStyleSheet(
            """
            font-size: 14px;
            font-weight: bold;
            color: #f8f8f2;
            margin: 0;
        """
        )

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addStretch()

        # 窗口控制按钮
        self.minimize_btn = QPushButton("−")
        self.maximize_btn = QPushButton("□")
        self.close_btn = QPushButton("×")

        button_style = """
            QPushButton {
                background: transparent;
                border: none;
                color: #f8f8f2;
                font-size: 16px;
                font-weight: bold;
                width: 35px;
                height: 35px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """

        close_button_style = (
            button_style
            + """
            QPushButton:hover {
                background-color: #e74c3c;
                color: #ffffff;
            }
        """
        )

        self.minimize_btn.setStyleSheet(button_style)
        self.maximize_btn.setStyleSheet(button_style)
        self.close_btn.setStyleSheet(close_button_style)

        # 连接信号
        self.minimize_btn.clicked.connect(self.parent.showMinimized)
        self.maximize_btn.clicked.connect(self.toggleMaximize)
        self.close_btn.clicked.connect(self.parent.close)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)

    def toggleMaximize(self):
        if self.parent.isMaximized():
            self.parent.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.parent.showMaximized()
            self.maximize_btn.setText("❐")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.drag_position = (
                event.globalPos() - self.parent.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self.parent, "drag_position"):
            self.parent.move(event.globalPos() - self.parent.drag_position)
            event.accept()


# 格式化AST为文本格式
def format_ast(node, indent=0):
    if node is None:
        return ""

    result = " " * indent + f"{node.__class__.__name__}"

    # 收集非列表类型的属性用于显示
    attrs = {}
    for key, value in node.__dict__.items():
        if not isinstance(value, list) and not key.startswith("_"):
            attrs[key] = value

    if attrs:
        result += ": " + ", ".join(f"{k}={v}" for k, v in attrs.items())

    result += "\n"

    # 检查不同类型的子节点属性
    children = []
    if hasattr(node, "declarations"):
        children = node.declarations
    elif hasattr(node, "statements"):
        children = node.statements
    elif hasattr(node, "children"):
        children = node.children
    elif hasattr(node, "params") and node.params:
        children.extend(node.params)
    elif hasattr(node, "body") and node.body:
        children = [node.body]
    elif hasattr(node, "then_block") and node.then_block:
        children = [node.condition, node.then_block]
        if node.else_block:
            children.append(node.else_block)
    elif hasattr(node, "expr") and node.expr:
        children = [node.expr]
    elif hasattr(node, "left") and node.left:
        children = [node.left, node.right]

    # 递归处理子节点
    if children:
        for child in children:
            if child is not None:  # 确保子节点不为空
                result += format_ast(child, indent + 2)

    return result


# 主窗口类
class CompilerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_file_path = None  # 跟踪当前文件路径
        self.drag_position = None  # 用于窗口拖拽
        self.initUI()

    def initUI(self):
        # 设置无边框窗口
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # 设置窗口属性
        self.setGeometry(100, 100, 1400, 900)  # 稍微调大窗口
        self.setMinimumSize(1000, 700)

        # 创建主容器和布局
        main_container = QWidget()
        self.setCentralWidget(main_container)
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 添加自定义标题栏
        self.title_bar = CustomTitleBar(self)
        main_layout.addWidget(self.title_bar)

        # 创建内容区域
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 5, 10, 10)
        content_layout.setSpacing(8)

        main_layout.addWidget(content_widget)

        # 连接树节点展开/折叠信号
        self.ast_tree_expanded_items = set()  # 用于跟踪展开的节点

        # 设置状态栏样式
        _, ui_fonts = get_best_font_family()
        status_font_family = ", ".join(ui_fonts[:3])

        self.statusBar().setStyleSheet(
            f"""
            QStatusBar {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2d3038, stop: 1 #363944);
                color: #f8f8f2;
                font-family: {status_font_family};
                font-size: 12px;  /* 增加状态栏字体大小 */
                padding: 8px 15px;
                border: none;
                border-top: 1px solid #4a9eff;
                font-weight: 500;
            }}
        """
        )
        self.statusBar().showMessage("就绪")

        # 创建主分割器 - 水平分割
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet(
            """
            QSplitter {
                background-color: #202228;
                border: none;
            }
            QSplitter::handle {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #363944, stop: 1 #4a4c58);
                border: 1px solid #4a9eff;
                border-radius: 3px;
                margin: 2px;
            }
            QSplitter::handle:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                           stop: 0 #4a9eff, stop: 1 #2563eb);
            }
        """
        )
        content_layout.addWidget(self.main_splitter)

        # 创建源代码编辑器 - 使用带行号的编辑器
        self.code_editor = CodeEditor()
        self.code_editor.setPlaceholderText("在这里输入Rust-like代码...")

        # 为源代码编辑器设置语法高亮
        self.rust_highlighter = RustHighlighter(self.code_editor.document())

        # 创建按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)

        self.load_button = QPushButton("📂 加载文件")
        self.load_button.clicked.connect(self.load_file)

        self.save_button = QPushButton("💾 保存文件")
        self.save_button.clicked.connect(self.save_file)

        self.compile_button = QPushButton("🚀 编译")
        self.compile_button.clicked.connect(self.compile_code)

        # 设置现代化按钮样式
        standard_button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #4a4c58, stop: 1 #363944);
                border: 1px solid #4a4c58;
                border-radius: 8px;
                color: #f8f8f2;
                font-weight: 500;
                padding: 10px 16px;
                font-size: 12px;  /* 增加按钮字体大小 */
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #5a5c68, stop: 1 #464854);
                border: 1px solid #4a9eff;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #2d3038, stop: 1 #363944);
                border: 1px solid #2563eb;
            }
        """

        # 编译按钮特殊样式（主要操作）
        compile_button_style = """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #4a9eff, stop: 1 #2563eb);
                border: 1px solid #4a9eff;
                border-radius: 8px;
                color: #ffffff;
                font-weight: bold;
                padding: 12px 20px;
                font-size: 12px;
                min-width: 120px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #60a5fa, stop: 1 #3b82f6);
                border: 1px solid #60a5fa;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #1e40af, stop: 1 #1d4ed8);
                border: 1px solid #1e40af;
            }
        """

        self.load_button.setStyleSheet(standard_button_style)
        self.save_button.setStyleSheet(standard_button_style)
        self.compile_button.setStyleSheet(compile_button_style)

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()  # 添加弹性空间
        button_layout.addWidget(self.compile_button)

        # 创建错误输出框
        self.error_output = QTextEdit()
        self.error_output.setMaximumHeight(150)  # 限制高度
        self.error_output.setPlaceholderText("编译错误和警告将显示在这里...")
        self.error_output.setReadOnly(True)

        # 设置错误输出的字体
        code_fonts, _ = get_best_font_family()
        error_font = QFont()
        error_font.setFamily(", ".join(code_fonts[:3]))
        error_font.setPointSize(10)
        error_font.setHintingPreference(QFont.PreferFullHinting)
        self.error_output.setFont(error_font)

        # 现代化错误输出样式
        self.error_output.setStyleSheet(
            """
            QTextEdit {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #181b20, stop: 1 #1a1d23);
                color: #f8f8f2;
                border: 1px solid #363944;
                border-radius: 8px;
                padding: 10px;
                selection-background-color: #4a9eff;
                selection-color: #ffffff;
            }
            QTextEdit:focus {
                border: 2px solid #4a9eff;
            }
        """
        )

        # 创建错误输出工具栏
        error_toolbar = QHBoxLayout()
        error_toolbar.setContentsMargins(0, 0, 0, 5)

        error_label = QLabel("输出:")
        _, ui_fonts = get_best_font_family()
        error_label.setStyleSheet(
            f"color: #f8f8f2; font-weight: bold; font-family: {', '.join(ui_fonts[:3])};"
        )
        error_toolbar.addWidget(error_label)

        error_toolbar.addStretch()  # 添加弹性空间

        # 清空输出按钮
        clear_output_btn = QPushButton("🗑️ 清空")
        clear_output_btn.setMaximumSize(80, 30)
        clear_output_btn.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #6b7280, stop: 1 #4b5563);
                color: #ffffff;
                border: 1px solid #6b7280;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #ef4444, stop: 1 #dc2626);
                border: 1px solid #ef4444;
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #dc2626, stop: 1 #b91c1c);
            }
        """
        )
        clear_output_btn.clicked.connect(self.clear_error_output)
        error_toolbar.addWidget(clear_output_btn)

        # 为错误输出添加右键菜单
        self.error_output.setContextMenuPolicy(Qt.CustomContextMenu)
        self.error_output.customContextMenuRequested.connect(
            self.show_error_context_menu
        )

        # 为错误输出添加双击事件
        self.error_output.mouseDoubleClickEvent = self.on_error_double_click

        # 创建左侧区域 - 使用垂直分割器分割代码编辑器和错误输出
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 创建错误输出容器（包含工具栏和输出框）
        error_container = QWidget()
        error_container_layout = QVBoxLayout(error_container)
        error_container_layout.setContentsMargins(0, 0, 0, 0)
        error_container_layout.setSpacing(0)
        error_container_layout.addLayout(error_toolbar)
        error_container_layout.addWidget(self.error_output)

        # 创建代码编辑区域的分割器
        code_splitter = QSplitter(Qt.Vertical)
        code_splitter.addWidget(self.code_editor)
        code_splitter.addWidget(error_container)
        code_splitter.setSizes([400, 150])  # 代码编辑器400，错误输出150

        left_layout.addWidget(code_splitter)
        left_layout.addWidget(button_widget)

        # 创建结果标签页
        self.result_tabs = QTabWidget()

        # 创建词法分析结果表格
        self.token_table = QTableWidget()
        self.token_table.setColumnCount(4)
        self.token_table.setHorizontalHeaderLabels(["类型", "值", "行", "列"])
        self.token_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.token_table.setWordWrap(False)

        # 设置表格字体
        code_fonts, _ = get_best_font_family()
        table_font = QFont()
        table_font.setFamily(", ".join(code_fonts[:3]))
        table_font.setPointSize(12)  # 增大表格字体
        table_font.setStyleStrategy(QFont.PreferAntialias)  # 启用抗锯齿
        self.token_table.setFont(table_font)
        # 设置列宽
        self.token_table.horizontalHeader().setStretchLastSection(False)
        self.token_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Interactive
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Interactive
        )
        self.token_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Interactive
        )

        # 创建带保存按钮的语法分析标签页
        self.ast_container = QWidget()
        ast_layout = QVBoxLayout(self.ast_container)

        # 创建顶部控制栏（包含展开/折叠和保存按钮）
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # 添加展开/折叠按钮
        expand_all_btn = QPushButton("全部展开")
        collapse_all_btn = QPushButton("全部折叠")
        save_ast_btn = QPushButton("保存AST")

        # 设置按钮样式
        button_style = """
            QPushButton {
                background-color: #44475a;
                color: #f8f8f2;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
                margin-left: 5px;
            }
            QPushButton:hover {
                background-color: #6272a4;
            }
            QPushButton:pressed {
                background-color: #535770;
            }
        """
        expand_all_btn.setStyleSheet(button_style)
        collapse_all_btn.setStyleSheet(button_style)
        save_ast_btn.setStyleSheet(button_style)

        # 创建AST树形视图组件
        self.ast_tree = QTreeWidget()
        self.ast_tree.setHeaderLabels(["语法分析树 (AST)"])
        self.ast_tree.setColumnCount(1)
        self.ast_tree.setAlternatingRowColors(False)  # 不使用交替行颜色
        self.ast_tree.setAnimated(True)  # 使用动画效果

        # 改进头部样式
        _, ui_fonts = get_best_font_family()
        header_font_family = ", ".join([f"'{font}'" for font in ui_fonts[:3]])

        self.ast_tree.header().setStyleSheet(
            f"""
            QHeaderView::section {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #3a3a3a, stop: 1 #2d2d2d);
                color: #ffffff;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid #4a9eff;
                font-family: {header_font_family};
                font-size: 12px;
                font-weight: bold;
                text-align: center;
            }}
            QHeaderView::section:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4a4a4a, stop: 1 #3d3d3d);
            }}
        """
        )

        # 创建中间代码表格组件
        self.ir_table = QTableWidget()
        self.ir_table.setColumnCount(4)
        self.ir_table.setHorizontalHeaderLabels(
            ["运算符", "操作数1", "操作数2", "结果"]
        )
        self.ir_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.ir_table.setWordWrap(False)

        # 设置中间代码表格字体
        self.ir_table.setFont(table_font)

        # 创建目标代码文本编辑器组件
        self.target_code = QTextEdit()
        self.target_code.setReadOnly(True)
        self.target_code.setLineWrapMode(QTextEdit.NoWrap)

        # 设置目标代码编辑器字体
        self.target_code.setFont(table_font)

        # 连接按钮信号
        expand_all_btn.clicked.connect(self.expand_ast_tree)
        collapse_all_btn.clicked.connect(self.collapse_ast_tree)
        save_ast_btn.clicked.connect(self.save_ast)

        # 添加弹簧和按钮到顶部布局
        top_layout.addStretch()
        top_layout.addWidget(expand_all_btn)
        top_layout.addWidget(collapse_all_btn)
        top_layout.addWidget(save_ast_btn)

        # 添加到主布局
        ast_layout.addWidget(top_widget)
        ast_layout.addWidget(self.ast_tree, 1)

        # 创建带保存按钮的中间代码标签页
        self.ir_container = QWidget()
        ir_layout = QVBoxLayout(self.ir_container)

        # 中间代码保存按钮
        ir_top_widget = QWidget()
        ir_top_layout = QHBoxLayout(ir_top_widget)
        ir_top_layout.setContentsMargins(5, 5, 5, 5)

        save_ir_btn = QPushButton("保存中间代码")
        save_ir_btn.setStyleSheet(button_style)
        save_ir_btn.clicked.connect(self.save_ir)

        ir_top_layout.addStretch()
        ir_top_layout.addWidget(save_ir_btn)

        ir_layout.addWidget(ir_top_widget)
        ir_layout.addWidget(self.ir_table, 1)

        # 创建带保存按钮的目标代码标签页
        self.target_container = QWidget()
        target_layout = QVBoxLayout(self.target_container)

        # 目标代码保存按钮
        target_top_widget = QWidget()
        target_top_layout = QHBoxLayout(target_top_widget)
        target_top_layout.setContentsMargins(5, 5, 5, 5)

        save_asm_btn = QPushButton("保存目标代码")
        save_asm_btn.setStyleSheet(button_style)
        save_asm_btn.clicked.connect(self.save_asm)

        target_top_layout.addStretch()
        target_top_layout.addWidget(save_asm_btn)

        target_layout.addWidget(target_top_widget)
        target_layout.addWidget(self.target_code, 1)

        # AST树形视图已在前面创建，这里继续配置其他属性
        self.ast_tree.setIndentation(25)  # 调整缩进距离，给连接线更多空间
        # 启用水平滚动，禁用自动换行
        self.ast_tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)
        self.ast_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ast_tree.setWordWrap(False)
        self.ast_tree.header().setStretchLastSection(False)  # 防止最后一列自动拉伸
        self.ast_tree.header().setDefaultSectionSize(1500)  # 设置更宽的默认列宽
        self.ast_tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)  # 平滑滚动
        self.ast_tree.setWordWrap(False)  # 禁用自动换行
        self.ast_tree.setTextElideMode(Qt.ElideNone)  # 不省略文本
        self.ast_tree.setRootIsDecorated(True)  # 显示展开/折叠控件
        self.ast_tree.setExpandsOnDoubleClick(True)  # 双击展开/折叠
        self.ast_tree.setUniformRowHeights(False)  # 允许不同高度的行
        self.ast_tree.setItemsExpandable(True)  # 允许展开项目
        self.ast_tree.setAutoExpandDelay(500)  # 设置自动展开延迟

        # 连接树节点展开/折叠信号
        self.ast_tree.itemExpanded.connect(self.on_item_expanded)
        self.ast_tree.itemCollapsed.connect(self.on_item_collapsed)

        # 设置树形视图样式
        code_fonts, _ = get_best_font_family()
        ast_font_family = ", ".join([f"'{font}'" for font in code_fonts[:3]])

        self.ast_tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: #1e1e1e;
                border: 1px solid #444444;
                font-family: {ast_font_family};
                font-size: 11px;
                color: #f8f8f2;
                outline: none;
                alternate-background-color: #252525;
                show-decoration-selected: 1;
            }}
            QTreeWidget::item {{
                padding: 4px 8px;
                border: 1px solid transparent;
                color: #f8f8f2;
                border-radius: 4px;
                margin: 1px 2px;
            }}
            QTreeWidget::item:selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #2563eb, stop: 1 #1d4ed8);
                border: 1px solid #3b82f6;
                border-radius: 4px;
                color: #ffffff;
                font-weight: 500;
            }}
            QTreeWidget::item:selected:active {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1d4ed8, stop: 1 #1e40af);
                border: 1px solid #2563eb;
            }}
            QTreeWidget::item:selected:!active {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #64748b, stop: 1 #475569);
                border: 1px solid #6b7280;
                color: #f1f5f9;
            }}
            QTreeWidget::item:hover {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #334155, stop: 1 #1e293b);
                border: 1px solid #475569;
                border-radius: 3px;
                color: #f8fafc;
            }}
            QTreeWidget::item:hover:!selected {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #374151, stop: 1 #1f2937);
                border: 1px solid #6b7280;
            }}
            /* 简化且更清晰的树形连接线系统 */
            QTreeWidget::branch {{
                background-color: transparent;
                margin: 0px;
                padding: 0px;
                width: 16px;
                height: 16px;
            }}
            
            /* 垂直连接线（连接到兄弟节点） */
            QTreeWidget::branch:has-siblings:!adjoins-item {{
                border-left: 2px solid #64748b;
                margin-left: 8px;
                background: transparent;
            }}
            
            /* L型连接线（当前节点的连接） */
            QTreeWidget::branch:has-siblings:adjoins-item {{
                border-left: 2px solid #64748b;
                border-top: 2px solid #64748b;
                margin-left: 8px;
                border-top-left-radius: 4px;
                background: transparent;
                width: 14px;
                height: 14px;
            }}
            
            /* 末尾节点的连接线（无兄弟节点）*/
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {{
                border-left: 2px solid #64748b;
                border-top: 2px solid #64748b;
                margin-left: 8px;
                border-top-left-radius: 4px;
                border-bottom-left-radius: 4px;
                background: transparent;
                width: 14px;
                height: 14px;
            }}
            
            /* 层级颜色区分 */
            /* 第一层 - 蓝色 */
            QTreeWidget > QTreeWidgetItem > QTreeWidget::branch {{
                border-color: #3b82f6;
            }}
            
            /* 第二层 - 紫色 */
            QTreeWidget > QTreeWidgetItem > QTreeWidgetItem > QTreeWidget::branch {{
                border-color: #8b5cf6;
            }}
            
            /* 第三层 - 绿色 */
            QTreeWidget > QTreeWidgetItem > QTreeWidgetItem > QTreeWidgetItem > QTreeWidget::branch {{
                border-color: #059669;
            }}
            
            /* 更深层级 - 灰色 */
            QTreeWidget > QTreeWidgetItem > QTreeWidgetItem > QTreeWidgetItem > QTreeWidgetItem > QTreeWidget::branch {{
                border-color: #6b7280;
            }}
            
            /* 展开/折叠指示器 - 更精美的设计 */
            QTreeWidget::branch:has-children:!has-siblings:closed,
            QTreeWidget::branch:closed:has-children:has-siblings {{
                border-image: none;
                image: none;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #10b981, stop: 0.5 #059669, stop: 1 #047857);
                border: 3px solid #10b981;
                border-radius: 12px;
                width: 24px;
                height: 24px;
                margin: 3px;
                subcontrol-position: center;
            }}
            
            QTreeWidget::branch:open:has-children:!has-siblings,
            QTreeWidget::branch:open:has-children:has-siblings {{
                border-image: none;
                image: none;
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                                          stop: 0 #f59e0b, stop: 0.5 #d97706, stop: 1 #b45309);
                border: 3px solid #f59e0b;
                border-radius: 12px;
                width: 24px;
                height: 24px;
                margin: 3px;
                subcontrol-position: center;
            }}
            
            /* 增强节点间距和对齐 */
            QTreeWidget::item {{
                padding: 4px 8px;
                margin: 1px 2px;
                border-radius: 4px;
                min-height: 16px;
            }}
            
            /* 为根节点特殊处理 */
            QTreeWidget > QTreeWidgetItem {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #1e40af, stop: 1 #1e3a8a);
                border: 2px solid #3b82f6;
                border-radius: 8px;
                font-weight: bold;
                font-size: 12px;
                color: #ffffff;
                margin: 3px 2px;
                padding: 6px 10px;
            }}
            
            /* 子节点样式优化 */
            QTreeWidget QTreeWidgetItem QTreeWidgetItem {{
                margin-left: 8px;
                border-left: 2px solid rgba(100, 116, 139, 0.3);
                background: rgba(55, 65, 81, 0.7);
            }}
            
            /* 深层节点渐变透明度 */
            QTreeWidget QTreeWidgetItem QTreeWidgetItem QTreeWidgetItem {{
                background: rgba(55, 65, 81, 0.5);
                margin-left: 12px;
            }}
            
            QTreeWidget QTreeWidgetItem QTreeWidgetItem QTreeWidgetItem QTreeWidgetItem {{
                background: rgba(55, 65, 81, 0.3);
                margin-left: 16px;
            }}
            /* 树形视图表头 */
            QHeaderView::section {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                          stop: 0 #4338ca, stop: 1 #1e1b4b);
                color: #f8f8f2;
                border: 1px solid #444444;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 4px;
            }}
        """
        )

        # 中间代码表格已在前面创建，这里继续配置其他属性
        # 设置列宽和调整模式
        self.ir_table.horizontalHeader().setStretchLastSection(False)
        self.ir_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Interactive
        )
        self.ir_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Interactive
        )
        self.ir_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.Interactive
        )
        self.ir_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.Interactive
        )
        # 设置默认列宽
        self.ir_table.setColumnWidth(0, 100)
        self.ir_table.setColumnWidth(1, 200)
        self.ir_table.setColumnWidth(2, 200)
        self.ir_table.setColumnWidth(3, 200)

        # 目标代码编辑器已在前面创建，这里继续配置其他属性
        self.target_code.setFont(QFont("Consolas", 12))
        self.target_code.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.target_code.setWordWrapMode(QTextOption.NoWrap)  # 禁用词换行

        # 为目标代码设置语法高亮
        self.mips_highlighter = MIPSHighlighter(self.target_code.document())

        # 设置标签页的样式和行为
        self.result_tabs.setTabBarAutoHide(False)  # 总是显示标签栏
        self.result_tabs.setElideMode(Qt.ElideNone)  # 不省略标签文本
        self.result_tabs.setMovable(True)  # 允许拖动标签
        self.result_tabs.setTabsClosable(False)  # 不显示关闭按钮
        self.result_tabs.setDocumentMode(True)  # 使用文档模式外观
        self.result_tabs.setStyleSheet(
            """
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #363944, stop: 1 #2d3038);
                border: 1px solid #2d3038;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 0px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #a0a2a8;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #4a9eff, stop: 1 #2563eb);
                color: #ffffff;
                border: 1px solid #2563eb;
                border-bottom: none;
                font-weight: bold;
            }
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                           stop: 0 #464854, stop: 1 #3d3f4a);
                color: #f8f8f2;
                border: 1px solid #3d3f4a;
                border-bottom: none;
            }
            QTabWidget::pane {
                border: 1px solid #2d3038;
                border-radius: 8px;
                background-color: #181b20;
                margin-top: -1px;
                border-top-left-radius: 0px;
            }
        """
        )

        # 添加标签页
        self.result_tabs.addTab(self.token_table, "词法分析")
        self.result_tabs.addTab(self.ast_container, "语法分析")
        self.result_tabs.addTab(self.ir_container, "中间代码")
        self.result_tabs.addTab(self.target_container, "目标代码")

        # 添加到主分割器
        self.main_splitter.addWidget(left_widget)
        self.main_splitter.addWidget(self.result_tabs)
        self.main_splitter.setSizes([500, 700])  # 设置初始分割大小

    def load_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开文件", "", "Rust Files (*.rs);;All Files (*)", options=options
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.code_editor.setPlainText(f.read())  # 注意这里使用setPlainText
                self.current_file_path = file_path  # 保存当前文件路径
                self.setWindowTitle(f"Toy Rust Compiler - {file_path}")
                QMessageBox.information(self, "成功", f"成功加载文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件: {str(e)}")

    def save_file(self):
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存文件", "", "Rust Files (*.rs);;All Files (*)", options=options
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.code_editor.toPlainText())
                self.current_file_path = file_path  # 保存当前文件路径
                self.setWindowTitle(f"Toy Rust Compiler - {file_path}")
                QMessageBox.information(self, "成功", f"成功保存文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")

    def show_error_dialog(self, title, message):
        """显示增强的错误对话框"""
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle(title)
        error_dialog.setText("编译过程中发现以下问题：")
        error_dialog.setDetailedText(message)
        error_dialog.setIcon(QMessageBox.Critical)

        # 设置对话框样式
        error_dialog.setStyleSheet(
            """
            QMessageBox {
                background-color: #2d3748;
                color: #f8f8f2;
            }
            QMessageBox QLabel {
                color: #f8f8f2;
                font-size: 12px;
            }
            QMessageBox QPushButton {
                background-color: #4a5568;
                color: #f8f8f2;
                border: 1px solid #718096;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: #718096;
            }
            QMessageBox QPushButton:pressed {
                background-color: #2d3748;
            }
            QTextEdit {
                background-color: #1a202c;
                color: #f8f8f2;
                border: 1px solid #4a5568;
                font-family: 'Consolas', monospace;
                font-size: 12px;  /* 增加错误对话框字体大小 */
            }
        """
        )

        error_dialog.exec_()

    def save_ast(self):
        """保存AST语法树到文件"""
        try:
            # 确保输出目录存在
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "test", "output", "ast"
            )
            os.makedirs(output_dir, exist_ok=True)

            # 生成默认文件名
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"ast_{timestamp}.txt"
            default_path = os.path.join(output_dir, default_filename)

            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存AST语法树", default_path, "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # 获取AST树的文本表示
                ast_text = self.get_ast_text()

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ast_text)

                QMessageBox.information(self, "成功", f"AST已保存到: {file_path}")
                self.statusBar().showMessage(f"AST已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存AST失败: {str(e)}")

    def save_ir(self):
        """保存中间代码到文件"""
        try:
            # 确保输出目录存在
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "test", "output", "ir"
            )
            os.makedirs(output_dir, exist_ok=True)

            # 生成默认文件名
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"ir_{timestamp}.txt"
            default_path = os.path.join(output_dir, default_filename)

            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存中间代码", default_path, "Text Files (*.txt);;All Files (*)"
            )

            if file_path:
                # 从表格中提取中间代码
                ir_text = self.get_ir_text()

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(ir_text)

                QMessageBox.information(self, "成功", f"中间代码已保存到: {file_path}")
                self.statusBar().showMessage(f"中间代码已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存中间代码失败: {str(e)}")

    def save_asm(self):
        """保存目标代码（汇编）到文件"""
        try:
            # 确保输出目录存在
            output_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "test", "output", "asm"
            )
            os.makedirs(output_dir, exist_ok=True)

            # 生成默认文件名
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"asm_{timestamp}.asm"
            default_path = os.path.join(output_dir, default_filename)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存目标代码",
                default_path,
                "Assembly Files (*.asm);;Text Files (*.txt);;All Files (*)",
            )

            if file_path:
                # 获取目标代码文本
                asm_text = self.target_code.toPlainText()

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(asm_text)

                QMessageBox.information(self, "成功", f"目标代码已保存到: {file_path}")
                self.statusBar().showMessage(f"目标代码已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存目标代码失败: {str(e)}")

    def get_ast_text(self):
        """获取AST树的文本表示"""

        def tree_to_text(item, indent=0):
            text = "  " * indent + item.text(0) + "\n"
            for i in range(item.childCount()):
                text += tree_to_text(item.child(i), indent + 1)
            return text

        if self.ast_tree.topLevelItemCount() == 0:
            return "# AST为空\n"

        result = "# Rust-like语言语法树 (AST)\n"
        result += "# Generated by Rust-like Compiler\n\n"

        for i in range(self.ast_tree.topLevelItemCount()):
            item = self.ast_tree.topLevelItem(i)
            result += tree_to_text(item)

        return result

    def get_ir_text(self):
        """获取中间代码的文本表示"""
        if self.ir_table.rowCount() == 0:
            return "# 中间代码为空\n"

        result = "# Rust-like语言中间代码 (IR)\n"
        result += "# Generated by Rust-like Compiler\n"
        result += "# Format: (Operator, Operand1, Operand2, Result)\n\n"

        for row in range(self.ir_table.rowCount()):
            op = self.ir_table.item(row, 0).text() if self.ir_table.item(row, 0) else ""
            arg1 = (
                self.ir_table.item(row, 1).text() if self.ir_table.item(row, 1) else ""
            )
            arg2 = (
                self.ir_table.item(row, 2).text() if self.ir_table.item(row, 2) else ""
            )
            result_text = (
                self.ir_table.item(row, 3).text() if self.ir_table.item(row, 3) else ""
            )

            result += f"({op}, {arg1}, {arg2}, {result_text})\n"

        return result

    def log_to_console(self, message, color="white"):
        """更新状态栏信息"""
        # 去除消息中的换行符和格式化字符
        clean_message = message.replace("\n", " ").strip()
        if clean_message:  # 如果消息非空
            self.statusBar().showMessage(clean_message)

    def log_compilation_stage(self, stage):
        """显示编译阶段信息"""
        self.statusBar().showMessage(f"正在执行: {stage}")
        QApplication.processEvents()  # 确保UI更新

    def compile_code(self):
        # 清空之前的结果
        self.token_table.setRowCount(0)
        self.ast_tree.clear()
        self.ir_table.setRowCount(0)
        self.target_code.clear()

        # 开始编译
        self.log_compilation_stage("编译开始")

        source_code = self.code_editor.toPlainText()

        if not source_code.strip():
            QMessageBox.warning(self, "警告", "请输入代码后再编译")
            self.statusBar().showMessage("错误: 请输入代码后再编译")
            return

        try:
            # 词法分析
            self.log_compilation_stage("词法分析")
            lexer = Lexer(source_code)
            tokens = lexer.tokenize()

            # 更新词法分析结果表
            self.token_table.setRowCount(0)  # 清空表格
            for i, token in enumerate(tokens):
                self.token_table.insertRow(i)
                self.token_table.setItem(i, 0, QTableWidgetItem(token.type))
                self.token_table.setItem(i, 1, QTableWidgetItem(token.value))
                self.token_table.setItem(i, 2, QTableWidgetItem(str(token.line)))
                self.token_table.setItem(i, 3, QTableWidgetItem(str(token.column)))

            # 语法分析
            self.log_compilation_stage("语法分析")
            parser_lexer = Lexer(source_code)
            irgen = IRGenerator()
            parser = myparser.Parser(parser_lexer, irgen)
            ast = parser.parse_program()

            # 确保AST不为空
            if ast is None:
                raise Exception("语法分析生成的AST为空")

            self.log_to_console("语法分析成功，生成AST.\n")
            self.log_to_console("AST根节点: " + ast.__class__.__name__ + "\n")

            # 语义分析
            self.log_compilation_stage("语义分析")
            semantic_analyzer = SemanticAnalyzer()
            semantic_errors = semantic_analyzer.analyze(ast)

            # 显示错误和警告在输出框中
            self.show_errors_in_output(semantic_errors)

            # 检查是否有致命错误（非警告）
            if semantic_errors:
                fatal_errors = [
                    e
                    for e in semantic_errors
                    if not e.error_type.startswith("warning_")
                ]

                if fatal_errors:
                    self.statusBar().showMessage(
                        f"编译失败: {len(fatal_errors)} 个错误, {len(semantic_errors) - len(fatal_errors)} 个警告"
                    )
                    return  # 停止编译
                else:
                    # 只有警告，继续编译
                    self.statusBar().showMessage(
                        f"编译完成: {len(semantic_errors)} 个警告"
                    )
            else:
                self.statusBar().showMessage("编译成功: 无错误或警告")

            # 只更新AST树形视图
            self.ast_tree.clear()
            root_item = self.build_ast_tree(ast, self.ast_tree)

            # 只展开前几层，而不是所有节点
            self.expand_to_level(root_item, 3)  # 展开到第3层

            # 如果是根节点，确保它被选中和可见
            if root_item:
                self.ast_tree.setCurrentItem(root_item)
                self.ast_tree.scrollToItem(root_item)

            self.ast_tree.setColumnWidth(0, 350)  # 设置适当的列宽

            # 中间代码生成
            self.log_compilation_stage("中间代码生成")
            irgen.generate(ast)
            ir_quads = irgen.quads

            # 更新中间代码表
            self.ir_table.setRowCount(0)  # 清空表格
            for i, quad in enumerate(ir_quads):
                self.ir_table.insertRow(i)
                self.ir_table.setItem(i, 0, QTableWidgetItem(str(quad.op)))
                self.ir_table.setItem(i, 1, QTableWidgetItem(str(quad.arg1)))
                self.ir_table.setItem(i, 2, QTableWidgetItem(str(quad.arg2)))
                self.ir_table.setItem(i, 3, QTableWidgetItem(str(quad.result)))

            # 目标代码生成
            self.log_compilation_stage("目标代码生成")
            code_gen = MIPSCodeGenerator(ir_quads)
            asm_code = code_gen.gen_asm()

            # 更新目标代码视图
            self.target_code.setText(asm_code)

            # 切换到语法分析标签页，便于查看AST
            self.result_tabs.setCurrentIndex(1)
            # 显示生成的汇编代码
            self.target_code.setText(asm_code)

            # 应用节点特定的样式
            self.apply_node_specific_styles()

            # 编译完成
            self.statusBar().showMessage("编译完成")

            # 获取文件名（如果有的话）
            if self.current_file_path:
                import os

                file_name = os.path.basename(self.current_file_path)
                success_msg = f'<span style="color: green;">✅ 编译成功完成</span><br/><span style="color: #7f8c8d;">文件: {file_name}</span>'
            else:
                success_msg = '<span style="color: green;">✅ 编译成功完成</span><br/><span style="color: #7f8c8d;">文件: 内存代码</span>'

            current_html = self.error_output.toHtml()
            if current_html and current_html.strip():
                new_content = (
                    current_html
                    + '<hr style="border: 1px solid #ccc; margin: 10px 0;">'
                    + success_msg
                )
            else:
                new_content = success_msg
            self.error_output.setHtml(new_content)

            # 滚动到底部
            cursor = self.error_output.textCursor()
            cursor.movePosition(cursor.End)
            self.error_output.setTextCursor(cursor)

        except myparser.ParseError as e:
            error_msg = f"语法错误: {str(e)}"
            self.statusBar().showMessage(error_msg)

            # 添加更详细的错误信息
            detailed_error = self.format_detailed_parse_error(e, source_code)

            current_html = self.error_output.toHtml()
            error_html = (
                f'<span style="color: red;">❌ 语法错误</span><br/>{detailed_error}'
            )

            if current_html and current_html.strip():
                new_content = (
                    current_html
                    + '<hr style="border: 1px solid #ccc; margin: 10px 0;">'
                    + error_html
                )
            else:
                new_content = error_html
            self.error_output.setHtml(new_content)

            # 滚动到底部
            cursor = self.error_output.textCursor()
            cursor.movePosition(cursor.End)
            self.error_output.setTextCursor(cursor)

        except Exception as e:
            error_msg = f"编译过程中发生错误: {str(e)}"
            self.statusBar().showMessage(error_msg)

            current_html = self.error_output.toHtml()
            error_html = f'<span style="color: red;">❌ 编译错误</span><br/><span style="color: #666;">{error_msg}</span>'

            if current_html and current_html.strip():
                new_content = (
                    current_html
                    + '<hr style="border: 1px solid #ccc; margin: 10px 0;">'
                    + error_html
                )
            else:
                new_content = error_html
            self.error_output.setHtml(new_content)

            # 滚动到底部
            cursor = self.error_output.textCursor()
            cursor.movePosition(cursor.End)
            self.error_output.setTextCursor(cursor)

            import traceback

    def format_detailed_parse_error(self, parse_error, source_code):
        """格式化详细的解析错误信息"""
        error_str = str(parse_error)

        # 尝试从错误信息中提取行号和列号
        import re

        location_match = re.search(r"L(\d+)C(\d+)", error_str)

        if location_match:
            line_num = int(location_match.group(1))
            col_num = int(location_match.group(2))

            # 获取错误行的内容
            lines = source_code.split("\n")
            if 1 <= line_num <= len(lines):
                error_line = lines[line_num - 1]

                # 构建详细错误信息
                detailed_info = f'<span style="color: #666;">位置: 第{line_num}行第{col_num}列</span><br/>'
                detailed_info += f'<span style="color: #666;">错误行: </span><span style="font-family: monospace; background-color: #f8f8f8; padding: 2px;">{error_line}</span><br/>'

                # 添加指针指示错误位置
                if col_num > 0:
                    pointer = " " * (col_num - 1) + "^"
                    detailed_info += f'<span style="font-family: monospace; color: red;">{pointer}</span><br/>'

                # 分析常见的语法错误并给出建议
                suggestions = self.get_parse_error_suggestions(error_str, error_line)
                if suggestions:
                    detailed_info += (
                        f'<span style="color: #3498db;">💡 可能的问题:</span><br/>'
                    )
                    for suggestion in suggestions:
                        detailed_info += f'<span style="color: #7f8c8d; margin-left: 20px;">• {suggestion}</span><br/>'

                return detailed_info

        return f'<span style="color: #666;">{error_str}</span>'

    def get_parse_error_suggestions(self, error_str, error_line):
        """根据错误信息和错误行内容提供建议"""
        suggestions = []

        if "EOF" in error_str:
            if "{" in error_line and "}" not in error_line:
                suggestions.append("可能缺少闭合的花括号 '}'")
            elif "(" in error_line and ")" not in error_line:
                suggestions.append("可能缺少闭合的圆括号 ')'")
            elif "[" in error_line and "]" not in error_line:
                suggestions.append("可能缺少闭合的方括号 ']'")
            else:
                suggestions.append(
                    "代码可能不完整，检查是否缺少分号、括号或其他语法元素"
                )

        if "无法识别的因子" in error_str:
            if "=" in error_line and not error_line.strip().endswith(";"):
                suggestions.append("语句可能缺少分号 ';'")
            if "if" in error_line and "{" not in error_line:
                suggestions.append("if语句可能缺少花括号 '{}'")

        return suggestions

    def clear_error_output(self):
        """清空错误输出"""
        self.error_output.clear()
        self.error_output.setPlaceholderText("编译错误和警告将显示在这里...")

    def expand_to_level(self, item, level):
        """展开树到指定层级"""
        if not item:
            return

        if level > 0:
            item.setExpanded(True)
            # 更新展开状态图标
            text = item.text(0)
            if text.startswith("▶ "):
                item.setText(0, "▼ " + text[2:])
            for i in range(item.childCount()):
                self.expand_to_level(item.child(i), level - 1)

    def on_item_expanded(self, item):
        """处理节点展开事件"""
        text = item.text(0)
        if text.startswith("▶ "):
            # 保持子节点计数，只更改展开/折叠图标
            remaining_text = text[2:]  # 去掉 "▶ "
            item.setText(0, "▼ " + remaining_text)

    def on_item_collapsed(self, item):
        """处理节点折叠事件"""
        text = item.text(0)
        if text.startswith("▼ "):
            # 保持子节点计数，只更改展开/折叠图标
            remaining_text = text[2:]  # 去掉 "▼ "
            item.setText(0, "▶ " + remaining_text)

    def update_tree_icons(self, item=None, expanded=True):
        """递归更新树节点的展开/折叠图标"""
        if item is None:
            root = self.ast_tree.invisibleRootItem()
            for i in range(root.childCount()):
                self.update_tree_icons(root.child(i), expanded)
            return

        text = item.text(0)
        if text.startswith("▼ ") or text.startswith("▶ "):
            item.setText(0, ("▼ " if expanded else "▶ ") + text[2:])

        for i in range(item.childCount()):
            self.update_tree_icons(item.child(i), expanded)

    def expand_ast_tree(self):
        """展开整个AST树"""
        self.ast_tree.expandAll()
        self.update_tree_icons(expanded=True)

    def collapse_ast_tree(self):
        """折叠整个AST树"""
        self.ast_tree.collapseAll()
        self.update_tree_icons(expanded=False)

    def get_node_category(self, node_type):
        """根据节点类型返回其类别"""
        program_nodes = ["ProgramNode", "FunctionDeclNode", "ParamNode"]
        statement_nodes = [
            "BlockNode",
            "LetDeclNode",
            "IfNode",
            "WhileNode",
            "ForNode",
            "ReturnNode",
            "AssignNode",
        ]
        expression_nodes = ["BinaryOpNode", "UnaryOpNode", "FunctionCallNode"]
        literal_nodes = [
            "NumberNode",
            "StringLiteralNode",
            "BooleanLiteralNode",
            "IdentifierNode",
        ]
        type_nodes = ["TypeNode"]

        if node_type in program_nodes:
            return "program"
        elif node_type in statement_nodes:
            return "statement"
        elif node_type in expression_nodes:
            return "expression"
        elif node_type in literal_nodes:
            return "literal"
        elif node_type in type_nodes:
            return "type"
        else:
            return "other"

    def create_bordered_widget(self, text, border_style, text_color):
        """创建带有样式的文本标签部件 (简化版，保留方法防止引用错误)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)

        label = QLabel(text)
        label.setStyleSheet(f"color: {text_color};")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        layout.addWidget(label)
        return widget

    def apply_node_specific_styles(self):
        """为AST节点应用特定的样式"""
        # 为不同类型的节点设置特定的边框样式
        additional_styles = """
            /* 程序结构节点 */
            QTreeWidget::item[data="program"] {
                border: 2px solid #3b82f6;
                border-radius: 6px;
                font-weight: bold;
            }
            
            /* 条件语句节点 */
            QTreeWidget::item[data="conditional"] {
                border: 2px solid #8b5cf6;
                border-radius: 4px;
            }
            
            /* 循环语句节点 */
            QTreeWidget::item[data="loop"] {
                border: 2px solid #10b981;
                border-radius: 4px;
            }
            
            /* 赋值语句节点 */
            QTreeWidget::item[data="assignment"] {
                border: 2px solid #ef4444;
                border-radius: 4px;
            }
            
            /* 返回语句节点 */
            QTreeWidget::item[data="return"] {
                border: 2px solid #f97316;
                border-radius: 4px;
            }
            
            /* 二元表达式节点 */
            QTreeWidget::item[data="binary"] {
                border: 2px solid #06b6d4;
                border-radius: 4px;
            }
            
            /* 函数相关节点 */
            QTreeWidget::item[data="function"] {
                border: 2px solid #a16207;
                border-radius: 4px;
            }
            
            /* 数字字面值节点 */
            QTreeWidget::item[data="number"] {
                border: 2px solid #2563eb;
                border-radius: 4px;
            }
            
            /* 字符串字面值节点 */
            QTreeWidget::item[data="string"] {
                border: 2px solid #16a34a;
                border-radius: 4px;
            }
            
            /* 标识符节点 */
            QTreeWidget::item[data="identifier"] {
                border: 2px solid #9333ea;
                border-radius: 4px;
            }
            
            /* 类型节点 */
            QTreeWidget::item[data="type"] {
                border: 2px solid #4f46e5;
                border-radius: 4px;
            }
        """

        current_style = self.ast_tree.styleSheet()
        self.ast_tree.setStyleSheet(current_style + additional_styles)

    def get_node_color(self, node_type):
        """根据节点类型返回颜色"""
        # 使用更柔和、专业的颜色方案 - 亮色系适合深色背景
        colors = {
            # 程序结构
            "ProgramNode": "#6ca7fc",  # 亮蓝色
            "FunctionDeclNode": "#79a8ff",  # 亮淡蓝色
            "ParamNode": "#92b5ff",  # 亮浅蓝色
            # 块和语句
            "BlockNode": "#a4b4c4",  # 亮灰色
            "LetDeclNode": "#c77dde",  # 亮紫色
            "IfNode": "#ff9c4e",  # 亮橙色
            "WhileNode": "#ff9c4e",  # 亮橙色
            "ForNode": "#ff9c4e",  # 亮橙色
            "ReturnNode": "#ff7676",  # 亮红色
            "AssignNode": "#c77dde",  # 亮紫色
            # 表达式
            "BinaryOpNode": "#4dc4bc",  # 亮青色
            "UnaryOpNode": "#4dc4bc",  # 亮青色
            "FunctionCallNode": "#b16dd9",  # 亮深紫色
            "FunctionExprNode": "#b16dd9",  # 亮深紫色
            # 字面值和标识符
            "NumberNode": "#e6d735",  # 亮金色
            "StringLiteralNode": "#a8cc00",  # 亮绿色
            "BooleanLiteralNode": "#e6d735",  # 亮金色
            "IdentifierNode": "#42a8f5",  # 亮深蓝色
            # 类型
            "TypeNode": "#8db1b6",  # 亮青灰色
            "VariableInternalDeclNode": "#ffa726",  # 橙色
        }

        # 返回颜色，如果没有特定颜色则返回白色
        return colors.get(node_type, "#ffffff")
        """根据节点类型返回颜色"""
        # 使用更柔和、专业的颜色方案 - 亮色系适合深色背景
        colors = {
            # 程序结构
            "ProgramNode": "#6ca7fc",  # 亮蓝色
            "FunctionDeclNode": "#79a8ff",  # 亮淡蓝色
            "ParamNode": "#92b5ff",  # 亮浅蓝色
            # 块和语句
            "BlockNode": "#a4b4c4",  # 亮灰色
            "LetDeclNode": "#c77dde",  # 亮紫色
            "IfNode": "#ff9c4e",  # 亮橙色
            "WhileNode": "#ff9c4e",  # 亮橙色
            "ForNode": "#ff9c4e",  # 亮橙色
            "ReturnNode": "#ff7676",  # 亮红色
            "AssignNode": "#c77dde",  # 亮紫色
            # 表达式
            "BinaryOpNode": "#4dc4bc",  # 亮青色
            "UnaryOpNode": "#4dc4bc",  # 亮青色
            "FunctionCallNode": "#b16dd9",  # 亮深紫色
            # 字面值和标识符
            "NumberNode": "#e6d735",  # 亮金色
            "StringLiteralNode": "#a8cc00",  # 亮绿色
            "BooleanLiteralNode": "#e6d735",  # 亮金色
            "IdentifierNode": "#42a8f5",  # 亮深蓝色
            # 类型
            "TypeNode": "#8db1b6",  # 亮青灰色
        }

        # 返回颜色，如果没有特定颜色则返回黑色
        return colors.get(node_type, "#000000")

    def build_ast_tree(self, node, tree_widget, parent_item=None):
        """为语法树节点创建改进版的树形视图"""
        if node is None:
            return

        # 获取节点的类名
        node_class_name = node.__class__.__name__

        # 创建主要标签 - 添加展开/折叠指示符和类型图标
        main_label = node_class_name.replace("Node", "")

        # 为不同类型的节点添加图标
        node_category = self.get_node_category(node_class_name)
        if node_category == "program":
            main_label = "🏛️ " + main_label
        elif node_category == "statement":
            if "If" in node_class_name:
                main_label = "🔀 " + main_label
            elif (
                "While" in node_class_name
                or "For" in node_class_name
                or "Loop" in node_class_name
            ):
                main_label = "🔄 " + main_label
            elif "Let" in node_class_name:
                main_label = "📝 " + main_label
            elif "Assign" in node_class_name:
                main_label = "➡️ " + main_label
            elif "Return" in node_class_name:
                main_label = "↩️ " + main_label
            else:
                main_label = "📄 " + main_label
        elif node_category == "expression":
            if "Binary" in node_class_name:
                main_label = "⚡ " + main_label
            elif "Unary" in node_class_name:
                main_label = "🔧 " + main_label
            elif "Function" in node_class_name:
                main_label = "🔧 " + main_label
            else:
                main_label = "💡 " + main_label
        elif node_category == "literal":
            if "Number" in node_class_name:
                main_label = "🔢 " + main_label
            elif "String" in node_class_name:
                main_label = "📝 " + main_label
            elif "Boolean" in node_class_name:
                main_label = "☑️ " + main_label
            elif "Identifier" in node_class_name:
                main_label = "🏷️ " + main_label
            else:
                main_label = "💎 " + main_label
        elif node_category == "type":
            main_label = "🏗️ " + main_label
        else:
            main_label = "📦 " + main_label

        # 提前收集所有子节点
        children = []

        # 检查集合类型的子节点
        if hasattr(node, "children") and node.children:
            children.extend(node.children)
        if hasattr(node, "declarations") and node.declarations:
            children.extend(node.declarations)
        if hasattr(node, "statements") and node.statements:
            children.extend(node.statements)
        if hasattr(node, "items") and node.items:  # FunctionExprNode
            children.extend(node.items)
        if hasattr(node, "params") and node.params:
            children.extend(node.params)
        if hasattr(node, "tuple_types") and node.tuple_types:
            children.extend(node.tuple_types)
        if hasattr(node, "else_if_parts") and node.else_if_parts:
            for part in node.else_if_parts:
                if isinstance(part, dict):
                    if "condition" in part:
                        children.append(part["condition"])
                    if "block" in part:
                        children.append(part["block"])
        if hasattr(node, "args") and node.args:  # 函数调用参数
            children.extend(node.args)

        # 检查单个子节点 - 这些应该作为子树展开，不是属性
        single_child_attrs = [
            "body",
            "condition",
            "then_block",
            "else_block",
            "expr",
            "init_expr",
            "array_type",
            "ref_type",
            "left",
            "right",
            "operand",
            "callee",
            "target",  # 赋值目标
            "value",  # 赋值值
            "init",  # 初始化表达式
            "update",  # 更新表达式
            "var_internal_decl",  # 变量内部声明
            "var_type",  # 变量类型
            "assignable_element",  # 赋值元素
            "name_internal",  # 参数名内部
            "param_type",  # 参数类型
            "then_expr_block",  # if表达式的then块
            "else_expr_block",  # if表达式的else块
            "iterable",  # for循环的可迭代对象
            "start_expr",  # 范围开始表达式
            "end_expr",  # 范围结束表达式
        ]

        for attr in single_child_attrs:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child is not None and isinstance(child, ASTNode):
                    children.append(child)

        # 如果有任何子节点，添加折叠指示符和子节点计数
        if children:
            child_count = len(children)
            main_label = f"▶ {main_label} ({child_count})"
        else:
            main_label = f"● {main_label}"  # 叶子节点使用圆点

        # 创建树项
        if parent_item is None:
            # 创建根节点
            item = QTreeWidgetItem([main_label])
            tree_widget.addTopLevelItem(item)
        else:
            # 创建子节点
            item = QTreeWidgetItem(parent_item, [main_label])

        # 设置节点样式
        node_color = self.get_node_color(node_class_name)
        node_category = self.get_node_category(node_class_name)

        # 为节点文本设置颜色，确保在深色背景上可见
        item.setForeground(0, QColor(node_color))

        # 设置节点类型数据，用于CSS选择器
        item.setData(0, Qt.UserRole + 1, node_category)  # 存储节点类别
        item.setData(0, Qt.UserRole + 2, node_class_name)  # 存储节点类名

        # 根据节点类型设置不同的背景和边框效果
        if node_category == "program":
            item.setBackground(0, QColor("#1e40af"))  # 蓝色背景
            item.setData(0, Qt.UserRole, "program")
        elif node_category == "statement":
            if "If" in node_class_name:
                item.setBackground(0, QColor("#7c3aed"))  # 紫色 - 条件语句
                item.setData(0, Qt.UserRole, "conditional")
            elif "While" in node_class_name or "For" in node_class_name:
                item.setBackground(0, QColor("#059669"))  # 绿色 - 循环语句
                item.setData(0, Qt.UserRole, "loop")
            elif "Let" in node_class_name or "Assign" in node_class_name:
                item.setBackground(0, QColor("#dc2626"))  # 红色 - 赋值语句
                item.setData(0, Qt.UserRole, "assignment")
            elif "Return" in node_class_name:
                item.setBackground(0, QColor("#ea580c"))  # 橙色 - 返回语句
                item.setData(0, Qt.UserRole, "return")
            else:
                item.setBackground(0, QColor("#374151"))  # 默认灰色
                item.setData(0, Qt.UserRole, "statement")
        elif node_category == "expression":
            if "Binary" in node_class_name:
                item.setBackground(0, QColor("#0891b2"))  # 青色 - 二元表达式
                item.setData(0, Qt.UserRole, "binary")
            elif "Function" in node_class_name:
                item.setBackground(0, QColor("#7c2d12"))  # 棕色 - 函数相关
                item.setData(0, Qt.UserRole, "function")
            else:
                item.setBackground(0, QColor("#065f46"))  # 深绿色
                item.setData(0, Qt.UserRole, "expression")
        elif node_category == "literal":
            if "Number" in node_class_name:
                item.setBackground(0, QColor("#1e3a8a"))  # 深蓝色 - 数字
                item.setData(0, Qt.UserRole, "number")
            elif "String" in node_class_name:
                item.setBackground(0, QColor("#166534"))  # 深绿色 - 字符串
                item.setData(0, Qt.UserRole, "string")
            elif "Identifier" in node_class_name:
                item.setBackground(0, QColor("#581c87"))  # 深紫色 - 标识符
                item.setData(0, Qt.UserRole, "identifier")
            else:
                item.setBackground(0, QColor("#7c2d12"))  # 棕色
                item.setData(0, Qt.UserRole, "literal")
        elif node_category == "type":
            item.setBackground(0, QColor("#4338ca"))  # 靛蓝色背景
            item.setData(0, Qt.UserRole, "type")
        else:
            item.setBackground(0, QColor("#374151"))  # 默认背景
            item.setData(0, Qt.UserRole, "other")

        # 设置字体 - 根据节点类型和层级调整
        font = QFont("Consolas", 10)  # 使用等宽字体，调小基础字体
        if node_category == "program":
            font.setBold(True)
            font.setPointSize(11)  # 程序节点稍大
        elif node_category in ["statement", "expression"]:
            font.setBold(True)
            font.setPointSize(10)  # 语句和表达式正常大小
        else:
            font.setBold(False)
            font.setPointSize(9)  # 其他节点更小
        item.setFont(0, font)

        # 根据节点深度调整透明度
        parent_count = 0
        temp_parent = parent_item
        while temp_parent is not None:
            parent_count += 1
            temp_parent = temp_parent.parent()

        # 深层节点使用更柔和的颜色
        if parent_count > 2:
            current_color = item.background(0).color()
            current_color.setAlpha(max(100, 255 - parent_count * 30))
            item.setBackground(0, current_color)

        # 收集节点的属性（排除AST子节点）
        attrs = {}
        for key, value in node.__dict__.items():
            if (
                not isinstance(value, list)
                and not key.startswith("_")
                and key not in single_child_attrs
                and key
                not in [
                    "children",
                    "declarations",
                    "statements",
                    "params",
                    "tuple_types",
                    "else_if_parts",
                    "items",
                    "args",
                ]
                and not isinstance(value, ASTNode)
            ):  # 排除AST节点
                attrs[key] = value

        # 添加属性作为子项
        if attrs and len(attrs) > 0:
            # 创建属性分组（添加展开指示符）
            attrs_group = QTreeWidgetItem(item, ["▶ 属性"])
            attrs_group_font = QFont()
            attrs_group_font.setItalic(True)
            attrs_group_font.setBold(True)
            attrs_group_font.setPointSize(9)
            attrs_group.setFont(0, attrs_group_font)
            attrs_group.setForeground(0, QColor("#a0aec0"))  # 更柔和的颜色
            attrs_group.setBackground(0, QColor("#1a202c"))  # 深色背景

            # 添加属性节点
            for k, v in attrs.items():
                if isinstance(v, str) and v:
                    # 如果字符串很长，进行换行处理
                    if len(str(v)) > 30:
                        attr_text = f'{k}:\n  "{v}"'
                    else:
                        attr_text = f'{k}: "{v}"'
                elif v is not None:
                    # 如果值很长，进行换行处理
                    if len(str(v)) > 30:
                        attr_text = f"{k}:\n  {v}"
                    else:
                        attr_text = f"{k}: {v}"
                else:
                    continue

                attrs_item = QTreeWidgetItem(attrs_group, [attr_text])
                # 设置属性节点的样式 - 使用不同颜色区分属性类型
                if isinstance(v, str):
                    attrs_item.setForeground(0, QColor("#68d391"))  # 字符串用绿色
                elif isinstance(v, bool):
                    attrs_item.setForeground(0, QColor("#f6ad55"))  # 布尔值用橙色
                elif isinstance(v, (int, float)):
                    attrs_item.setForeground(0, QColor("#63b3ed"))  # 数字用蓝色
                else:
                    attrs_item.setForeground(0, QColor("#cbd5e0"))  # 其他用灰色

                attrs_item.setBackground(0, QColor("#2d3748"))  # 统一的属性背景
                font = QFont()
                font.setItalic(True)
                font.setPointSize(9)
                attrs_item.setFont(0, font)

        # 如果找到了子节点，则添加它们
        if children and len(children) > 0:
            # 为每个子节点设置位置信息，用于CSS样式控制
            for i, child in enumerate(children):
                if child is not None:  # 确保子节点不为空
                    child_item = self.build_ast_tree(child, tree_widget, item)

                    # 设置子节点的位置属性，用于连接线样式控制
                    if len(children) == 1:
                        # 单个子节点 - 使用L型闭合连接线
                        child_item.setData(0, Qt.UserRole + 3, "single")
                    elif i == 0:
                        # 第一个子节点 - T型连接线（顶部开放）
                        child_item.setData(0, Qt.UserRole + 3, "first")
                    elif i == len(children) - 1:
                        # 最后一个子节点 - L型连接线（底部闭合）
                        child_item.setData(0, Qt.UserRole + 3, "last")
                    else:
                        # 中间的子节点 - 十字型连接线
                        child_item.setData(0, Qt.UserRole + 3, "middle")

                    # 根据位置设置不同的图标前缀
                    current_text = child_item.text(0)
                    if (
                        current_text.startswith("▶ ")
                        or current_text.startswith("▼ ")
                        or current_text.startswith("● ")
                    ):
                        # 移除现有的前缀
                        if current_text.startswith("▶ ") or current_text.startswith(
                            "▼ "
                        ):
                            base_text = current_text[2:]
                            prefix = current_text[:2]
                        else:
                            base_text = current_text[2:]
                            prefix = "● "

                        # 根据位置添加不同的连接线指示符
                        if len(children) == 1:
                            child_item.setText(0, prefix + base_text)  # 保持原有前缀
                        elif i == 0:
                            child_item.setText(0, prefix + base_text)  # 第一个
                        elif i == len(children) - 1:
                            child_item.setText(0, prefix + base_text)  # 最后一个
                        else:
                            child_item.setText(0, prefix + base_text)  # 中间

        return item

    def show_errors_in_output(self, errors):
        """在错误输出框中显示错误信息"""
        # 不清空，而是追加内容
        current_html = self.error_output.toHtml()

        if not errors:
            if not current_html or current_html.strip() == "":
                self.error_output.setPlaceholderText("编译成功，无错误或警告")
            return

        error_text = ""
        for error in errors:
            if error.error_type.startswith("warning_"):
                icon = "⚠️"
                prefix = "警告"
                color = "#f39c12"  # 橙色
            else:
                icon = "❌"
                prefix = "错误"
                color = "#e74c3c"  # 红色

            location = f"第{error.line}行" if error.line else "未知位置"

            # 构建HTML格式的错误信息
            error_line = f'<span style="color: {color};">{icon} {prefix} ({location}): {error.message}</span>'

            if error.suggestion:
                error_line += f'<br><span style="color: #95a5a6; margin-left: 20px;">💡 建议: {error.suggestion}</span>'

            error_text += error_line + "<br><br>"

        # 追加到现有内容
        if current_html and current_html.strip():
            # 如果已有内容，添加分隔线
            existing_content = self.error_output.toHtml()
            new_content = (
                existing_content
                + '<hr style="border: 1px solid #ccc; margin: 10px 0;">'
                + error_text
            )
        else:
            new_content = error_text

        self.error_output.setHtml(new_content)

        # 滚动到底部显示最新内容
        cursor = self.error_output.textCursor()
        cursor.movePosition(cursor.End)
        self.error_output.setTextCursor(cursor)

        # 如果有错误，自动显示错误输出区域
        if errors:
            self.error_output.setMaximumHeight(200)

    def show_error_context_menu(self, position):
        """显示错误输出的右键菜单"""
        menu = QMenu(self)

        clear_action = QAction("清空", self)
        clear_action.triggered.connect(self.error_output.clear)

        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.error_output.copy)

        select_all_action = QAction("全选", self)
        select_all_action.triggered.connect(self.error_output.selectAll)

        menu.addAction(clear_action)
        menu.addSeparator()
        menu.addAction(copy_action)
        menu.addAction(select_all_action)

        menu.exec_(self.error_output.mapToGlobal(position))

    def on_error_double_click(self, event):
        """处理错误输出的双击事件"""
        # 获取点击位置的文本
        cursor = self.error_output.textCursor()
        cursor.select(cursor.LineUnderCursor)
        line_text = cursor.selectedText()

        # 提取行号信息
        import re

        match = re.search(r"第(\d+)行", line_text)
        if match:
            line_number = int(match.group(1))
            # 跳转到代码编辑器的对应行
            self.goto_line(line_number)

    def goto_line(self, line_number):
        """跳转到代码编辑器的指定行"""
        cursor = self.code_editor.textCursor()
        cursor.movePosition(cursor.Start)
        cursor.movePosition(cursor.Down, cursor.MoveAnchor, line_number - 1)
        self.code_editor.setTextCursor(cursor)
        self.code_editor.centerCursor()
        self.code_editor.setFocus()


def load_example_code(gui):
    """加载示例代码到编辑器"""
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test", "example_for_ast.rs"
    )
    if os.path.exists(example_path):
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                gui.code_editor.setPlainText(f.read())
                gui.setWindowTitle(f"Toy Rust Compiler - {example_path}")
        except Exception as e:
            print(f"无法加载示例文件: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 设置全局字体
    setup_application_font(app)

    # 应用现代化一体化主题
    apply_modern_theme(app)

    gui = CompilerGUI()
    gui.show()

    # 加载示例代码
    load_example_code(gui)

    sys.exit(app.exec_())
