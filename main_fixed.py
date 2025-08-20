"""
Description  : 适用于单遍编译的Rust-like语言词法分析器 (修复版)
Author       : Hyoung (修复: GitHub Copilot)
Date         : 2025-08-18 18:54:14
LastEditTime : 2025-08-21
FilePath     : \\课程设计\\rust-like-compiler\\main_fixed.py
"""

# main_fixed.py
# 课设主程序入口，组织编译流程，修复了导入问题

import sys
import os

# 添加当前目录到模块搜索路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入编译器相关模块
try:
    # 导入词法分析器
    from lexer import Lexer, TT_DOTDOT, TT_MOD  # 确保导入这两个标记类型

    # 明确使用本地的parser模块，避免与标准库冲突
    sys.modules.pop("parser", None)  # 移除可能已导入的标准库parser模块
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "myparser", os.path.join(current_dir, "parser.py")
    )
    myparser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(myparser)
    Parser, ParseError = myparser.Parser, myparser.ParseError

    # 导入其他编译器组件
    from ir_generator import IRGenerator
    from ir_writer import save_ir_to_file
    from codegen2 import MIPSCodeGenerator

    print("编译器模块导入成功")
except ImportError as e:
    print(f"编译器模块导入错误: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)


def main():
    args = sys.argv[1:]
    test_dir = os.path.join(os.path.dirname(__file__), "test")
    output_dir = os.path.join(test_dir, "output")
    ir_dir = os.path.join(output_dir, "ir")
    asm_dir = os.path.join(output_dir, "asm")
    os.makedirs(ir_dir, exist_ok=True)
    os.makedirs(asm_dir, exist_ok=True)

    if not args:
        print("使用方法: python main.py <源文件路径> [--ir] [--asm]")
        print("选项:")
        print("  --ir  : 只生成中间代码")
        print("  --asm : 生成汇编代码")
        # 寻找测试文件夹中所有的.rs文件
        rs_files = []
        for file in os.listdir(test_dir):
            if file.endswith(".rs"):
                rs_files.append(os.path.join(test_dir, file))
        if rs_files:
            print("\n可用的测试文件:")
            for i, file in enumerate(rs_files):
                print(f"  {i+1}. {os.path.basename(file)}")
        return

    source_path = args[0]
    gen_ir = "--ir" in args
    gen_asm = "--asm" in args

    if not os.path.exists(source_path):
        print(f"错误: 源文件 '{source_path}' 不存在")
        return

    # 设置输出文件路径
    base_name = os.path.basename(source_path)
    name_without_ext = os.path.splitext(base_name)[0]
    ir_path = os.path.join(ir_dir, f"{name_without_ext}.ir")
    asm_path = os.path.join(asm_dir, f"{name_without_ext}.asm")

    try:
        with open(source_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        print(f"正在编译 {base_name}...")

        # 词法分析
        lexer = Lexer(source_code)

        # IR生成器
        irgen = IRGenerator()

        # 语法分析
        parser = Parser(lexer, irgen)

        try:
            # 解析程序
            ast = parser.parse_program()
            print("语法分析成功")

            # 生成IR
            irgen.generate(ast)
            ir = irgen.quads

            # 保存IR到文件
            save_ir_to_file(ir, ir_path)
            print(f"中间代码已保存到 {ir_path}")

            # 如果不是只生成IR，就继续生成汇编代码
            if not gen_ir or gen_asm:
                # MIPS代码生成
                codegen = MIPSCodeGenerator(ir)
                mips_code = codegen.gen_asm()

                # 保存汇编代码到文件
                with open(asm_path, "w", encoding="utf-8") as f:
                    f.write(mips_code)
                print(f"汇编代码已保存到 {asm_path}")

        except ParseError as e:
            print(f"语法错误: {e}")

    except Exception as e:
        print(f"发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
