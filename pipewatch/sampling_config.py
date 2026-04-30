"""Load SamplingPolicy from a YAML configuration file."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from pipewatch.sampling import SamplingPolicy


@dataclass
class SamplingConfig:
    default: SamplingPolicy
    overrides: Dict[str, SamplingPolicy]

    def policy_for(self, pipeline: str) -> SamplingPolicy:
        """Return the pipeline-specific policy, or the default."""
        return self.overrides.get(pipeline, self.default)


def _parse_policy(data: Dict[str, Any]) -> SamplingPolicy:
    return SamplingPolicy(
        max_samples=int(data.get("max_samples", 50)),
        min_interval_seconds=float(data.get("min_interval_seconds", 0.0)),
    )


def parse_sampling_config(data: Dict[str, Any]) -> SamplingConfig:
    """Parse a dict (e.g. from YAML) into a SamplingConfig."""
    default_data = data.get("default", {})
    default_policy = _parse_policy(default_data)

    overrides: Dict[str, SamplingPolicy] = {}
    for pipeline, override_data in data.get("overrides", {}).items():
        if not isinstance(pipeline, str) or not pipeline.strip():
            raise ValueError(f"Invalid pipeline name in overrides: {pipeline!r}")
        overrides[pipeline] = _parse_policy(override_data)

    return SamplingConfig(default=default_policy, overrides=overrides)


def load_from_yaml(path: str) -> SamplingConfig:
    """Load a SamplingConfig from a YAML file."""
    if yaml is None:  # pragma: no cover
        raise RuntimeError("PyYAML is required to load sampling config from YAML.")
    with open(path, "r") as fh:
        data = yaml.safe_load(fh) or {}
    return parse_sampling_config(data)
