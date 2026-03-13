"""Phase 8 integration and regression tests for CompileX."""

from pathlib import Path

from compiler.integration import (
    compile_file,
    run_regression_suite,
    validate_output_contract,
)
from compiler.pipeline import compile_source


def test_compile_source_contract_is_consistent_on_valid_program():
    source = "let x: int = 1; print(x);"
    output = compile_source(source)

    issues = validate_output_contract(output)

    assert issues == []
    assert output.diagnostics == []
    assert len(output.tac) > 0


def test_compile_file_invalid_program_still_returns_partial_outputs():
    sample = Path("docs/samples/invalid/missing_semicolon.edl")
    output = compile_file(sample)

    issues = validate_output_contract(output)

    assert issues == []
    assert len(output.tokens) > 0
    assert len(output.diagnostics) > 0


def test_regression_suite_passes_for_current_sample_set():
    report = run_regression_suite(Path("."))

    assert report.total_cases >= 5
    assert report.failed_cases == 0
    assert report.passed_cases == report.total_cases
