fn main() {
    let x = 42;
    let y: i32;          // 未初始化变量
    x = 10;              // 对不可变变量赋值 (错误)
    z = 5;               // 使用未声明变量 (错误)
    
    // 类型不匹配
    let mut a: i32 = "hello";  // 错误：字符串赋值给整数
}

fn test() -> i32 {
    // 缺少返回语句 (错误)
}

fn invalid_call() {
    add(1, 2, 3);        // 错误：参数数量不匹配
    unknown_func();      // 错误：调用未定义函数
}
