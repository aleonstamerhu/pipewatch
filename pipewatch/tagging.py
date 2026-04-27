"""Pipeline tagging: attach and query metadata tags on pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class TagStore:
    """In-memory store mapping pipeline names to sets of tags."""

    _tags: Dict[str, Set[str]] = field(default_factory=dict)

    def add(self, pipeline: str, *tags: str) -> None:
        """Add one or more tags to a pipeline."""
        if not pipeline:
            raise ValueError("pipeline name must not be empty")
        for tag in tags:
            if not tag or not tag.strip():
                raise ValueError("tag must not be empty or whitespace")
        self._tags.setdefault(pipeline, set()).update(t.strip().lower() for t in tags)

    def remove(self, pipeline: str, tag: str) -> bool:
        """Remove a tag from a pipeline. Returns True if the tag existed."""
        tag = tag.strip().lower()
        bucket = self._tags.get(pipeline, set())
        if tag in bucket:
            bucket.discard(tag)
            if not bucket:
                del self._tags[pipeline]
            return True
        return False

    def get(self, pipeline: str) -> List[str]:
        """Return sorted list of tags for a pipeline."""
        return sorted(self._tags.get(pipeline, set()))

    def pipelines_with_tag(self, tag: str) -> List[str]:
        """Return sorted list of pipeline names that carry the given tag."""
        tag = tag.strip().lower()
        return sorted(p for p, tags in self._tags.items() if tag in tags)

    def all_tags(self) -> List[str]:
        """Return sorted list of all unique tags across all pipelines."""
        return sorted({t for tags in self._tags.values() for t in tags})

    def clear(self, pipeline: Optional[str] = None) -> None:
        """Clear tags for a specific pipeline, or all pipelines if None."""
        if pipeline is None:
            self._tags.clear()
        else:
            self._tags.pop(pipeline, None)


_default_store: Optional[TagStore] = None


def get_store() -> TagStore:
    """Return the module-level default TagStore (created on first call)."""
    global _default_store
    if _default_store is None:
        _default_store = TagStore()
    return _default_store
