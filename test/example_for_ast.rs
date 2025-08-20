// 这是一个Rust-like测试文件，用于测试语法树可视化
fn main() -> i32 {
    let mut x: i32 = 10;
    let y: i32 = 20;
    let mut flag: i32 = 0;
    
    if x > y {
        flag = 1;
    } else if x < y {
        flag = 2;
    } else {
        flag = 0; 
    }
    
    while x > 0 {
        x = x - 1;
    }
    
    return 0;
}
