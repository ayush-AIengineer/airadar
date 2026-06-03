"""Maps a source's ``adapter_class`` string (stored in the DB registry) to its class.

New adapters register here. The Discovery agent uses this to instantiate the right
adapter for each enabled source row.
"""

from __future__ import annotations

from airadar.sources.base import SourceAdapter
from airadar.sources.hackernews import HackerNewsAdapter

# adapter_class name -> adapter type
_REGISTRY: dict[str, type] = {
    "HackerNewsAdapter": HackerNewsAdapter,
}


def get_adapter(adapter_class: str) -> SourceAdapter:
    try:
        cls = _REGISTRY[adapter_class]
    except KeyError as exc:
        raise ValueError(f"Unknown adapter_class: {adapter_class!r}") from exc
    adapter: SourceAdapter = cls()
    return adapter


def known_adapters() -> list[str]:
    return sorted(_REGISTRY)
