# Xcompiler

An educational mini compiler for the custom `EduLang` language, with a GUI frontend for visualization and a modular compiler core that includes lexing, parsing, semantic analysis, intermediate code generation, and execution.

## Project Objective

- Demonstrate a complete compiler pipeline in a clean, modular structure.
- Provide a GUI layer for editing code, visualizing tokens, AST, TAC, symbol tables, and runtime output.
- Support syntax and semantic error detection with helpful suggestions.
- Use a simple recursive descent parser and three-address code (TAC) intermediate representation.

## What This Project Does

- Reads user source code in the `EduLang` language.
- Tokenizes the input using the lexical analyzer.
- Parses tokens into an Abstract Syntax Tree (AST).
- Performs semantic validation with a symbol table and type checking.
- Generates intermediate three-address code.
- Executes TAC through an interpreter and captures runtime output.
- Displays errors and suggestions through the GUI.

## Core Components

- `compiler/lexer.py` — lexical analyzer generates tokens.
- `compiler/parser.py` — recursive descent parser builds AST.
- `compiler/semantic.py` — semantic analyzer checks declarations, types, and scopes.
- `compiler/tac_generator.py` — creates TAC from the AST.
- `compiler/tac_interpreter.py` — executes TAC and produces runtime output.
- `compiler/errors.py` — manages compiler error reporting.
- `gui/interface.py` — GUI entry point and visualization layer.

## Language Overview

The custom language `EduLang` supports:

- `let` declarations with typed variables (`int`, `float`, `bool`, `string`)
- arithmetic expressions, comparisons, and boolean logic
- `print(...)` statements
- `if` / `else` and `while` control flow
- nested blocks with lexical scope
- single-line `//` and multi-line `/* ... */` comments

Source files use `;` to terminate statements, except for block statements.

## How To Start

### Step 1: Set up the environment

You can use either `venv` or `conda`, depending on your preference and existing setup.

#### Option A: Use `venv`

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Option B: Use `conda`

If the environment already exists:

```bash
conda activate compilex
```

If you need to create it:

```bash
conda create -n compilex python=3.11 -y
conda activate compilex
```

If `conda activate` fails in `zsh`:

```bash
conda init zsh
exec zsh
conda activate compilex
```

### Step 2: Install requirements

```bash
pip install pytest
```

### Step 3: Run the GUI

Use the Makefile:

```bash
make gui
```

Or run directly:

```bash
make run
```

Or launch the GUI module manually:

```bash
python -m gui.interface
```

## Running Tests

Execute the project test suite with:

```bash
pytest
```

## Manual Module Usage

The root `how_to_run.md` contains examples for running individual compiler phases manually, including the lexer, parser, semantic analyzer, TAC generator, and TAC interpreter.

## Sample Programs

Valid and invalid language samples are available under:

- `docs/samples/valid/`
- `docs/samples/invalid/`

Use these examples for testing compiler behavior and exercising error handling.

## Project Structure

- `compiler/` — core compiler implementation
- `gui/` — user interface and visualization
- `docs/` — architecture, language spec, implementation notes, and samples
- `tests/` — automated unit and integration tests

## Notes

The compiler is intentionally educational and modular, so each phase can be examined separately and the GUI remains independent of compiler logic.
