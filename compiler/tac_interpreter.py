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
                    return ExecutionResult(output, memory, f"Unknown label in GOTO: {ins.result}")
                pc = labels[ins.result]
                continue

            if op == "IF_FALSE_GOTO":
                condition = self._resolve_operand(ins.arg1, memory)
                if isinstance(condition, RuntimeError):
                    return ExecutionResult(output, memory, str(condition))
                if not bool(condition):
                    if ins.result not in labels:
                        return ExecutionResult(
                            output,
                            memory,
                            f"Unknown label in IF_FALSE_GOTO: {ins.result}",
                        )
                    pc = labels[ins.result]
                    continue
                pc += 1
                continue

            if op == "ASSIGN":
                value = self._resolve_operand(ins.arg1, memory)
                if isinstance(value, RuntimeError):
                    return ExecutionResult(output, memory, str(value))
                if ins.result is None:
                    return ExecutionResult(output, memory, "ASSIGN instruction missing result target")
                memory[ins.result] = value
                pc += 1
                continue

            if op == "ARRAY_NEW":
                if ins.result is None:
                    return ExecutionResult(output, memory, "ARRAY_NEW instruction missing result target")
                memory[ins.result] = []
                pc += 1
                continue

            if op == "ARRAY_APPEND":
                if ins.result is None:
                    return ExecutionResult(output, memory, "ARRAY_APPEND instruction missing result target")
                container_value = memory.get(ins.result)
                if not isinstance(container_value, list):
                    return ExecutionResult(output, memory, "ARRAY_APPEND target is not an array")
                value = self._resolve_operand(ins.arg2, memory)
                if isinstance(value, RuntimeError):
                    return ExecutionResult(output, memory, str(value))
                container_value.append(value)
                pc += 1
                continue

            if op == "DICT_NEW":
                if ins.result is None:
                    return ExecutionResult(output, memory, "DICT_NEW instruction missing result target")
                memory[ins.result] = {}
                pc += 1
                continue

            if op == "DICT_SET":
                if ins.result is None:
                    return ExecutionResult(output, memory, "DICT_SET instruction missing result target")
                container_value = memory.get(ins.result)
                if not isinstance(container_value, dict):
                    return ExecutionResult(output, memory, "DICT_SET target is not a dictionary")
                key = self._resolve_operand(ins.arg1, memory)
                value = self._resolve_operand(ins.arg2, memory)
                if isinstance(key, RuntimeError):
                    return ExecutionResult(output, memory, str(key))
                if isinstance(value, RuntimeError):
                    return ExecutionResult(output, memory, str(value))
                container_value[key] = value
                pc += 1
                continue

            if op == "INDEX_GET":
                collection = self._resolve_operand(ins.arg1, memory)
                index = self._resolve_operand(ins.arg2, memory)
                if isinstance(collection, RuntimeError):
                    return ExecutionResult(output, memory, str(collection))
                if isinstance(index, RuntimeError):
                    return ExecutionResult(output, memory, str(index))
                if ins.result is None:
                    return ExecutionResult(output, memory, "INDEX_GET instruction missing result target")
                try:
                    memory[ins.result] = collection[index]
                except Exception as exc:  # pragma: no cover - defensive runtime safety
                    return ExecutionResult(output, memory, f"Runtime error in INDEX_GET: {exc}")
                pc += 1
                continue

            if op == "PRINT":
                value = self._resolve_operand(ins.arg1, memory)
                if isinstance(value, RuntimeError):
                    return ExecutionResult(output, memory, str(value))
                output.append(str(value))
                pc += 1
                continue

            if op in {"NEG", "NOT"}:
                operand = self._resolve_operand(ins.arg1, memory)
                if isinstance(operand, RuntimeError):
                    return ExecutionResult(output, memory, str(operand))
                if ins.result is None:
                    return ExecutionResult(output, memory, f"{op} instruction missing result target")
                if op == "NEG":
                    if not isinstance(operand, (int, float)):
                        return ExecutionResult(output, memory, "NEG requires numeric operand")
                    memory[ins.result] = -operand
                else:
                    memory[ins.result] = not bool(operand)
                pc += 1
                continue

            if op in {"+", "-", "*", "/", "%", "<", "<=", ">", ">=", "==", "!=", "&&", "||"}:
                left = self._resolve_operand(ins.arg1, memory)
                right = self._resolve_operand(ins.arg2, memory)
                if isinstance(left, RuntimeError):
                    return ExecutionResult(output, memory, str(left))
                if isinstance(right, RuntimeError):
                    return ExecutionResult(output, memory, str(right))
                if ins.result is None:
                    return ExecutionResult(output, memory, f"{op} instruction missing result target")

                try:
                    memory[ins.result] = self._apply_binary_op(op, left, right)
                except Exception as exc:  # pragma: no cover - defensive runtime safety
                    return ExecutionResult(output, memory, f"Runtime error in op '{op}': {exc}")

                pc += 1
                continue

            return ExecutionResult(output, memory, f"Unsupported TAC operation: {op}")

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
