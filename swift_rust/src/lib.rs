use cpython::{PyResult, Python, py_module_initializer, py_fn};

py_module_initializer!(rust2swift, |py, m| {
    m.add(py, "__doc__", "This module is implemented in Rust.")?;
    m.add(py, "sum_as_string", py_fn!(py, sum_as_string_py(a: i64, b:i64)))?;
    m.add(py, "hello_swift", py_fn!(py, hello_swift_py()))?;
    m.add(py, "update_spim", py_fn!(py, update_spim_py(data: &[u8])))?;
    Ok(())
});

fn sum_as_string(a:i64, b:i64) -> String {
    format!("{}", a + b).to_string()
}

fn sum_as_string_py(_: Python, a:i64, b:i64) -> PyResult<String> {
    let out = sum_as_string(a, b);
    Ok(out)
}

fn hello_swift() -> String {
    String::from("Hello Swift!")
}

fn hello_swift_py(_: Python) -> PyResult<String> {
    let out = hello_swift();
    Ok(out)
}

fn update_spim(data: &[u8]) -> String {
    println!("{:?}", data);
    String::from("OK")
}

fn update_spim_py(_: Python, data: &[u8]) -> PyResult<String> {
    let out = update_spim(data);
    Ok(out)
}
