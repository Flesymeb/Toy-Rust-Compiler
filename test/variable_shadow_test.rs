fn main() {
    let mut a: i32 = 1;  // 第一个a
    let mut a = 2;       // 第二个a，遮蔽第一个
    let mut a: i32 = 3;  // 第三个a，遮蔽第二个，这个a未被使用
    
    let b = 10;          // b定义但未使用
    let c = 20;          // c将被使用
    
    println!("{}", c);   // 使用c
}
