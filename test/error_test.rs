// Rust-like语言测试文件 - 包含各种错误
// 用于测试语义分析器的错误检测能力

fn main() -> i32 {
    // 正确的变量声明
    let x: i32 = 10;
    let mut y: i32 = 20;
    
    // 错误1: 重复定义
    let x: i32 = 30;  // 错误：重复定义变量x
    
    // 错误2: 使用未声明的变量
    let z = undefined_var;  // 错误：undefined_var未声明
    
    // 错误3: 对不可变变量赋值
    x = 50;  // 错误：x是不可变的
    
    // 正确的可变变量赋值
    y = 100;
    
    // 错误4: 类型不匹配
    let flag: bool = 42;  // 错误：将i32赋值给bool
    
    // 错误5: 条件类型错误
    if x {  // 错误：if条件必须是bool类型
        y = 200;
    }
    
    // 正确的条件
    if x > y {
        y = x;
    }
    
    // 错误6: 返回类型不匹配
    return true;  // 错误：函数声明返回i32，但返回bool
}

// 错误7: 函数重复定义
fn main() -> bool {  // 错误：重复定义main函数
    return false;
}

// 正确的函数定义
fn add(a: i32, b: i32) -> i32 {
    return a + b;
}

fn test_function_calls() -> i32 {
    // 错误8: 调用未定义的函数
    let result1 = undefined_function(10);  // 错误：函数未定义
    
    // 错误9: 函数参数数量不匹配
    let result2 = add(10);  // 错误：add函数需要2个参数，只提供了1个
    let result3 = add(10, 20, 30);  // 错误：add函数需要2个参数，提供了3个
    
    // 正确的函数调用
    let result4 = add(10, 20);
    
    return result4;
}
