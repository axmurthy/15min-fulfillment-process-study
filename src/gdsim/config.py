"""Configuration loading.

The YAML config is the single source of truth for every assumption. We wrap it
in a light attribute-access object so model code reads naturally (cfg.courier.n_couriers)
while keeping the raw dict available for logging/provenance.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


class DotDict(dict):
    """Dict that also supports attribute access, recursively."""

    def __getattr__(self, name: str) -> Any:
        try:
            value = self[name]
        except KeyError as exc:  # pragma: no cover - defensive
            raise AttributeError(name) from exc
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        self[name] = value


def _wrap(obj: Any) -> Any:
    if isinstance(obj, dict):
        return DotDict({k: _wrap(v) for k, v in obj.items()})
    if isinstance(obj, list):
        return [_wrap(v) for v in obj]
    return obj


def load_config(path: str | Path = "config.yaml") -> DotDict:
    """Load a YAML config file into a DotDict."""
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    return _wrap(raw)


def from_dict(raw: dict) -> DotDict:
    """Build a config object from an in-memory dict (used by the DOE runner)."""
    return _wrap(copy.deepcopy(raw))


def apply_overrides(cfg: DotDict, overrides: dict[str, Any]) -> DotDict:
    """Return a deep copy of cfg with dotted-key overrides applied.

    Example: apply_overrides(cfg, {"courier.n_couriers": 6,
                                   "geography.service_radius_km": 2.0})
    """
    new = from_dict(cfg)
    for dotted, value in overrides.items():
        parts = dotted.split(".")
        node = new
        for key in parts[:-1]:
            node = node[key]
        node[parts[-1]] = value
    return new
