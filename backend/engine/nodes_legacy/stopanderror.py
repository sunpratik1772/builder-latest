"""STOP_AND_ERROR node raising workflow exceptions."""
from __future__ import annotations

from pathlib import Path
import json

from ..context import RunContext
from ..node_spec import NodeSpec, _spec_from_yaml


def handle_stopanderror(node: dict, ctx: RunContext) -> None:
    """Raise configured error message or object."""
    node_id = node.get("id", "stopanderror")
    cfg = node.get("config", {}) or {}
    error_type = str(cfg.get("errorType", cfg.get("error_type", "errorMessage")))
    if error_type == "errorObject":
        err_obj = cfg.get("errorObject", cfg.get("error_object", {}))
        if isinstance(err_obj, str):
            try:
                err_obj = json.loads(err_obj)
            except Exception:
                err_obj = {"message": err_obj}
        message = str((err_obj or {}).get("message", "Workflow stopped with error object"))
        code = (err_obj or {}).get("code")
        ex = RuntimeError(message)
        if code is not None:
            ex.args = (*ex.args, {"code": code, "error": err_obj})
        raise ex
    message = str(cfg.get("errorMessage", cfg.get("error_message", "An error occurred!")))
    raise RuntimeError(message)



NODE_SPEC: NodeSpec = _spec_from_yaml(Path(__file__).with_suffix('.yaml'), handle_stopanderror)
