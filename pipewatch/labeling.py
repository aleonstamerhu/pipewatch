"""Pipeline labeling: assign and query free-form key-value labels on pipelines."""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterator, List, Optional, Tuple


class LabelStore:
    """Stores key-value labels per pipeline."""

    def __init__(self) -> None:
        # pipeline_name -> {key: value}
        self._labels: Dict[str, Dict[str, str]] = defaultdict(dict)

    def set(self, pipeline: str, key: str, value: str) -> None:
        """Set a label on a pipeline. Keys and values are stored as-is."""
        if not pipeline:
            raise ValueError("pipeline name must not be empty")
        if not key:
            raise ValueError("label key must not be empty")
        self._labels[pipeline][key] = value

    def remove(self, pipeline: str, key: str) -> bool:
        """Remove a label key from a pipeline. Returns True if it existed."""
        return self._labels[pipeline].pop(key, None) is not None

    def get(self, pipeline: str, key: str) -> Optional[str]:
        """Return the value for a label key, or None."""
        return self._labels.get(pipeline, {}).get(key)

    def get_all(self, pipeline: str) -> Dict[str, str]:
        """Return all labels for a pipeline as a dict copy."""
        return dict(self._labels.get(pipeline, {}))

    def pipelines_with_label(self, key: str, value: Optional[str] = None) -> List[str]:
        """Return pipelines that have a given label key (optionally matching value)."""
        result = []
        for pipeline, labels in self._labels.items():
            if key in labels:
                if value is None or labels[key] == value:
                    result.append(pipeline)
        return sorted(result)

    def all_pipelines(self) -> List[str]:
        """Return all pipelines that have at least one label."""
        return sorted(p for p, labels in self._labels.items() if labels)

    def iter_labels(self) -> Iterator[Tuple[str, str, str]]:
        """Yield (pipeline, key, value) for every stored label."""
        for pipeline, labels in self._labels.items():
            for key, value in labels.items():
                yield pipeline, key, value

    def clear_pipeline(self, pipeline: str) -> int:
        """Remove all labels from a pipeline. Returns count removed."""
        removed = len(self._labels.get(pipeline, {}))
        self._labels.pop(pipeline, None)
        return removed
