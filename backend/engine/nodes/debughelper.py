"""DEBUG_HELPER node for synthetic failures/data generation."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import random
import uuid

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def _to_list(v: Any) -> list[Any]:
    if isinstance(v, list):
        return v
    return [v] if v is not None else []


def _random_user() -> dict[str, Any]:
    first = random.choice(["Ana", "Sam", "Lia", "Kai", "Ravi"])
    last = random.choice(["Miller", "Singh", "Chen", "Lopez", "Ibrahim"])
    return {
        "firstName": first,
        "lastName": last,
        "email": f"{first.lower()}.{last.lower()}@example.com",
    }


def handle_debughelper(node: dict, ctx: RunContext) -> None:
    """Execute selected debug category operation."""
    node_id = node.get("id", "debughelper")
    cfg = node.get("config", {}) or {}
    items = _to_list(ctx.get(f"{node_id}_input", []))
    category = str(cfg.get("category", "throwError"))
    out: list[dict[str, Any]] = []

    if category == "doNothing":
        out = [x if isinstance(x, dict) else {"value": x} for x in items]
        ctx.set(f"{node_id}_output", out)
        return

    if category == "throwError":
        err_type = str(cfg.get("throwErrorType", cfg.get("error_type", "Error")))
        message = str(cfg.get("throwErrorMessage", cfg.get("error_message", "Node has thrown an error")))
        if err_type == "NodeApiError":
            raise RuntimeError(f"NodeApiError: {message}")
        if err_type == "NodeOperationError":
            raise RuntimeError(f"NodeOperationError: {message}")
        raise RuntimeError(message)

    if category == "oom":
        size = int(cfg.get("memorySizeValue", cfg.get("memory_size_to_generate", 10)) or 10)
        # Avoid real OOM; generate deterministic synthetic stats.
        mem_stats = {
            "requestedMiB": size,
            "allocatedMiB": max(1, min(size, 64)),
            "warning": "simulated_oom_mode",
        }
        out = [{"memory": mem_stats}]
        ctx.set(f"{node_id}_output", out)
        return

    # randomData
    dtype = str(cfg.get("randomDataType", cfg.get("data_type", "user")))
    count = int(cfg.get("randomDataCount", 10) or 10)
    single_array = bool(cfg.get("randomDataSingleArray", False))
    random.seed(str(cfg.get("randomDataSeed", "")) or None)

    generated: list[Any] = []
    for _ in range(max(count, 0)):
        if dtype == "email":
            generated.append({"email": _random_user()["email"]})
        elif dtype == "uuid":
            generated.append({"uuid": str(uuid.uuid4())})
        elif dtype == "ipv4":
            generated.append({"ipv4": ".".join([str(random.randint(1, 254)) for _ in range(4)])})
        elif dtype == "nanoid":
            alphabet = str(cfg.get("nanoidAlphabet", "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            n = int(cfg.get("nanoidLength", "16") or 16)
            generated.append({"nanoid": "".join(random.choice(alphabet) for _ in range(max(1, n)))})
        else:
            generated.append(_random_user())

    if single_array:
        out = [{"generatedItems": generated}]
    else:
        out = [g if isinstance(g, dict) else {"value": g} for g in generated]
    ctx.set(f"{node_id}_output", out)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_debughelper)
