// 测试7.2 函数表达式块作为函数体
fn program_7_2(mut x:i32, mut y:i32) -> i32 {
    let mut t = x*x + x;
    t = t + x*y;
    return t;
}
