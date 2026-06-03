# How To Run

This guide explains how to set up, run, test, and debug the current CompileX implementation.

Current implementation status:
- Phase 1 completed: language design and sample programs.
- Phase 2 completed: lexical analyzer.
- Phase 3 completed: syntax analyzer (recursive descent parser + AST).
- Phase 4 completed: semantic analyzer (symbol table + type/scope validation).
- Phase 5 completed: intermediate code generation (TAC).
- Phase 5B completed: TAC interpreter and runtime output generation.
    - Includes arithmetic execution, print output, arrays, dictionaries, and index/key access.
- Phase 6 completed: error detection and suggestion module.
- Phase 7 completed: GUI development and compiler pipeline facade.
- Phase 8 completed: integration and testing.

## Project Setup

This project targets macOS with Mini Conda.

If environment already exists:

```bash
conda activate compilex
```

If environment does not exist:

```bash
conda create -n compilerx python=3.11 -y
conda activate compilex
```

If `conda activate` fails in zsh:

```bash
conda init zsh
exec zsh
conda activate compilex
```

Go to project root:

```bash
cd /Users/ashok/projects/CompileX
```

Install required package(s):

```bash
pip install pytest
```

## Running the Application

Launch the GUI using Makefile:

```bash
make gui
```

Or:

```bash
make run
```

Direct launch:

```bash
python -m gui.interface
```

## Running Individual Compiler Modules

### Run lexical analyzer manually (valid sample)

```bash
python - <<'PY'
from pathlib import Path
from compiler.lexer import Lexer

source = Path("docs/samples/valid/basic_declarations.edl").read_text()
tokens, errors = Lexer(source).tokenize()

print("TOKENS:")
for t in tokens:
    print(f"{t.token_type:14} {t.lexeme!r:20} line={t.line} col={t.column}")

print("\nLEXER ERRORS:")
if not errors:
    print("No lexical errors")
else:
    for e in errors:
        print(f"{e.message} (line {e.line}, col {e.column})")
PY
```

### Run parser manually (build AST + syntax diagnostics)

```bash
python - <<'PY'
from pathlib import Path
from compiler.lexer import Lexer
from compiler.parser import Parser

source = Path("docs/samples/valid/control_flow.edl").read_text()
tokens, lex_errors = Lexer(source).tokenize()
program, parse_errors = Parser(tokens).parse()

print("Statement count:", len(program.statements))
print("Lexer errors:", len(lex_errors))
print("Parser errors:", len(parse_errors))
for err in parse_errors:
    print(f"- {err.message} (line {err.line}, col {err.column})")
PY
```

### Run semantic analyzer manually (symbol table + semantic diagnostics)

```bash
python - <<'PY'
from pathlib import Path
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantic import SemanticAnalyzer

source = Path("docs/samples/valid/control_flow.edl").read_text()
tokens, lex_errors = Lexer(source).tokenize()
program, parse_errors = Parser(tokens).parse()
symbols, semantic_errors = SemanticAnalyzer().analyze(program)

print("Lexer errors:", len(lex_errors))
print("Parser errors:", len(parse_errors))
print("Semantic errors:", len(semantic_errors))
print("Symbols:")
for s in symbols:
    print(f"- {s.name}: {s.var_type} (scope {s.scope_level})")
for err in semantic_errors:
    print(f"- {err.message} (line {err.line}, col {err.column})")
PY
```

### Run TAC generator manually (intermediate code output)

```bash
python - <<'PY'
from pathlib import Path
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac_generator import TACGenerator

source = Path("docs/samples/valid/control_flow.edl").read_text()
tokens, lex_errors = Lexer(source).tokenize()
program, parse_errors = Parser(tokens).parse()
tac = TACGenerator().generate(program)

print("Lexer errors:", len(lex_errors))
print("Parser errors:", len(parse_errors))
print("TAC instructions:")
for i, ins in enumerate(tac, start=1):
    print(f"{i:02d}: op={ins.op}, arg1={ins.arg1}, arg2={ins.arg2}, result={ins.result}")
PY
```

### Run TAC interpreter manually (execute TAC and capture program output)

```bash
python - <<'PY'
from pathlib import Path
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.tac_generator import TACGenerator
from compiler.tac_interpreter import TACInterpreter

source = Path("docs/samples/valid/control_flow.edl").read_text()
tokens, lex_errors = Lexer(source).tokenize()
program, parse_errors = Parser(tokens).parse()
tac = TACGenerator().generate(program)
runtime = TACInterpreter().execute(tac)

print("Lexer errors:", len(lex_errors))
print("Parser errors:", len(parse_errors))
print("Runtime output:")
for line in runtime.output_lines:
    print(line)
PY
```

