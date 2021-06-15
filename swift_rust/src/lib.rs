use cpython::{PyResult, Python, py_module_initializer, py_fn};

py_module_initializer!(rust2swift, |py, m| {
    m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "hello_swift", py_fn!(py, hello_swift_py()))?;
    m.add(py, "update_spim", py_fn!(py, update_spim_py(data: &[u8])))?;
    Ok(())
});

fn hello_swift() -> String {
    String::from("Hello Swift!")
}

fn hello_swift_py(_: Python) -> PyResult<String> {
    let out = hello_swift();
    Ok(out)
}

fn update_spim(data: &[u8]) -> Vec<u32> {
    let eness: Vec<u32> = vec![256*256*256, 256*256, 256, 1];
    let iter: Vec<u32> = data.chunks_exact(4).zip(eness.chunks_exact(4).cycle()).map(|(a, b)| {
        let mut sum = 0u32;
        for i in 0..4 {
            sum+=a[i] as u32 * b[i];
        }
        sum
    }).collect();
    iter
}

fn update_spim_py(_: Python, data: &[u8]) -> PyResult<Vec<u32>> {
    let out = update_spim(data);
    Ok(out)
}


