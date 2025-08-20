fn main() {
    let mut i:i32 = 0;
    let mut sum:i32 = 0;
    while i < 10 {
        i = i + 1;
        if i % 2 == 0 {
            continue;
        }
        sum = sum + i;  // 只累加奇数
    }
}
