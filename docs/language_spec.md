# Language Specification (Phase 1)

## 1. Purpose
This document defines the custom educational language used by the compiler project.
The language is intentionally small, consistent, and easy to parse with recursive descent.

## 2. Language Name
`EduLang`

## 3. Program Structure
A program is a sequence of statements.

Each statement must end with `;` except block statements (`if`, `else`, `while`, and `{ ... }` blocks).

## 4. Keywords
- `let`
- `if`
- `else`
- `while`
- `true`
- `false`
- `print`

## 5. Data Types
- `int`
- `float`
- `bool`
- `string`

Type declarations use `let` with explicit type annotation:
`let <identifier>: <type> = <expression>;`

Examples:
- `let x: int = 5;`
- `let ratio: float = 3.14;`
- `let ok: bool = true;`
- `let msg: string = "hello";`

## 6. Comments
- Single-line: `// comment text`
- Multi-line: `/* comment text */`

## 7. Tokens

### 7.1 Identifier
- Pattern: `[A-Za-z_][A-Za-z0-9_]*`
- Case-sensitive

### 7.2 Literals
- Integer: `0`, `12`, `300`
- Float: `3.14`, `0.5`, `10.0`
- Boolean: `true`, `false`
- String: `"text"` (double-quoted)

### 7.3 Operators
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- Assignment: `=`
- Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Logical: `&&`, `||`, `!`

### 7.4 Delimiters and Symbols
- `(`, `)`
- `{`, `}`
- `;`
- `:`

## 8. Grammar (EBNF)

```ebnf
program         = { statement } ;

statement       = declaration_stmt
                | assignment_stmt
                | print_stmt
                | if_stmt
                | while_stmt
                | block ;

block           = "{" { statement } "}" ;

declaration_stmt= "let" IDENTIFIER ":" type "=" expression ";" ;

assignment_stmt = IDENTIFIER "=" expression ";" ;

print_stmt      = "print" "(" expression ")" ";" ;

if_stmt         = "if" "(" expression ")" block [ "else" block ] ;

while_stmt      = "while" "(" expression ")" block ;

type            = "int" | "float" | "bool" | "string" ;

expression      = logical_or ;
logical_or      = logical_and { "||" logical_and } ;
logical_and     = equality { "&&" equality } ;
equality        = comparison { ("==" | "!=") comparison } ;
comparison      = term { ("<" | "<=" | ">" | ">=") term } ;
term            = factor { ("+" | "-") factor } ;
factor          = unary { ("*" | "/" | "%") unary } ;
unary           = ("!" | "-") unary | primary ;
primary         = INT_LITERAL
                | FLOAT_LITERAL
                | STRING_LITERAL
                | "true"
                | "false"
                | IDENTIFIER
                | "(" expression ")" ;
```

## 9. Operator Precedence and Associativity
Higher rows bind more strongly.

| Level | Operators            | Associativity |
|------:|----------------------|---------------|
| 1     | `!`, unary `-`       | Right         |
| 2     | `*`, `/`, `%`        | Left          |
| 3     | `+`, `-`             | Left          |
| 4     | `<`, `<=`, `>`, `>=` | Left          |
| 5     | `==`, `!=`           | Left          |
| 6     | `&&`                 | Left          |
| 7     | `||`                 | Left          |

## 10. Type Rules
- Assignment requires compatible types between target and expression.
- `int` can be promoted to `float` in arithmetic expressions.
- `float` to `int` implicit narrowing is not allowed.
- Arithmetic operators (`+`, `-`, `*`, `/`, `%`) require numeric operands (`int`, `float`).
- `%` is only valid for `int` operands.
- Comparison operators return `bool`.
- Logical operators (`&&`, `||`, `!`) require `bool` operands.
- `if` and `while` conditions must evaluate to `bool`.

## 11. Initial Semantic Constraints
- Variables must be declared before use.
- Redeclaration in the same scope is not allowed.
- Shadowing in nested scopes is allowed.

## 12. Example Program Categories
- Valid examples: declarations, expressions, control flow, nested blocks.
- Invalid examples: missing semicolon, undeclared variable, type mismatch, malformed syntax.

## 13. Phase 1 Deliverable Notes
This specification is the source of truth for:
- lexer token definitions
- parser grammar implementation
- semantic type and scope checks
- future TAC test cases
