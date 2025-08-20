# Toy-Rust-Compiler

同济大学编译原理课程设计，类 Rust 编译器

## 📋 项目简介

这是一个基于 Python 实现的类 Rust 语言编译器，支持词法分析、语法分析、语义分析、中间代码生成和 MIPS 汇编代码生成的完整编译流程。项目提供了现代化的图形用户界面，实现了课设要求的编译器功能。

## ✨ 主要特性

### 🔧 编译器核心功能

- **词法分析**：支持 Rust-like 语法的词法单元识别
- **语法分析**：递归下降语法分析器，生成抽象语法树(AST)
- **语义分析**：类型检查、作用域管理、变量声明检查
- **中间代码生成**：生成四元式中间代码
- **目标代码生成**：生成 MIPS 汇编代码

### 🎨 现代化用户界面

- **一体化设计**：无边框窗口，自定义标题栏
- **语法高亮**：代码编辑器支持语法高亮
- **可视化 AST**：树形展示抽象语法树结构
- **实时错误显示**：错误信息面板，支持点击跳转
- **多标签页**：词法分析、语法分析、中间代码、目标代码分离显示

### 💡 支持的语言特性

- 函数定义和调用
- 变量声明（支持 `let` 和 `let mut`）
- 基本数据类型（`i32`, `f32`, `bool`, `char`）
- 数组和切片
- 控制流语句（`if-else`, `while`, `for`, `loop`）
- 表达式计算
- 作用域和变量遮蔽

## 🚀 快速开始

### 环境要求

- Python 3.8+
- PyQt5
- 其他依赖见 `requirements.txt`

### 安装与运行

1. **克隆项目**

```bash
git clone https://github.com/Flesymeb/Toy-Rust-Compiler.git
cd Toy-Rust-Compiler
```

2. **安装依赖**

```bash
pip install PyQt5
# 或使用 conda
conda install pyqt
```

3. **运行编译器**

```bash
python gui.py
```

### 使用方法

1. **编写代码**：在左侧代码编辑器中输入类 Rust 代码
2. **编译运行**：点击"编译"按钮开始编译
3. **查看结果**：
   - **词法分析**：查看词法单元表
   - **语法分析**：查看 AST 语法树
   - **中间代码**：查看四元式中间代码
   - **目标代码**：查看生成的 MIPS 汇编
4. **错误处理**：底部错误面板显示编译错误，点击可跳转到错误位置

## 📁 项目结构

```
rust-like-compiler/
├── gui.py                  # 主界面程序
├── main.py                 # 命令行版本编译器
├── lexer.py                # 词法分析器
├── parser.py               # 语法分析器
├── parser_nodes.py         # AST 节点定义
├── semantic_analyzer.py    # 语义分析器
├── symbol_table.py         # 符号表管理
├── ir_generator.py         # 中间代码生成器
├── codegen2mips.py         # MIPS 代码生成器
├── grammar.txt             # 语法规则文档
├── test/                   # 测试用例目录
│   ├── *.rs               # Rust-like 测试文件
│   └── output/            # 编译输出目录
└── README.md              # 项目说明文档
```

## 🧪 测试用例

项目包含丰富的测试用例，涵盖：

- **基础语法**：变量声明、函数定义
- **控制流**：条件语句、循环语句
- **数据类型**：基本类型、数组操作
- **错误测试**：语法错误、语义错误
- **复杂程序**：综合功能测试

运行测试：

```bash
# 使用 GUI 界面加载 test/ 目录下的 .rs 文件
# 或使用命令行版本
python main.py test/simple_test.rs
```

## 🎯 语法支持示例

```rust
fn main() {
    let mut x: i32 = 10;
    let y: i32 = 20;

    if x < y {
        println!("x is less than y");
    }

    let arr: [i32; 3] = [1, 2, 3];
    for i in 0..3 {
        println!("{}", arr[i]);
    }
}

fn add(a: i32, b: i32) -> i32 {
    return a + b;
}
```

## 📚 相关文档

- **课程设计报告**：详细的设计思路和实现方案
- **语法规则文档**：`grammar.txt` - 完整的 BNF 语法定义
- **测试文档**：测试用例说明和预期结果

_同济大学编译原理课程设计 © 2025_
