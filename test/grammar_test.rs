// 基于PDF语法规则的测试代码
// 测试1.1基础程序结构

fn main() {
    ;
}

// 测试1.4函数输入
fn test_fn(mut x: i32) {
    return;
}

// 测试1.5函数输出
fn add(mut a: i32, mut b: i32) -> i32 {
    return a + b;
}

// 测试2.1变量声明
fn var_test() {
    let mut x: i32;
    let y;
}

// 测试2.2赋值语句
fn assign_test() {
    let mut x: i32;
    x = 42;
}

// 测试2.3变量声明赋值
fn declare_assign() {
    let mut x: i32 = 10;
    let y = 20;
}

// 测试3.1基本表达式
fn expr_test() {
    42;
    x;
    (1 + 2);
}

// 测试3.2计算和比较
fn calc_test() {
    1 + 2 * 3;
    x < y;
    a == b;
}

// 测试3.3函数调用
fn call_test() {
    test_fn(42);
    add(1, 2);
}

// 测试4.1选择结构
fn if_test() {
    if x > 0 {
        ;
    }
    
    if y < 10 {
        ;
    } else {
        ;
    }
}

// 测试5.1 while循环
fn while_test() {
    while x > 0 {
        x = x - 1;
    }
}

// 测试5.2 for循环
fn for_test() {
    for mut i in 0..10 {
        ;
    }
}

// 测试5.3 loop循环
fn loop_test() {
    loop {
        break;
    }
}

// 测试5.4 break和continue
fn control_test() {
    while true {
        continue;
        break;
    }
}
