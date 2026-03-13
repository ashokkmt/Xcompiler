"""Tkinter GUI for visualizing CompileX compiler phases (Phase 7)."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from compiler.pipeline import compile_source


class CompilerGUI:
    """GUI layer that delegates compilation to compiler-core APIs."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("CompileX - Educational Mini Compiler")
        self.root.geometry("1100x760")

        self.source_text: tk.Text
        self.output_widgets: dict[str, tk.Text] = {}

        self._build_layout()

    def _build_layout(self) -> None:
        top_bar = ttk.Frame(self.root, padding=8)
        top_bar.pack(fill=tk.X)

        ttk.Label(top_bar, text="Sample:").pack(side=tk.LEFT)
        self.sample_var = tk.StringVar(value="custom")
        sample_box = ttk.Combobox(
            top_bar,
            textvariable=self.sample_var,
            state="readonly",
            width=28,
            values=["custom", "valid/basic_declarations", "valid/control_flow", "invalid/missing_semicolon"],
        )
        sample_box.pack(side=tk.LEFT, padx=(6, 8))
        sample_box.bind("<<ComboboxSelected>>", self._on_sample_selected)

        ttk.Button(top_bar, text="Compile", command=self._compile).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(top_bar, text="Clear", command=self._clear_all).pack(side=tk.LEFT)

        editor_frame = ttk.LabelFrame(self.root, text="Source Code", padding=8)
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.source_text = tk.Text(editor_frame, wrap=tk.NONE, height=14)
        self.source_text.pack(fill=tk.BOTH, expand=True)
        self.source_text.insert(
            tk.END,
            "let x: int = 0;\n"
            "while (x < 3) {\n"
            "    print(x);\n"
            "    x = x + 1;\n"
            "}\n",
        )

        outputs_frame = ttk.LabelFrame(self.root, text="Compiler Outputs", padding=8)
        outputs_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        notebook = ttk.Notebook(outputs_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        for name in ["Tokens", "AST", "Symbol Table", "TAC", "Errors"]:
            tab = ttk.Frame(notebook)
            notebook.add(tab, text=name)
            widget = tk.Text(tab, wrap=tk.NONE)
            widget.pack(fill=tk.BOTH, expand=True)
            self.output_widgets[name] = widget

    def _on_sample_selected(self, _event=None) -> None:
        selected = self.sample_var.get()
        if selected == "custom":
            return

        sample_path = Path("docs/samples") / f"{selected}.edl"
        if not sample_path.exists():
            return

        self.source_text.delete("1.0", tk.END)
        self.source_text.insert(tk.END, sample_path.read_text())

    def _clear_all(self) -> None:
        self.source_text.delete("1.0", tk.END)
        for widget in self.output_widgets.values():
            widget.delete("1.0", tk.END)

    def _compile(self) -> None:
        source = self.source_text.get("1.0", tk.END)
        result = compile_source(source)

        self._write_output("Tokens", self._format_tokens(result.tokens))
        self._write_output("AST", self._format_ast(result.ast))
        self._write_output("Symbol Table", self._format_symbol_table(result.symbol_table))
        self._write_output("TAC", self._format_tac(result.tac))
        self._write_output("Errors", self._format_diagnostics(result.diagnostics))

    def _write_output(self, section: str, text: str) -> None:
        widget = self.output_widgets[section]
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, text)

    def _format_tokens(self, tokens) -> str:
        lines = ["type            lexeme               line  col", "-" * 52]
        for token in tokens:
            lines.append(
                f"{token.token_type:14} {repr(token.lexeme):20} {token.line:4} {token.column:4}"
            )
        return "\n".join(lines)

    def _format_ast(self, ast) -> str:
        return json.dumps(asdict(ast), indent=2)

    def _format_symbol_table(self, symbols) -> str:
        if not symbols:
            return "No symbols recorded."

        lines = ["name            type       scope", "-" * 34]
        for entry in symbols:
            lines.append(f"{entry.name:14} {entry.var_type:10} {entry.scope_level}")
        return "\n".join(lines)

    def _format_tac(self, tac) -> str:
        if not tac:
            return "No TAC instructions generated."

        lines = ["#   op              arg1            arg2            result", "-" * 66]
        for idx, ins in enumerate(tac, start=1):
            lines.append(
                f"{idx:02}  {ins.op:14} {str(ins.arg1):14} {str(ins.arg2):14} {str(ins.result)}"
            )
        return "\n".join(lines)

    def _format_diagnostics(self, diagnostics) -> str:
        if not diagnostics:
            return "No diagnostics."

        lines = []
        for diag in diagnostics:
            lines.append(
                f"[{diag.phase}/{diag.severity}] {diag.message} "
                f"(line {diag.line}, col {diag.column})"
            )
            lines.append(f"Suggestion: {diag.suggestion}")
            lines.append("")
        return "\n".join(lines).rstrip()


def main() -> None:
    root = tk.Tk()
    CompilerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
