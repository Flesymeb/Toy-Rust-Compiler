fn main() {
    // 测试变量声明赋值和类型推导
    let mut a:i32 = 1;
    let mut b = 2;  // 类型推导
    
    // 测试loop循环
    let mut i:i32 = 0;
    loop {
        i = i + 1;
        if i > 5 {
            break;
        }
        if i % 2 == 0 {
            continue;
        }
        a = a + i;  // 只累加奇数
    }
    
    // 测试变量重影(shadowing)
    let mut a = 10;  // 重影之前的a
    b = a;
}
