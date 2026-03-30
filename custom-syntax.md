# Custom Language Syntax Guide

This document explains the syntax of the custom educational language used in CompileX.
It is intended to help developers write test programs and extend language features.

## Basic Program Structure

A program is a list of statements executed top to bottom.

Rules:
- Most statements end with `;`.
- Block statements use `{ ... }` and contain inner statements.
- Comments are supported:
  - `// single-line comment`
  - `/* multi-line comment */`

Supported statement forms:
- Variable declaration: `let name: type = expression;`
- Assignment: `name = expression;`
- Print: `print(expression);`
- Conditional: `if (condition) { ... } else { ... }`
- Loop: `while (condition) { ... }`

## Variable Assignment

Variables are declared with explicit type annotations.
After declaration, values can be reassigned with assignment statements.

```edl
let x: int = 5;
let y: int = x + 10;
x = y - 3;
```

## Arithmetic Operations

Supported arithmetic operators:
- `+`
- `-`
- `*`
- `/`
- `%`

Example:

```edl
let a: int = 4;
let b: int = 7;
let z: int = a + b * 3;
print(z);
```

## Print Statement

Use `print(...)` to send values to runtime output.

```edl
let x: int = 12;
let a: int = 2;
let b: int = 3;
print(x);
print(a + b);
```

## Arrays

Array creation uses square brackets.

```edl
let arr: array = [1, 2, 3];
print(arr[1]);
```

Notes:
- Arrays are stored as list values at runtime.
- Index expressions use integer indexes.

## Dictionaries

Dictionary creation uses braces with `key: value` entries.

```edl
let data: dict = {"a": 10, "b": 20};
print(data["a"]);
```

Notes:
- Dictionaries are stored as dict values at runtime.
- Keys are commonly strings, but expressions are also supported.

## Multiple Statements

Programs can contain many lines and mixed statement types.

```edl
let x: int = 10;
let y: int = x + 5;
print(y);

let arr: array = [y, y + 1];
print(arr[0]);
```

## Expressions and Nesting

Expressions support grouping and nesting.

```edl
let x: int = 2;
let y: int = 5;
let result: int = (x + (y * 3)) - ((x + y) % 3);
print(result);
```

## Developer Notes

Use this guide with files in `docs/samples/valid/` and `docs/samples/invalid/` to:
- understand grammar usage,
- create new compiler tests,
- prototype new syntax features in future phases.
