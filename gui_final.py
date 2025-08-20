"""
Description  : Rust-like语言编译器GUI界面 (修复版 - 左右布局与树形AST)
Date         : 2025-08-19
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
    from codegen2 import MIPSCodeGenerator
    from parser_nodes import ASTNode  # 导入ASTNode基类

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
        font = QFont("Consolas", 12)
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
            lineColor = QColor(50, 52, 64)  # 当前行高亮颜色

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


# 应用暗色主题
def apply_dark_theme(app):
    app.setStyle(QStyleFactory.create("Fusion"))

    dark_palette = QPalette()
    dark_palette.setColor(QPalette.Window, QColor(40, 42, 54))
    dark_palette.setColor(QPalette.WindowText, QColor(248, 248, 242))
    dark_palette.setColor(QPalette.Base, QColor(30, 31, 41))
    dark_palette.setColor(QPalette.AlternateBase, QColor(50, 52, 64))
    dark_palette.setColor(QPalette.ToolTipBase, QColor(248, 248, 242))
    dark_palette.setColor(QPalette.ToolTipText, QColor(248, 248, 242))
    dark_palette.setColor(QPalette.Text, QColor(248, 248, 242))
    dark_palette.setColor(QPalette.Button, QColor(59, 60, 76))
    dark_palette.setColor(QPalette.ButtonText, QColor(248, 248, 242))
    dark_palette.setColor(QPalette.BrightText, Qt.red)
    dark_palette.setColor(QPalette.Link, QColor(80, 250, 123))
    dark_palette.setColor(QPalette.Highlight, QColor(68, 71, 90))
    dark_palette.setColor(QPalette.HighlightedText, QColor(248, 248, 242))

    app.setPalette(dark_palette)

    app.setStyleSheet(
        """
        QToolTip { 
            color: #f8f8f2; 
            background-color: #282a36;
            border: 1px solid #6272a4;
        }
        QTableWidget {
            gridline-color: #44475a;
            selection-background-color: #44475a;
        }
        QHeaderView::section {
            background-color: #44475a;
            padding: 4px;
            border: 1px solid #6272a4;
        }
        QTabBar::tab {
            background: #282a36;
            border: 1px solid #44475a;
            padding: 5px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background: #44475a;
        }
        QTabWidget::pane {
            border: 1px solid #44475a;
        }
        QSplitter::handle {
            background-color: #44475a;
        }
        QScrollBar:vertical {
            border: none;
            background: #282a36;
            width: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:vertical {
            background: #44475a;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar:horizontal {
            border: none;
            background: #282a36;
            height: 10px;
            margin: 0px 0px 0px 0px;
        }
        QScrollBar::handle:horizontal {
            background: #44475a;
            min-width: 20px;
            border-radius: 5px;
        }
        QTreeWidget {
            background-color: #2d2d2d;
            color: #ffffff;  /* 明亮的白色文本 */
            border: 1px solid #3d3d3d;
            font-size: 10pt;
        }
        QTreeWidget::item {
            color: #ffffff;  /* 确保所有项目都有白色文本 */
            padding: 4px;
            border-bottom: 1px dotted #333333;
        }
        QTreeWidget::item:selected {
            background-color: #4d4d4d;  /* 更明显的选中背景色 */
            color: #ffffff;
        }
        QTreeWidget::item:hover {
            background-color: #353535;  /* 轻微高亮的悬停效果 */
        }
    """
    )


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
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Rust-like语言编译器")
        self.setGeometry(100, 100, 1200, 800)

        # 连接树节点展开/折叠信号
        self.ast_tree_expanded_items = set()  # 用于跟踪展开的节点

        # 设置状态栏样式
        self.statusBar().setStyleSheet(
            """
            QStatusBar {
                background-color: #282a36;
                color: #f8f8f2;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 3px;
                border-top: 1px solid #44475a;
            }
        """
        )
        self.statusBar().showMessage("就绪")

        # 创建主分割器 - 水平分割
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)

        # 创建源代码编辑器 - 使用带行号的编辑器
        self.code_editor = CodeEditor()
        self.code_editor.setPlaceholderText("在这里输入Rust-like代码...")

        # 为源代码编辑器设置语法高亮
        self.rust_highlighter = RustHighlighter(self.code_editor.document())

        # 创建按钮区域
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)

        self.load_button = QPushButton("加载文件")
        self.load_button.clicked.connect(self.load_file)

        self.save_button = QPushButton("保存文件")
        self.save_button.clicked.connect(self.save_file)

        self.compile_button = QPushButton("编译")
        self.compile_button.clicked.connect(self.compile_code)

        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.compile_button)

        # 创建左侧区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(self.code_editor)
        left_layout.addWidget(button_widget)

        # 创建结果标签页
        self.result_tabs = QTabWidget()

        # 创建词法分析结果表格
        self.token_table = QTableWidget()
        self.token_table.setColumnCount(4)
        self.token_table.setHorizontalHeaderLabels(["类型", "值", "行", "列"])
        self.token_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.token_table.setWordWrap(False)
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

        # 创建语法分析结果（仅保留树形视图）
        self.ast_container = QWidget()
        ast_layout = QVBoxLayout(self.ast_container)

        # 树形视图 - 语法分析可视化
        self.ast_tree = QTreeWidget()
        self.ast_tree.setHeaderLabels(["语法分析可视化 (AST)"])
        self.ast_tree.setColumnCount(1)
        self.ast_tree.setAlternatingRowColors(False)  # 不使用交替行颜色
        self.ast_tree.setAnimated(True)  # 使用动画效果
        self.ast_tree.setIndentation(20)  # 设置缩进
        # 启用水平滚动，禁用自动换行
        self.ast_tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)
        self.ast_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.ast_tree.setWordWrap(False)
        self.ast_tree.header().setStretchLastSection(False)  # 防止最后一列自动拉伸
        self.ast_tree.header().setDefaultSectionSize(800)  # 设置更宽的默认列宽
        self.ast_tree.header().setStretchLastSection(False)  # 不自动拉伸最后一列
        self.ast_tree.setHorizontalScrollMode(QTreeWidget.ScrollPerPixel)  # 平滑滚动
        self.ast_tree.setWordWrap(False)  # 禁用自动换行
        self.ast_tree.setTextElideMode(Qt.ElideNone)  # 不省略文本
        self.ast_tree.setRootIsDecorated(True)  # 显示展开/折叠控件
        self.ast_tree.setExpandsOnDoubleClick(True)  # 双击展开/折叠

        # 连接树节点展开/折叠信号
        self.ast_tree.itemExpanded.connect(self.on_item_expanded)
        self.ast_tree.itemCollapsed.connect(self.on_item_collapsed)

        # 设置树形视图样式
        self.ast_tree.setStyleSheet(
            """
            QTreeWidget {
                background-color: #1e1e1e;
                border: 1px solid #444444;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                color: #f8f8f2;
                outline: none;
            }
            QTreeWidget::item {
                padding: 2px 4px;
                border: none;
                color: #f8f8f2;
            }
            QTreeWidget::item:selected {
                background-color: #3d3d3d;
                border: 1px solid #6ca7fc;
                border-radius: 2px;
            }
            QTreeWidget::item:hover {
                background-color: #2d2d2d;
            }
            /* 树的分支线条 */
            QTreeWidget::branch {
                background-color: transparent;
            }
            QTreeWidget::branch:has-siblings:!adjoins-item {
                border-left: 1px solid #5a7db5;
            }
            QTreeWidget::branch:has-siblings:adjoins-item {
                border-left: 1px solid #5a7db5;
            }
            QTreeWidget::branch:!has-children:!has-siblings:adjoins-item {
                border-left: 1px solid #5a7db5;
            }
            /* 树形视图表头 */
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #f8f8f2;
                border: 1px solid #444444;
                padding: 6px;
                font-weight: bold;
            }
        """
        )

        # 创建顶部控制栏
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(5, 5, 5, 5)

        # 添加展开/折叠按钮
        expand_all_btn = QPushButton("全部展开")
        collapse_all_btn = QPushButton("全部折叠")

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

        # 连接按钮信号
        expand_all_btn.clicked.connect(self.expand_ast_tree)
        collapse_all_btn.clicked.connect(self.collapse_ast_tree)

        # 添加弹簧和按钮到顶部布局
        top_layout.addStretch()
        top_layout.addWidget(expand_all_btn)
        top_layout.addWidget(collapse_all_btn)

        # 添加到主布局
        ast_layout.addWidget(top_widget)
        ast_layout.addWidget(self.ast_tree, 1)

        # 创建中间代码结果表格
        self.ir_table = QTableWidget()
        self.ir_table.setColumnCount(4)
        self.ir_table.setHorizontalHeaderLabels(
            ["运算符", "操作数1", "操作数2", "结果"]
        )
        self.ir_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.ir_table.setWordWrap(False)
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

        # 创建目标代码结果
        self.target_code = QTextEdit()
        self.target_code.setReadOnly(True)
        self.target_code.setFont(QFont("Consolas", 12))
        self.target_code.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.target_code.setLineWrapMode(QTextEdit.NoWrap)  # 禁用自动换行
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
                padding: 8px 16px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: #44475a;
            }
        """
        )

        # 添加标签页
        self.result_tabs.addTab(self.token_table, "词法分析")
        self.result_tabs.addTab(self.ast_container, "语法分析")
        self.result_tabs.addTab(self.ir_table, "中间代码")
        self.result_tabs.addTab(self.target_code, "目标代码")

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
                self.setWindowTitle(f"Rust-like编译器 - {file_path}")
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
                self.setWindowTitle(f"Rust-like编译器 - {file_path}")
                QMessageBox.information(self, "成功", f"成功保存文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")

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

            # 编译完成
            self.statusBar().showMessage("编译完成")
            QMessageBox.information(self, "成功", "编译完成")

        except myparser.ParseError as e:
            error_msg = f"语法错误: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "语法错误", error_msg)
        except Exception as e:
            error_msg = f"编译过程中发生错误: {str(e)}"
            self.statusBar().showMessage(error_msg)
            QMessageBox.critical(self, "编译错误", error_msg)

            import traceback

            traceback.print_exc()  # 在控制台打印堆栈跟踪信息

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
            item.setText(0, "▼ " + text[2:])

    def on_item_collapsed(self, item):
        """处理节点折叠事件"""
        text = item.text(0)
        if text.startswith("▼ "):
            item.setText(0, "▶ " + text[2:])

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

        # 创建主要标签 - 添加展开/折叠指示符
        main_label = node_class_name.replace("Node", "")

        # 检查是否有子节点
        has_children = False

        # 提前收集所有子节点
        children = []

        # 检查集合类型的子节点
        if hasattr(node, "children") and node.children:
            children.extend(node.children)
        if hasattr(node, "declarations") and node.declarations:
            children.extend(node.declarations)
        if hasattr(node, "statements") and node.statements:
            children.extend(node.statements)
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

        # 检查单个子节点
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
        ]

        for attr in single_child_attrs:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if isinstance(child, ASTNode):
                    children.append(child)

        # 如果有任何子节点，添加折叠指示符
        if children:
            has_children = True
            main_label = "▶ " + main_label

        # 检查可能作为单个子节点的属性
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
        ]

        for attr in single_child_attrs:
            if hasattr(node, attr) and getattr(node, attr) is not None:
                child = getattr(node, attr)
                if isinstance(child, ASTNode):
                    has_children = True
                    break

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

        # 为节点文本设置颜色，确保在深色背景上可见
        item.setForeground(0, QColor(node_color))

        # 获取节点类别
        node_category = self.get_node_category(node_class_name)

        # 设置节点背景 - 简洁的风格
        item.setBackground(0, QColor("#2d2d2d"))

        # 设置字体 - 节点名称加粗
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)  # 适当增大字体
        item.setFont(0, font)

        # 收集节点的属性
        attrs = {}
        for key, value in node.__dict__.items():
            if not isinstance(value, list) and not key.startswith("_"):
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
            attrs_group.setForeground(0, QColor("#8db1b6"))  # 使用柔和的青灰色

            # 添加属性节点
            for k, v in attrs.items():
                if isinstance(v, str) and v:
                    attr_text = f'{k}: "{v}"'
                elif v is not None:
                    attr_text = f"{k}: {v}"
                else:
                    continue

                attrs_item = QTreeWidgetItem(attrs_group, [attr_text])
                # 设置属性节点的样式 - 使用柔和的颜色
                attrs_item.setForeground(0, QColor("#a4b4c4"))  # 亮灰色
                font = QFont()
                font.setItalic(True)
                font.setPointSize(9)
                attrs_item.setFont(0, font)

        # children列表已经在之前收集完成，直接使用

        # 如果找到了子节点，则添加它们
        if children and len(children) > 0:
            # 根据节点类型选择适当的标签
            label = "子节点"
            if hasattr(node, "statements"):
                label = "语句"
            elif hasattr(node, "declarations"):
                label = "声明"
            elif hasattr(node, "params"):
                label = "参数"
            elif hasattr(node, "else_if_parts"):
                label = "else-if分支"

            # 添加展开/折叠指示符
            label = "▶ " + label

            # 创建子节点分组
            children_item = QTreeWidgetItem(item, [label])
            children_font = QFont()
            children_font.setItalic(True)
            children_font.setBold(True)
            children_font.setPointSize(9)
            children_item.setFont(0, children_font)
            children_item.setForeground(0, QColor("#8db1b6"))  # 使用和属性组相同的颜色

            # 添加子节点
            for child in children:
                if child is not None:  # 确保子节点不为空
                    self.build_ast_tree(child, tree_widget, children_item)

        return item


def load_example_code(gui):
    """加载示例代码到编辑器"""
    example_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "test", "example_for_ast.rs"
    )
    if os.path.exists(example_path):
        try:
            with open(example_path, "r", encoding="utf-8") as f:
                gui.code_editor.setPlainText(f.read())
                gui.setWindowTitle(f"Rust-like编译器 - {example_path}")
        except Exception as e:
            print(f"无法加载示例文件: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 应用暗色主题
    apply_dark_theme(app)

    gui = CompilerGUI()
    gui.show()

    # 加载示例代码
    load_example_code(gui)

    sys.exit(app.exec_())
