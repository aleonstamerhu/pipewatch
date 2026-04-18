"""Load and validate scheduler configuration from YAML/dict."""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class JobConfig:
    pipeline_name: str
    interval_seconds: int

    def validate(self) -> None:
        if not self.pipeline_name:
            raise ValueError("pipeline_name must not be empty")
        if self.interval_seconds <= 0:
            raise ValueError(f"interval_seconds must be positive, got {self.interval_seconds}")


def parse_job_configs(raw: List[Dict[str, Any]]) -> List[JobConfig]:
    """Parse a list of raw dicts into validated JobConfig objects."""
    configs = []
    for entry in raw:
        cfg = JobConfig(
            pipeline_name=entry.get("pipeline_name", ""),
            interval_seconds=int(entry.get("interval_seconds", 0)),
        )
        cfg.validate()
        configs.append(cfg)
    return configs


def load_from_yaml(path: str) -> List[JobConfig]:
    """Load job configs from a YAML file."""
    import yaml  # optional dependency
    with open(path, "r") as f:
        data = yaml.safe_load(f) or {}
    raw_jobs = data.get("jobs", [])
    return parse_job_configs(raw_jobs)
