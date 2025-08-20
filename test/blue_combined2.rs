// 综合测试蓝色组
fn main() {
    // 测试2.3 变量声明赋值
    let mut a:i32 = 1;
    let mut b = 2;
    
    // 测试5.3 loop循环和5.4 break/continue
    let mut i = 0;
    loop {
        i = i + 1;
        if i > 10 {
            break;
        }
        if i == 5 {
            continue;
        }
    }
    
    // 测试7.1 函数表达式块
    let mut c = {
        let mut t = a*a;
        t = t + b;
        t;
    };
    
    // 测试7.3 选择表达式
    let mut d = if c > 10 {
        c - 5;
    } else {
        c + 5;
    };
}
