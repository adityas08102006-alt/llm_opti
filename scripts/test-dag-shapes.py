#!/usr/bin/env python3
"""Test DAG shape classification."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.decomposer import classify_dag_shape, build_dag

tests = [
    "Write a function to calculate fibonacci",
    "Write an API endpoint with docs",
    "Write code and unit tests",
    "Write code with documentation and tests",
    "Just write documentation",
    "Build a REST API endpoint",
    "Write tests for my function",
]

for t in tests:
    shape = classify_dag_shape(t)
    dag = build_dag(t, shape)
    names = [n["name"] for n in dag]
    print(f"  shape={shape:35s} nodes={names}")

print()
# Verify all shapes return valid identifiers
shapes_found = set()
for t in tests:
    s = classify_dag_shape(t)
    shapes_found.add(s)
    dag = build_dag(t, s)
    assert len(dag) >= 1, f"Empty DAG for {t!r}"
    assert all(n["depends_on"] is not None for n in dag), f"None deps in DAG for {t!r}"
print(f"  Shapes found: {shapes_found}")
# All shapes must be A, B, or C
valid = shapes_found.issubset({"A", "B", "C"})
print(f"DAG shapes use A/B/C classification: {'PASS' if valid else 'FAIL'}")
# Test Shape C (linear chain)
seq_shape = classify_dag_shape("Write a sequential function with tests")
assert seq_shape == "C", f"Expected C got {seq_shape}"
seq_dag = build_dag("Write a sequential function with tests", seq_shape)
first = True
chain_ok = True
for n in seq_dag:
    if first:
        chain_ok = chain_ok and (n["depends_on"] == [])
        first = False
    else:
        expected = [n["id"] - 1]
        chain_ok = chain_ok and (n["depends_on"] == expected)
print(f"Linear chain (Shape C) topology: {'PASS' if chain_ok else 'FAIL'}")
# Test Shape A (fan-out) — code + docs with no test keywords have no deps
a_dag = build_dag("Write an API endpoint with documentation", "A")
fan_ok = all(n["depends_on"] == [] for n in a_dag)
if not fan_ok:
    for n in a_dag:
        print(f"    FAIL: id={n['id']} name={n['name']} depends_on={n['depends_on']}")
print(f"Fan-out (Shape A) topology: {'PASS' if fan_ok else 'FAIL'}")
