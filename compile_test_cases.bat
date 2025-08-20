@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
echo ========================================
echo    Toy-Rust-like-Compiler 测试套件
echo ========================================
echo.

if "%~1"=="--help" (
    echo 使用方法:
    echo   compile_test_cases.bat                  - 测试所有样例
    echo   compile_test_cases.bat filename.rs     - 测试单个文件
    echo   compile_test_cases.bat --green         - 只测试green系列（正确样例）
    echo   compile_test_cases.bat --blue          - 只测试blue系列（复杂样例）
    echo   compile_test_cases.bat --error         - 只测试error系列（错误样例）
    echo   compile_test_cases.bat --help          - 显示帮助信息
    echo.
    exit /b 0
)

if not exist "test\" (
    echo 错误：test 目录不存在！
    exit /b 1
)

set total_tests=0
set passed_tests=0
set failed_tests=0

echo 开始编译测试...
echo.

REM 单个文件测试
if not "%~1"=="" if not "%~1"=="--green" if not "%~1"=="--blue" if not "%~1"=="--error" (
    if exist "test\%~1" (
        echo 测试文件: %~1
        python main.py "test\%~1"
        echo.
    ) else (
        echo 错误：文件 test\%~1 不存在！
    )
    exit /b 0
)

REM 测试分类
set test_pattern=*.rs
if "%~1"=="--green" set test_pattern=green_*.rs
if "%~1"=="--blue" set test_pattern=blue_*.rs
if "%~1"=="--error" set test_pattern=error_*.rs

echo 测试模式: !test_pattern!
echo ----------------------------------------

for %%f in (test\!test_pattern!) do (
    set /a total_tests+=1
    echo [测试 !total_tests!] 编译文件: %%~nxf
    
    python main.py "%%f" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [✓] 成功 - %%~nxf
        set /a passed_tests+=1
    ) else (
        echo [✗] 失败 - %%~nxf
        set /a failed_tests+=1
    )
    echo.
)

REM 如果没有指定模式，测试所有其他文件
if "%~1"=="" (
    for %%f in (test\simple_test.rs test\minimal_test.rs test\grammar_test.rs test\example_for_ast.rs test\test_new_features.rs test\variable_shadow_test.rs) do (
        if exist "%%f" (
            set /a total_tests+=1
            echo [测试 !total_tests!] 编译文件: %%~nxf
            
            python main.py "%%f" >nul 2>&1
            if !errorlevel! equ 0 (
                echo [✓] 成功 - %%~nxf
                set /a passed_tests+=1
            ) else (
                echo [✗] 失败 - %%~nxf
                set /a failed_tests+=1
            )
            echo.
        )
    )
)

echo ========================================
echo              测试结果汇总
echo ========================================
echo 总测试数: !total_tests!
echo 成功数量: !passed_tests!
echo 失败数量: !failed_tests!

if !failed_tests! equ 0 (
    echo 🎉 所有测试都通过了！
) else (
    echo ⚠️ 有 !failed_tests! 个测试失败
)

echo ========================================
echo.

REM 询问是否查看详细结果
set /p choice="是否查看某个测试文件的详细输出？(输入文件名或直接回车跳过): "
if not "!choice!"=="" (
    if exist "test\!choice!" (
        echo.
        echo 详细输出 - !choice!:
        echo ----------------------------------------
        python main.py "test\!choice!"
    ) else (
        echo 文件不存在: test\!choice!
    )
)

echo.
echo 测试完成！