### Run collection runtime example (arrays and dictionaries)

```bash
python - <<'PY'
from compiler.pipeline import compile_source

source = '''
let arr: array = [1, 2, 3];
let data: dict = {"a": 10, "b": 20};
print(arr[1]);
print(data["a"]);
'''

result = compile_source(source)
print("Program output:")
for line in result.program_output:
    print(line)

print("Diagnostics:", len(result.diagnostics))
for d in result.diagnostics:
    print(f"- [{d.phase}] {d.message}")
PY
```

### Run error module manually (unified diagnostics + suggestions)

```bash
python - <<'PY'
from pathlib import Path
from compiler.errors import ErrorIntelligenceModule

# Intentionally invalid sample to demonstrate error recovery and suggestions.
source = Path("docs/samples/invalid/missing_semicolon.edl").read_text()
result = ErrorIntelligenceModule().analyze_source(source)

print("Diagnostics:")
for d in result.diagnostics:
    print(
        f"- [{d.phase}/{d.severity}] {d.message} "
        f"(line {d.line}, col {d.column}) -> Suggestion: {d.suggestion}"
    )

print("\nPartial outputs:")
print("Token count:", len(result.tokens))
print("Parsed statements:", len(result.ast.statements))
print("Symbol entries:", len(result.symbol_table))
PY
```

### Run full compiler pipeline manually (no GUI)

```bash
python - <<'PY'
from compiler.pipeline import compile_source

source = "let x: int = 1; print(x);"
result = compile_source(source)

print("Tokens:", len(result.tokens))
print("Statements:", len(result.ast.statements))
print("Symbols:", len(result.symbol_table))
print("TAC instructions:", len(result.tac))
print("Program output lines:", len(result.program_output))
for line in result.program_output:
    print("OUTPUT:", line)
print("Diagnostics:", len(result.diagnostics))
PY
```

### Run integration regression suite manually

```bash
python - <<'PY'
from compiler.integration import run_regression_suite

report = run_regression_suite(".")
print(f"Total: {report.total_cases}")
print(f"Passed: {report.passed_cases}")
print(f"Failed: {report.failed_cases}")
for case in report.cases:
    status = "PASS" if case.passed else "FAIL"
    print(f"[{status}] {case.name} | diagnostics={case.diagnostics_count}")
    if case.contract_issues:
        print("  contract issues:", case.contract_issues)
PY
```

## Using Makefile Commands

Show command list:

```bash
make help
```

Run all tests:

```bash
make test
```

Run lexer tests only:

```bash
make test-lexer
```

Run parser tests only:

```bash
make test-parser
```

Run semantic analyzer tests only:

```bash
make test-semantic
```

Run TAC generator tests only:

```bash
make test-tac
```

Run TAC interpreter tests only:

```bash
make test-interpreter
```

Run error module tests only:

```bash
make test-errors
```

Run compiler pipeline tests only:

```bash
make test-pipeline
```

Run integration/regression tests only:

```bash
make test-integration
```

Clean Python cache files:

```bash
make clean
```

Note:
- If your shell does not have `python` mapped, override Python executable:

```bash
make PYTHON=/Users/ashok/projects/CompileX/.venv/bin/python test
```

## Testing and Debugging Commands

Run full test suite:

```bash
python -m pytest -q
```

Run parser tests with verbose output:

```bash
python -m pytest -q tests/test_parser.py -vv
```

Run lexer tests with verbose output:

```bash
python -m pytest -q tests/test_lexer.py -vv
```

Run semantic tests with verbose output:

```bash
python -m pytest -q tests/test_semantic.py -vv
```

Run TAC tests with verbose output:

```bash
python -m pytest -q tests/test_tac_generator.py -vv
```

Run error module tests with verbose output:

```bash
python -m pytest -q tests/test_errors.py -vv
```

Run pipeline tests with verbose output:

```bash
python -m pytest -q tests/test_pipeline.py -vv
```

Run integration tests with verbose output:

```bash
python -m pytest -q tests/test_integration.py -vv
```

Run TAC interpreter tests with verbose output:

```bash
python -m pytest -q tests/test_tac_interpreter.py -vv
```

Run a specific test by name:

```bash
python -m pytest -q tests/test_parser.py -k precedence -vv
```

## Notes

- Primary planning docs are in `docs/`.
- Root-level run documentation is maintained in this file (`how_to_run.md`).
- Update this file after each phase to include new module run/test commands.
