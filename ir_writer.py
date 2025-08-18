"""
Description  : 适用于单遍编译的Rust-like语言中间代码写入器
Author       : Hyoung
Date         : 2025-08-18 18:56:22
LastEditTime : 2025-08-18 18:56:23
FilePath     : \\课程设计\\rust-like-compiler\\ir_writer.py
"""


def save_ir_to_file(quads, output_file):
    """将中间代码（四元式）保存到文件"""
    with open(output_file, "w", encoding="utf-8") as f:
        for i, quad in enumerate(quads):
            f.write(f"{i}: {quad}\n")
