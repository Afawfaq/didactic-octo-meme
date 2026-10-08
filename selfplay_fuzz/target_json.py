from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass
class ExecutionResult:
    edges: set[str]
    crashed: bool
    crash_signature: str | None


def _nesting_depth(value: object, depth: int = 0) -> int:
    if isinstance(value, dict):
        return max([depth] + [_nesting_depth(v, depth + 1) for v in value.values()])
    if isinstance(value, list):
        return max([depth] + [_nesting_depth(v, depth + 1) for v in value])
    return depth


def evaluate_input(data: bytes) -> ExecutionResult:
    text = data.decode("utf-8", errors="ignore")
    edges: set[str] = set()
    edges.add(f"len_bucket:{min(len(text) // 8, 16)}")
    if text:
        edges.add(f"prefix:{text[0]}")
    if "\\" in text:
        edges.add("contains_escape")

    try:
        parsed = json.loads(text)
        edges.add("json_valid")
        edges.add(f"type:{type(parsed).__name__}")
        if isinstance(parsed, dict):
            edges.add(f"dict_keys_bucket:{min(len(parsed), 10)}")
            if any(str(k).startswith("_") for k in parsed):
                edges.add("dict_private_key")
        if isinstance(parsed, list):
            edges.add(f"list_len_bucket:{min(len(parsed), 10)}")
        edges.add(f"depth_bucket:{min(_nesting_depth(parsed), 8)}")

        if isinstance(parsed, dict) and parsed.get("__boom__") == 1337:
            raise RuntimeError("simulated_heap_overflow")
        return ExecutionResult(edges=edges, crashed=False, crash_signature=None)
    except RuntimeError as exc:
        edges.add("runtime_exception")
        return ExecutionResult(edges=edges, crashed=True, crash_signature=f"runtime:{exc}")
    except Exception as exc:  # json parse failures are a normal signal
        edges.add("json_invalid")
        edges.add(type(exc).__name__)
        return ExecutionResult(edges=edges, crashed=False, crash_signature=None)
