@echo off
echo Rust-like 编译器 (批处理启动器)
echo.

if "%~1"=="" (
    echo 使用方法: compile.bat 源文件 [--ir] [--asm]
    echo 选项:
    echo   --ir  : 只生成中间代码
    echo   --asm : 生成汇编代码
    python main_fixed.py
) else (
    python main_fixed.py %*
)
