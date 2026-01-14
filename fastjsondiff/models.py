"""
Data models for fastjsondiff results.

This module defines the public-facing types returned by comparison operations.
"""
import typing as t
from dataclasses import dataclass, field
from enum import Enum
import json


class DiffType(Enum):
    """Types of differences that can be detected."""

    ADDED = "added"
    """Key or element exists in second input but not first."""

    REMOVED = "removed"
    """Key or element exists in first input but not second."""

    CHANGED = "changed"
    """Value differs between inputs at the same path."""


@dataclass
class Difference:
    """A single difference between two JSON values."""

    type: DiffType
    """Type of change: added, removed, or changed."""

    path: str
    """JSON path to the difference location (e.g., 'root.items[0].name')."""

    old_value: t.Any = None
    """Previous value (None for 'added' type)."""

    new_value: t.Any = None
    """New value (None for 'removed' type)."""

    def to_dict(self) -> dict[str, str]:
        """Serialize to dictionary."""
        result = {
            "type": self.type.value,
            "path": self.path,
        }
        if self.old_value is not None:
            result["old_value"] = self.old_value
        if self.new_value is not None:
            result["new_value"] = self.new_value
        return result

    def __repr__(self) -> str:
        parts = [f"type={self.type.value!r}", f"path={self.path!r}"]
        if self.old_value is not None:
            parts.append(f"old_value={self.old_value!r}")
        if self.new_value is not None:
            parts.append(f"new_value={self.new_value!r}")
        return f"Difference({', '.join(parts)})"


@dataclass
class DiffSummary:
    """Summary counts of differences by type."""

    added: int = 0
    """Count of added keys/elements."""

    removed: int = 0
    """Count of removed keys/elements."""

    changed: int = 0
    """Count of changed values."""

    @property
    def total(self) -> int:
        """Total number of differences."""
        return self.added + self.removed + self.changed

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "added": self.added,
            "removed": self.removed,
            "changed": self.changed,
            "total": self.total,
        }


@dataclass
class DiffMetadata:
    """Metadata about the comparison operation."""

    paths_compared: int = 0
    """Total number of JSON paths visited during comparison."""

    max_depth: int = 0
    """Maximum nesting depth encountered."""

    duration_ms: float = 0.0
    """Time taken for comparison in milliseconds."""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "paths_compared": self.paths_compared,
            "max_depth": self.max_depth,
            "duration_ms": self.duration_ms,
        }


@dataclass
class DiffResult:
    """Complete result of a JSON comparison operation."""

    differences: list[Difference] = field(default_factory=list)
    """Ordered list of all detected differences."""

    summary: DiffSummary = field(default_factory=DiffSummary)
    """Aggregate counts by difference type."""

    metadata: DiffMetadata = field(default_factory=DiffMetadata)
    """Information about the comparison operation."""

    def __len__(self) -> int:
        """Number of differences found."""
        return len(self.differences)

    def __iter__(self) -> t.Iterator[Difference]:
        """Iterate over differences."""
        return iter(self.differences)

    def __bool__(self) -> bool:
        """True if any differences exist."""
        return len(self.differences) > 0

    def __getitem__(self, index: int) -> Difference:
        """Get difference by index."""
        return self.differences[index]

    def filter(self, diff_type: DiffType | None = None) -> list[Difference]:
        """
        Filter differences by type.

        Args:
            diff_type: Type to filter by, or None for all differences

        Returns:
            List of differences matching the filter
        """
        if diff_type is None:
            return list(self.differences)
        return [d for d in self.differences if d.type == diff_type]

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON export."""
        return {
            "differences": [d.to_dict() for d in self.differences],
            "summary": self.summary.to_dict(),
            "metadata": self.metadata.to_dict(),
        }

    def to_json(self, indent: int | None = None) -> str:
        """
        Serialize to JSON string.

        Args:
            indent: Indentation level for pretty-printing

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def __repr__(self) -> str:
        return (
            f"DiffResult(differences={len(self.differences)}, "
            f"summary={self.summary.to_dict()})"
        )


class InvalidJsonError(ValueError):
    """Raised when input is not valid JSON."""

    def __init__(
        self,
        message: str,
        *,
        input_name: str = "unknown",
        position: int | None = None,
        line: int | None = None,
        column: int | None = None,
    ):
        self.message = message
        self.input_name = input_name
        self.position = position
        self.line = line
        self.column = column

        # Build error message
        parts = [message]
        if input_name != "unknown":
            parts.append(f"(input: {input_name})")
        if line is not None and column is not None:
            parts.append(f"at line {line}, column {column}")
        elif position is not None:
            parts.append(f"at position {position}")

        super().__init__(" ".join(parts))
