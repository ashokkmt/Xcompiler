"""Integration and regression utilities for full CompileX pipeline (Phase 8)."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from compiler.pipeline import CompileOutput, compile_source


@dataclass(frozen=True)
class IntegrationCaseResult:
    """Result for one integration test case."""

    name: str
    expected_valid: bool
    passed: bool
    diagnostics_count: int
    contract_issues: List[str]


@dataclass(frozen=True)
class RegressionReport:
    """Aggregated results for a regression run."""

    total_cases: int
    passed_cases: int
    failed_cases: int
    cases: List[IntegrationCaseResult]


def compile_file(file_path: str | Path) -> CompileOutput:
    """Compile source from a file path through the full pipeline."""
    path = Path(file_path)
    source = path.read_text()
    return compile_source(source)


def validate_output_contract(output: CompileOutput) -> List[str]:
    """Validate compile output contract consistency across stages."""
    issues: List[str] = []

    if not isinstance(output.tokens, list):
        issues.append("tokens must be a list")
    if not isinstance(output.tac, list):
        issues.append("tac must be a list")
    if not isinstance(output.program_output, list):
        issues.append("program_output must be a list")
    if not isinstance(output.diagnostics, list):
        issues.append("diagnostics must be a list")
    if output.ast is None:
        issues.append("ast must not be None")

    # Token stream contract: always ends with EOF token.
    if output.tokens:
        last = output.tokens[-1]
        if getattr(last, "token_type", None) != "EOF":
            issues.append("token stream must end with EOF token")
    else:
        issues.append("token stream is empty")

    # Diagnostic contract: ensure mandatory fields exist.
    for idx, diag in enumerate(output.diagnostics):
        if not getattr(diag, "phase", None):
            issues.append(f"diagnostic[{idx}] missing phase")
        if not getattr(diag, "severity", None):
            issues.append(f"diagnostic[{idx}] missing severity")
        if not getattr(diag, "message", None):
            issues.append(f"diagnostic[{idx}] missing message")
        if not getattr(diag, "suggestion", None):
            issues.append(f"diagnostic[{idx}] missing suggestion")

    return issues


def run_regression_suite(project_root: str | Path) -> RegressionReport:
    """Run regression checks against sample programs under docs/samples."""
    root = Path(project_root)
    sample_sets = [
        (root / "docs" / "samples" / "valid", True),
        (root / "docs" / "samples" / "invalid", False),
    ]

    cases: List[IntegrationCaseResult] = []

    for folder, expected_valid in sample_sets:
        if not folder.exists():
            continue
        for sample_file in sorted(folder.glob("*.edl")):
            output = compile_file(sample_file)
            issues = validate_output_contract(output)

            diagnostics_count = len(output.diagnostics)
            diagnostics_ok = diagnostics_count == 0 if expected_valid else diagnostics_count > 0
            passed = diagnostics_ok and not issues

            cases.append(
                IntegrationCaseResult(
                    name=str(sample_file.relative_to(root)),
                    expected_valid=expected_valid,
                    passed=passed,
                    diagnostics_count=diagnostics_count,
                    contract_issues=issues,
                )
            )

    total = len(cases)
    passed = sum(1 for case in cases if case.passed)
    return RegressionReport(
        total_cases=total,
        passed_cases=passed,
        failed_cases=total - passed,
        cases=cases,
    )
