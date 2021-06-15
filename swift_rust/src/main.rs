fn main() {
    println!("Hello, world!");
    //let a:Vec<u8> = vec![255, 255, 255, 255, 0, 0, 0, 1, 0, 0, 1, 0, 1, 1, 1, 1];
    let a:Vec<u8> = vec![1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0];
    update_spim(&a);
}

fn update_spim(data: &[u8]) {
    let eness: Vec<u32> = vec![256*256*256, 256*256, 256, 1];
    let iter:Vec<u32> = data.chunks_exact(4).zip(eness.chunks_exact(4).cycle()).map(|(a, b)| {
        let mut sum = 0u32;
        for i in 0..4 {
            sum+=a[i] as u32 * b[i];
        }
        sum
    }).collect();
    println!("{:?}", iter);
}
