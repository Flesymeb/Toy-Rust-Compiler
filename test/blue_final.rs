// 测试组别5：循环结构 (5.2, 5.3, 5.4)
fn test_group5() {
    // 5.2 for循环
    let mut sum1 = 0;
    for mut i in 1..10 {
        sum1 = sum1 + i;
    }
    
    // 5.3 loop循环 和 5.4 break/continue
    let mut sum2 = 0;
    let mut i = 0;
    loop {
        i = i + 1;
        if i > 10 {
            break;
        }
        if i == 5 {
            continue;
        }
        sum2 = sum2 + i;
    }
    
    return;
}

// 测试组别7：表达式块 (7.1, 7.2, 7.3)
fn test_group7(mut x:i32, mut y:i32) -> i32 {
    // 7.1 函数表达式块
    let mut z = {
        let mut t = x*x + x;
        t = t + x*y;
        t;
    };
    
    // 7.3 选择表达式
    let mut result = if z > 10 {
        z - 5;
    } else {
        z + 5;
    };
    
    // 7.2 函数表达式块作为函数体
    // (隐式返回最后一个表达式)
    return result;
}

fn main() {
    test_group5();
    let result = test_group7(3, 4);
    return;
}
