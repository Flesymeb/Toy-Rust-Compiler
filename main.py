"""
Description  : 适用于单遍编译的Rust-like语言词法分析器
Author       : Hyoung
Date         : 2025-08-18 18:54:14
LastEditTime : 2025-08-18 18:55:39
FilePath     : \\课程设计\\rust-like-compiler\\main.py
"""

# main.py
# 课设主程序入口，组织编译流程

from lexer import Lexer
from parser import Parser, ParseError
from ir_generator import IRGenerator
from ir_writer import save_ir_to_file

# from codegen import X86AsmGenerator
from codegen2 import MIPSCodeGenerator


def main():
    import sys
    import os

    args = sys.argv[1:]
    test_dir = os.path.join(os.path.dirname(__file__), "test")
    output_dir = os.path.join(test_dir, "output")
    ir_dir = os.path.join(output_dir, "ir")
    asm_dir = os.path.join(output_dir, "asm")
    os.makedirs(ir_dir, exist_ok=True)
    os.makedirs(asm_dir, exist_ok=True)

    def run_one_rs(src_file, ir_file, show_name=True):
        fname = os.path.basename(src_file)
        if show_name:
            print(f"\n==================== 测试用例: {fname} ====================")
        with open(src_file, "r", encoding="utf-8") as f:
            code = f.read()
        try:
            lexer = Lexer(code)
            irgen = IRGenerator()
            parser = Parser(lexer, irgen)
            ast = parser.parse()
            print("--- AST ---")
            print(ast)
            print("\n--- IR (四元式) ---")
            for quad in irgen.quads:
                print(quad)
            # 保存中间代码
            ir_file_real = os.path.join(ir_dir, os.path.basename(ir_file))
            save_ir_to_file(irgen.quads, ir_file_real)
            print(f"\n中间代码已保存到: output/ir/{os.path.basename(ir_file)}")

            print("\n--- 汇编代码 ---")
            asm_file = os.path.join(
                asm_dir, os.path.basename(ir_file).rsplit(".", 1)[0] + ".asm"
            )
            asm_gen = MIPSCodeGenerator(irgen.quads)
            with open(asm_file, "w") as f:
                f.write(asm_gen.gen_asm())
            print(f"汇编代码已保存到: output/asm/{os.path.basename(asm_file)}")

        except ParseError as e:
            print(f"[语法错误] {e}")
        except Exception as e:
            print(f"[其他错误] {e}")

    if args and args[0].endswith(".rs"):
        # 指定单个rs文件
        src_file = args[0]
        if not os.path.isabs(src_file):
            src_file = os.path.abspath(src_file)
        fname = os.path.basename(src_file)
        ir_file = fname.rsplit(".", 1)[0] + ".ir"
        run_one_rs(src_file, ir_file, show_name=False)
    else:
        # 批量测试test目录
        rs_files = [f for f in os.listdir(test_dir) if f.endswith(".rs")]
        if not rs_files:
            print("test 目录下没有 .rs 测试文件！")
            return
        for fname in sorted(rs_files):
            src_file = os.path.join(test_dir, fname)
            ir_file = fname.rsplit(".", 1)[0] + ".ir"
            run_one_rs(src_file, ir_file)


if __name__ == "__main__":
    main()
