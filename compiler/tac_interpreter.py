"""TAC interpreter for runtime execution and output generation (new phase)."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from compiler.tac_generator import TACInstruction


@dataclass(frozen=True)
class ExecutionResult:
    """Runtime result for a TAC program execution."""

    output: List[str]
    memory: Dict[str, Any]
    runtime_error: Optional[str]
    runtime_error_suggestion: Optional[str] = None
    runtime_error_line: int = 0
    runtime_error_column: int = 0


class TACInterpreter:
    """Executes TAC instructions sequentially and simulates runtime behavior."""

    def execute(self, instructions: List[TACInstruction]) -> ExecutionResult:
        memory: Dict[str, Any] = {}
        output: List[str] = []
        labels = self._index_labels(instructions)

        pc = 0
        while pc < len(instructions):
            ins = instructions[pc]
            op = ins.op

            if op == "LABEL":
                pc += 1
                continue

            if op == "GOTO":
                if ins.result not in labels:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        f"Unknown label in GOTO: {ins.result}",
                        "Check generated control-flow labels in TAC.",
                    )
                pc = labels[ins.result]
                continue

            if op == "IF_FALSE_GOTO":
                condition = self._resolve_operand(ins.arg1, memory)
                if isinstance(condition, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(condition),
                        "Ensure all referenced values are initialized before use.",
                    )
                if not bool(condition):
                    if ins.result not in labels:
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            f"Unknown label in IF_FALSE_GOTO: {ins.result}",
                            "Check generated control-flow labels in TAC.",
                        )
                    pc = labels[ins.result]
                    continue
                pc += 1
                continue

            if op == "ASSIGN":
                value = self._resolve_operand(ins.arg1, memory)
                if isinstance(value, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(value),
                        "Ensure all referenced values are initialized before use.",
                    )
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "ASSIGN instruction missing result target",
                        "Regenerate TAC to include a valid assignment destination.",
                    )
                memory[ins.result] = value
                pc += 1
                continue

            if op == "ARRAY_NEW":
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "ARRAY_NEW instruction missing result target",
                        "Regenerate TAC to include an array destination temporary.",
                    )
                memory[ins.result] = []
                pc += 1
                continue

            if op == "ARRAY_APPEND":
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "ARRAY_APPEND instruction missing result target",
                        "Regenerate TAC to include an array destination temporary.",
                    )
                container_value = memory.get(ins.result)
                if not isinstance(container_value, list):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "ARRAY_APPEND target is not an array",
                        "Use ARRAY_APPEND only on array values.",
                    )
                value = self._resolve_operand(ins.arg2, memory)
                if isinstance(value, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(value),
                        "Ensure all referenced values are initialized before use.",
                    )
                container_value.append(value)
                pc += 1
                continue

            if op == "DICT_NEW":
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "DICT_NEW instruction missing result target",
                        "Regenerate TAC to include a dictionary destination temporary.",
                    )
                memory[ins.result] = {}
                pc += 1
                continue

            if op == "DICT_SET":
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "DICT_SET instruction missing result target",
                        "Regenerate TAC to include a dictionary destination temporary.",
                    )
                container_value = memory.get(ins.result)
                if not isinstance(container_value, dict):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "DICT_SET target is not a dictionary",
                        "Use DICT_SET only on dictionary values.",
                    )
                key = self._resolve_operand(ins.arg1, memory)
                value = self._resolve_operand(ins.arg2, memory)
                if isinstance(key, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(key),
                        "Ensure dictionary keys are resolved before insertion.",
                    )
                if isinstance(value, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(value),
                        "Ensure dictionary values are resolved before insertion.",
                    )
                if not self._is_hashable(key):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        f"Invalid dictionary key access: key of type '{type(key).__name__}' is not hashable",
                        "Use hashable key types like string, int, float, or bool.",
                    )

                container_value[key] = value
                pc += 1
                continue

            if op == "INDEX_GET":
                collection = self._resolve_operand(ins.arg1, memory)
                index = self._resolve_operand(ins.arg2, memory)
                if isinstance(collection, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(collection),
                        "Ensure the indexed value is initialized before access.",
                    )
                if isinstance(index, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(index),
                        "Ensure the index/key value is initialized before access.",
                    )
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        "INDEX_GET instruction missing result target",
                        "Regenerate TAC to include a destination temporary for index access.",
                    )

                if isinstance(collection, list):
                    if isinstance(index, bool) or not isinstance(index, int):
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            f"Array index must be integer, got {type(index).__name__}",
                            "Use an integer index such as 0, 1, or a variable of type int.",
                        )
                    if index < 0 or index >= len(collection):
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            f"Array index out of bounds: index {index}, valid range is 0 to {len(collection) - 1}",
                            "Check array length and ensure index stays within bounds.",
                        )
                    memory[ins.result] = collection[index]
                    pc += 1
                    continue

                if isinstance(collection, dict):
                    if not self._is_hashable(index):
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            f"Invalid dictionary key access: key of type '{type(index).__name__}' is not hashable",
                            "Use hashable key types like string, int, float, or bool.",
                        )
                    if index not in collection:
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            f"Dictionary key not found: {index!r}",
                            "Check available keys before access or initialize the key first.",
                        )
                    memory[ins.result] = collection[index]
                    pc += 1
                    continue

                return self._instruction_error(
                    output,
                    memory,
                    ins,
                    f"Invalid index access on type '{type(collection).__name__}'",
                    "Index access is supported only for arrays and dictionaries.",
                )

            if op == "PRINT":
                value = self._resolve_operand(ins.arg1, memory)
                if isinstance(value, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(value),
                        "Ensure printed values are initialized before use.",
                    )
                output.append(str(value))
                pc += 1
                continue

            if op in {"NEG", "NOT"}:
                operand = self._resolve_operand(ins.arg1, memory)
                if isinstance(operand, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(operand),
                        "Ensure the unary operand is initialized before use.",
                    )
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        f"{op} instruction missing result target",
                        "Regenerate TAC to include a destination temporary.",
                    )
                if op == "NEG":
                    if not isinstance(operand, (int, float)):
                        return self._instruction_error(
                            output,
                            memory,
                            ins,
                            "NEG requires numeric operand",
                            "Use NEG only with int or float values.",
                        )
                    memory[ins.result] = -operand
                else:
                    memory[ins.result] = not bool(operand)
                pc += 1
                continue

            if op in {"+", "-", "*", "/", "%", "<", "<=", ">", ">=", "==", "!=", "&&", "||"}:
                left = self._resolve_operand(ins.arg1, memory)
                right = self._resolve_operand(ins.arg2, memory)
                if isinstance(left, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(left),
                        "Ensure the left operand is initialized before use.",
                    )
                if isinstance(right, RuntimeError):
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        str(right),
                        "Ensure the right operand is initialized before use.",
                    )
                if ins.result is None:
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        f"{op} instruction missing result target",
                        "Regenerate TAC to include a destination temporary.",
                    )

                try:
                    memory[ins.result] = self._apply_binary_op(op, left, right)
                except Exception as exc:  # pragma: no cover - defensive runtime safety
                    suggestion = "Review operand values for this operation."
                    if "division by zero" in str(exc) or "modulo by zero" in str(exc):
                        suggestion = "Ensure the divisor is not zero before performing division or modulo."
                    return self._instruction_error(
                        output,
                        memory,
                        ins,
                        f"Runtime error in op '{op}': {exc}",
                        suggestion,
                    )

                pc += 1
                continue

            return self._instruction_error(
                output,
                memory,
                ins,
                f"Unsupported TAC operation: {op}",
                "Regenerate TAC to ensure only supported operations are emitted.",
            )

        return ExecutionResult(output, memory, None)

    def _index_labels(self, instructions: List[TACInstruction]) -> Dict[str, int]:
        labels: Dict[str, int] = {}
        for idx, ins in enumerate(instructions):
            if ins.op == "LABEL" and ins.result is not None:
                labels[ins.result] = idx
        return labels

    def _resolve_operand(self, operand: Optional[str], memory: Dict[str, Any]):
        if operand is None:
            return RuntimeError("Missing operand")

        if operand in memory:
            return memory[operand]

        if operand.startswith('"') and operand.endswith('"') and len(operand) >= 2:
            return operand[1:-1]

        if operand == "true":
            return True
        if operand == "false":
            return False

        try:
            if "." in operand:
                return float(operand)
            return int(operand)
        except ValueError:
            pass

        return RuntimeError(f"Undefined runtime value for operand: {operand}")

    def _instruction_error(
        self,
        output: List[str],
        memory: Dict[str, Any],
        instruction: TACInstruction,
        message: str,
        suggestion: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            output=output,
            memory=memory,
            runtime_error=message,
            runtime_error_suggestion=suggestion,
            runtime_error_line=instruction.line,
            runtime_error_column=instruction.column,
        )

    def _is_hashable(self, value: Any) -> bool:
        try:
            hash(value)
        except TypeError:
            return False
        return True

    def _apply_binary_op(self, op: str, left: Any, right: Any):
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            if right == 0:
                raise ZeroDivisionError("division by zero")
            return left / right
        if op == "%":
            if right == 0:
                raise ZeroDivisionError("modulo by zero")
            return left % right
        if op == "<":
            return left < right
        if op == "<=":
            return left <= right
        if op == ">":
            return left > right
        if op == ">=":
            return left >= right
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "&&":
            return bool(left) and bool(right)
        if op == "||":
            return bool(left) or bool(right)
        raise ValueError(f"Unknown binary op: {op}")
