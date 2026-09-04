"""Tests for fork_meter.analyzer — C, C++, C#, Rust, Kotlin, and Scala support."""

from fork_meter.analyzer import _get_parent_class_rust, analyze_file


def test_c_function_complexity(tmp_path):
    src = b"""
int add(int a, int b) {
    if (a > 0) {
        for (int i = 0; i < a; i++) {
            a += i;
        }
    }
    return a + b;
}
"""
    f = tmp_path / "test.c"
    f.write_bytes(src)
    results = analyze_file(f, "C")
    assert len(results) == 1
    res = results[0]
    assert res.name == "add"
    assert res.parent_class is None
    assert res.fragment_type == "function"
    assert res.complexity == 3  # 1 base + if + for


def test_c_switch_case_and_ternary(tmp_path):
    src = b"""
int classify(int a) {
    int b = a ? a : 0;
    switch (b) {
        case 1:
            break;
        default:
            break;
    }
    return b;
}
"""
    f = tmp_path / "test.c"
    f.write_bytes(src)
    results = analyze_file(f, "C")
    assert len(results) == 1
    assert results[0].complexity == 4  # 1 base + ternary + 2 case_statement


def test_cpp_method_and_free_function(tmp_path):
    src = b"""
class Calc {
public:
    int compute(int x) {
        if (x > 0) {
            for (int i = 0; i < x; i++) {
                x--;
            }
        }
        return x;
    }
};

int freeFn(int a) {
    return a;
}
"""
    f = tmp_path / "test.cpp"
    f.write_bytes(src)
    results = analyze_file(f, "C++")
    assert len(results) == 2
    compute = next(r for r in results if r.name == "compute")
    free_fn = next(r for r in results if r.name == "freeFn")
    assert compute.parent_class == "Calc"
    assert compute.fragment_type == "method"
    assert compute.complexity == 3  # 1 base + if + for
    assert free_fn.parent_class is None
    assert free_fn.fragment_type == "function"
    assert free_fn.complexity == 1


def test_cpp_try_catch_and_for_range(tmp_path):
    src = b"""
int sum(int arr[3]) {
    int total = 0;
    try {
        for (int x : arr) {
            total += x;
        }
    } catch (...) {
        total = 0;
    }
    return total;
}
"""
    f = tmp_path / "test.cpp"
    f.write_bytes(src)
    results = analyze_file(f, "C++")
    assert len(results) == 1
    assert results[0].complexity == 3  # 1 base + for_range_loop + catch_clause


def test_csharp_constructor_and_method(tmp_path):
    src = b"""
class Calc {
    public Calc() {}
    public int Compute(int x) {
        if (x > 0) {
            for (int i = 0; i < x; i++) {
                x--;
            }
        }
        return x;
    }
}
"""
    f = tmp_path / "Calc.cs"
    f.write_bytes(src)
    results = analyze_file(f, "C#")
    assert len(results) == 2
    ctor = next(r for r in results if r.fragment_type == "constructor")
    method = next(r for r in results if r.fragment_type == "method")
    assert ctor.parent_class == "Calc"
    assert ctor.complexity == 1
    assert method.name == "Compute"
    assert method.parent_class == "Calc"
    assert method.complexity == 3  # 1 base + if + for


def test_csharp_switch_section_and_ternary(tmp_path):
    src = b"""
class Calc {
    int Classify(int a) {
        int b = a > 0 ? a : 0;
        switch (b) {
            case 1:
                break;
            default:
                break;
        }
        return b;
    }
}
"""
    f = tmp_path / "Calc.cs"
    f.write_bytes(src)
    results = analyze_file(f, "C#")
    assert len(results) == 1
    assert results[0].complexity == 4  # 1 base + ternary + 2 switch_section


def test_rust_impl_method_and_free_function(tmp_path):
    src = b"""
struct Counter;

impl Counter {
    fn increment(&self, delta: i32) -> i32 {
        let mut total = 0;
        for i in 0..delta {
            total += i;
        }
        total
    }
}

fn free_fn(a: i32) -> i32 {
    a
}
"""
    f = tmp_path / "test.rs"
    f.write_bytes(src)
    results = analyze_file(f, "Rust")
    assert len(results) == 2
    increment = next(r for r in results if r.name == "increment")
    free_fn = next(r for r in results if r.name == "free_fn")
    assert increment.parent_class == "Counter"
    assert increment.fragment_type == "method"
    assert increment.complexity == 2  # 1 base + for_expression
    assert free_fn.parent_class is None
    assert free_fn.fragment_type == "function"
    assert free_fn.complexity == 1


def test_rust_match_and_while_loop(tmp_path):
    src = b"""
fn classify(a: i32) -> i32 {
    let mut x = a;
    while x > 0 {
        x -= 1;
    }
    match a {
        1 => 1,
        _ => 0,
    }
}
"""
    f = tmp_path / "test.rs"
    f.write_bytes(src)
    results = analyze_file(f, "Rust")
    assert len(results) == 1
    assert results[0].complexity == 4  # 1 base + while + 2 match_arm


def test_get_parent_class_rust_no_impl():
    class FakeNode:
        parent = None

    assert _get_parent_class_rust(FakeNode()) is None


def test_kotlin_method_complexity(tmp_path):
    src = b"""
class Calc {
    fun compute(x: Int): Int {
        var result = x
        if (x > 0) {
            for (i in 0..x) {
                result += i
            }
        }
        return result
    }
}
"""
    f = tmp_path / "Calc.kt"
    f.write_bytes(src)
    results = analyze_file(f, "Kotlin")
    assert len(results) == 1
    res = results[0]
    assert res.name == "compute"
    assert res.parent_class == "Calc"
    assert res.fragment_type == "method"
    assert res.complexity == 3  # 1 base + if + for


def test_kotlin_when_and_catch(tmp_path):
    src = b"""
fun classify(a: Int): Int {
    when (a) {
        1 -> return 1
        else -> return 0
    }
    try {
        return a
    } catch (e: Exception) {
        return 0
    }
}
"""
    f = tmp_path / "test.kt"
    f.write_bytes(src)
    results = analyze_file(f, "Kotlin")
    assert len(results) == 1
    assert results[0].parent_class is None
    assert results[0].fragment_type == "function"
    assert results[0].complexity == 4  # 1 base + 2 when_entry + catch_block


def test_scala_method_complexity(tmp_path):
    src = b"""
class Calc {
    def compute(x: Int): Int = {
        var result = x
        if (x > 0) {
            for (i <- 0 to x) {
                result += i
            }
        }
        result
    }
}
"""
    f = tmp_path / "Calc.scala"
    f.write_bytes(src)
    results = analyze_file(f, "Scala")
    assert len(results) == 1
    res = results[0]
    assert res.name == "compute"
    assert res.parent_class == "Calc"
    assert res.fragment_type == "method"
    assert res.complexity == 3  # 1 base + if_expression + for_expression


def test_scala_match_case_clauses(tmp_path):
    src = b"""
def classify(a: Int): Int = {
    a match {
        case 1 => 1
        case _ => 0
    }
}
"""
    f = tmp_path / "test.scala"
    f.write_bytes(src)
    results = analyze_file(f, "Scala")
    assert len(results) == 1
    assert results[0].parent_class is None
    assert results[0].fragment_type == "function"
    assert results[0].complexity == 3  # 1 base + 2 case_clause
