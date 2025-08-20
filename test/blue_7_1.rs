// 测试7.1 函数表达式块
fn main() {
    let mut z = {
        let mut t = 1*2 + 3;
        t = t + 4*5;
        t;
    };
}
