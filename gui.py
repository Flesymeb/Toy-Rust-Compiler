"""
Description  : Rust-like语言编译器GUI界面
Date         : 2025-08-19
"""

import sys
import os
from PyQt5.QtWidgets import (
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
    QHeaderView,
    QLabel,
)
from PyQt5.QtGui import QPainter, QIcon, QPixmap, QColor, QPen, QFont
from PyQt5.QtCore import Qt, QSize

# 导入编译器相关模块
from lexer import Lexer, TT_EOF
from parser import Parser, ParseError
from ir_generator import IRGenerator
from codegen2 import MIPSCodeGenerator


class CompilerGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 设置窗口属性
        self.setWindowTitle("Rust-like 编译器")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中心部件
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # 创建主布局
        self.main_layout = QVBoxLayout(self.central_widget)

        # 创建水平分割器
        self.splitter = QSplitter(Qt.Horizontal)

        # 创建左侧编辑区域
        self.editor_widget = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_widget)

        # 添加文件操作按钮
        self.file_buttons_layout = QHBoxLayout()

        self.load_button = QPushButton("加载文件")
        self.load_button.clicked.connect(self.load_file)
        self.file_buttons_layout.addWidget(self.load_button)

        self.save_button = QPushButton("保存文件")
        self.save_button.clicked.connect(self.save_file)
        self.file_buttons_layout.addWidget(self.save_button)

        self.editor_layout.addLayout(self.file_buttons_layout)

        # 添加源代码编辑区
        self.source_label = QLabel("源代码:")
        self.editor_layout.addWidget(self.source_label)

        self.source_editor = QTextEdit()
        self.source_editor.setPlaceholderText("在此输入 Rust-like 代码...")
        self.editor_layout.addWidget(self.source_editor)

        # 添加编译按钮
        self.compile_button = QPushButton("编译")
        self.compile_button.clicked.connect(self.compile_code)
        self.compile_button.setMinimumHeight(40)
        self.editor_layout.addWidget(self.compile_button)

        # 创建右侧输出区域
        self.output_widget = QTabWidget()

        # 创建词法分析输出页
        self.lexer_tab = QWidget()
        self.lexer_layout = QVBoxLayout(self.lexer_tab)
        self.lexer_output = QTableWidget()
        self.lexer_output.setColumnCount(3)
        self.lexer_output.setHorizontalHeaderLabels(["类型", "值", "位置"])
        self.lexer_output.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.lexer_layout.addWidget(self.lexer_output)
        self.output_widget.addTab(self.lexer_tab, "词法分析")

        # 创建语法分析输出页
        self.parser_tab = QWidget()
        self.parser_layout = QVBoxLayout(self.parser_tab)
        self.parser_output = QTextEdit()
        self.parser_output.setReadOnly(True)
        self.parser_layout.addWidget(self.parser_output)
        self.output_widget.addTab(self.parser_tab, "语法分析")

        # 创建IR输出页
        self.ir_tab = QWidget()
        self.ir_layout = QVBoxLayout(self.ir_tab)
        self.ir_output = QTableWidget()
        self.ir_output.setColumnCount(4)
        self.ir_output.setHorizontalHeaderLabels(["操作", "参数1", "参数2", "结果"])
        self.ir_output.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ir_layout.addWidget(self.ir_output)

        # 添加IR保存按钮
        self.save_ir_button = QPushButton("保存IR代码")
        self.save_ir_button.clicked.connect(self.save_ir)
        self.ir_layout.addWidget(self.save_ir_button)

        self.output_widget.addTab(self.ir_tab, "中间代码")

        # 创建汇编输出页
        self.asm_tab = QWidget()
        self.asm_layout = QVBoxLayout(self.asm_tab)
        self.asm_output = QTextEdit()
        self.asm_output.setReadOnly(True)
        self.asm_layout.addWidget(self.asm_output)

        # 添加汇编保存按钮
        self.save_asm_button = QPushButton("保存汇编代码")
        self.save_asm_button.clicked.connect(self.save_asm)
        self.asm_layout.addWidget(self.save_asm_button)

        self.output_widget.addTab(self.asm_tab, "汇编代码")

        # 添加部件到分割器
        self.splitter.addWidget(self.editor_widget)
        self.splitter.addWidget(self.output_widget)
        self.splitter.setSizes([400, 800])

        # 添加分割器到主布局
        self.main_layout.addWidget(self.splitter)

        # 初始化存储编译结果的变量
        self.tokens = []
        self.ast = None
        self.ir_quads = []
        self.asm_code = ""

        # 设置示例代码
        self.set_example_code()

    def set_example_code(self):
        """设置示例代码"""
        example_code = """fn main() {
    let mut i: i32 = 0;
    let mut sum: i32 = 0;
    
    while i < 10 {
        i = i + 1;
        if i % 2 == 0 {
            continue;
        }
        sum = sum + i;
    }
}
"""
        self.source_editor.setText(example_code)

    def load_file(self):
        """加载源代码文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开源代码文件", "", "Rust 文件 (*.rs);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    self.source_editor.setText(file.read())
                self.statusBar().showMessage(f"已加载文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件: {str(e)}")

    def save_file(self):
        """保存源代码到文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存源代码", "", "Rust 文件 (*.rs);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.source_editor.toPlainText())
                self.statusBar().showMessage(f"已保存到文件: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存文件: {str(e)}")

    def compile_code(self):
        """编译源代码"""
        source_code = self.source_editor.toPlainText()

        if not source_code.strip():
            QMessageBox.warning(self, "警告", "请输入源代码")
            return

        try:
            # 清空所有输出
            self.clear_outputs()

            # 1. 词法分析
            self.statusBar().showMessage("正在进行词法分析...")
            lexer = Lexer(source_code)
            self.tokens = lexer.tokenize()
            self.display_tokens()

            # 2. 语法分析
            self.statusBar().showMessage("正在进行语法分析...")
            irgen = IRGenerator()
            parser = Parser(lexer, irgen)
            self.ast = parser.parse()
            self.display_ast()

            # 3. 中间代码生成
            self.statusBar().showMessage("正在生成中间代码...")
            self.ir_quads = irgen.quads
            self.display_ir()

            # 4. 生成目标代码
            self.statusBar().showMessage("正在生成汇编代码...")
            code_gen = MIPSCodeGenerator(irgen.quads)
            self.asm_code = code_gen.gen_asm()
            self.display_asm()

            self.statusBar().showMessage("编译完成")
            QMessageBox.information(self, "成功", "编译完成！")

        except ParseError as e:
            self.statusBar().showMessage(f"语法错误: {str(e)}")
            QMessageBox.warning(self, "语法错误", str(e))
        except Exception as e:
            self.statusBar().showMessage(f"编译错误: {str(e)}")
            QMessageBox.critical(self, "编译错误", f"编译过程中发生错误:\n{str(e)}")
            import traceback

            print(traceback.format_exc())

    def clear_outputs(self):
        """清空所有输出"""
        self.lexer_output.setRowCount(0)
        self.parser_output.clear()
        self.ir_output.setRowCount(0)
        self.asm_output.clear()

    def display_tokens(self):
        """显示词法分析结果"""
        self.lexer_output.setRowCount(0)

        for token in self.tokens:
            # 不显示 EOF 标记
            if token.type == TT_EOF:
                continue

            row = self.lexer_output.rowCount()
            self.lexer_output.insertRow(row)

            # 设置类型
            type_item = QTableWidgetItem(token.type)
            self.lexer_output.setItem(row, 0, type_item)

            # 设置值
            value_item = QTableWidgetItem(str(token.value))
            self.lexer_output.setItem(row, 1, value_item)

            # 设置位置
            pos_item = QTableWidgetItem(f"L{token.line}C{token.column}")
            self.lexer_output.setItem(row, 2, pos_item)

        self.output_widget.setCurrentIndex(0)  # 切换到词法分析选项卡

    def display_ast(self):
        """显示语法分析结果（AST）"""
        self.parser_output.clear()
        if self.ast:
            self.parser_output.setText(str(self.ast))

    def display_ir(self):
        """显示中间代码（IR）"""
        self.ir_output.setRowCount(0)

        for i, quad in enumerate(self.ir_quads):
            row = self.ir_output.rowCount()
            self.ir_output.insertRow(row)

            # 操作
            op_item = QTableWidgetItem(str(quad.op))
            self.ir_output.setItem(row, 0, op_item)

            # 参数1
            arg1_item = QTableWidgetItem(
                str(quad.arg1) if quad.arg1 is not None else ""
            )
            self.ir_output.setItem(row, 1, arg1_item)

            # 参数2
            arg2_item = QTableWidgetItem(
                str(quad.arg2) if quad.arg2 is not None else ""
            )
            self.ir_output.setItem(row, 2, arg2_item)

            # 结果
            result_item = QTableWidgetItem(
                str(quad.result) if quad.result is not None else ""
            )
            self.ir_output.setItem(row, 3, result_item)

    def display_asm(self):
        """显示汇编代码"""
        self.asm_output.clear()
        if self.asm_code:
            self.asm_output.setText(self.asm_code)

    def save_ir(self):
        """保存中间代码到文件"""
        if not self.ir_quads:
            QMessageBox.warning(self, "警告", "没有可保存的中间代码")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存中间代码", "", "IR 文件 (*.ir);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    for quad in self.ir_quads:
                        file.write(f"{quad}\n")
                self.statusBar().showMessage(f"中间代码已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存中间代码: {str(e)}")

    def save_asm(self):
        """保存汇编代码到文件"""
        if not self.asm_code:
            QMessageBox.warning(self, "警告", "没有可保存的汇编代码")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存汇编代码", "", "汇编文件 (*.asm);;所有文件 (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(self.asm_code)
                self.statusBar().showMessage(f"汇编代码已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法保存汇编代码: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CompilerGUI()
    window.show()
    sys.exit(app.exec_())
