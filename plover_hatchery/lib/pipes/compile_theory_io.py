
import hashlib
import pickle

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .compile_theory import TheoryHooks


_COMPILED_LOOKUP_CACHE_VERSION = 1
_COMPILED_LOOKUP_CACHE_PAYLOAD_FORMAT = 2


@dataclass(frozen=True)
class CacheLoadResult:
    loaded: bool
    needs_refresh: bool = False

    def __bool__(self):
        return self.loaded


def compiled_lookup_cache_path(filename: str):
    if filename == "":
        return None

    path = Path(filename)
    return path.with_suffix(f"{path.suffix}.compiled-trie.pickle")


def hash_strings(strings: Iterable[str]):
    digest = hashlib.sha256()
    for string in strings:
        digest.update(len(string).to_bytes(8, "little"))
        digest.update(string.encode("utf-8", "surrogatepass"))
    return digest.hexdigest()


def hash_file(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_compiled_lookup_cache(
    *,
    cache_path: Path,
    source_hash: str,
    source_hash_kind: str,
    prefix_hash: str,
    base_entry_id: int,
    legacy_source_hash_valid: bool,
    hooks: "TheoryHooks",
    states: dict[int, Any],
    translations: list[str],
    reverse_translations: dict[str, list[int]],
    defs_list: list[str],
):
    with cache_path.open("rb") as file:
        payload = pickle.load(file)

    if payload.get("version") != _COMPILED_LOOKUP_CACHE_VERSION:
        return CacheLoadResult(False)

    source_hash_matches = payload.get("source_hash") == source_hash
    source_hash_kind_matches = payload.get("source_hash_kind") in {None, source_hash_kind}
    if not (source_hash_matches and source_hash_kind_matches):
        if not (payload.get("source_hash_kind") is None and legacy_source_hash_valid):
            return CacheLoadResult(False)
    if payload.get("source_hash_kind") is not None and payload.get("source_hash_kind") != source_hash_kind:
        return CacheLoadResult(False)
    if payload.get("prefix_hash") != prefix_hash:
        return CacheLoadResult(False)
    if payload.get("base_entry_id") != base_entry_id:
        return CacheLoadResult(False)

    plugin_cache = payload["plugins"]
    for plugin_id, handler in hooks.import_build_cache.ids_handlers():
        handler(state=states.get(plugin_id), cache=plugin_cache)

    translations[:] = payload["translations"]
    defs_list[:] = payload["defs_list"]
    reverse_translations.clear()
    reverse_translations.update({
        translation: list(entry_ids)
        for translation, entry_ids in payload["reverse_translations"].items()
    })

    return CacheLoadResult(
        True,
        payload.get("payload_format") != _COMPILED_LOOKUP_CACHE_PAYLOAD_FORMAT
        or _plugin_cache_uses_legacy_shape(plugin_cache),
    )


def save_compiled_lookup_cache(
    *,
    cache_path: Path,
    source_hash: str,
    source_hash_kind: str,
    prefix_hash: str,
    base_entry_id: int,
    hooks: "TheoryHooks",
    states: dict[int, Any],
    translations: list[str],
    reverse_translations: dict[str, list[int]],
    defs_list: list[str],
):
    plugin_cache: dict[str, Any] = {}
    for plugin_id, handler in hooks.export_build_cache.ids_handlers():
        result = handler(state=states.get(plugin_id))
        if result is None:
            continue

        cache_key, cache_value = result
        plugin_cache[cache_key] = cache_value

    if len(plugin_cache) == 0:
        return

    payload = {
        "version": _COMPILED_LOOKUP_CACHE_VERSION,
        "payload_format": _COMPILED_LOOKUP_CACHE_PAYLOAD_FORMAT,
        "source_hash": source_hash,
        "source_hash_kind": source_hash_kind,
        "prefix_hash": prefix_hash,
        "base_entry_id": base_entry_id,
        "plugins": plugin_cache,
        "translations": list(translations),
        "reverse_translations": dict(reverse_translations),
        "defs_list": list(defs_list),
    }

    tmp_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
    with tmp_path.open("wb") as file:
        pickle.dump(payload, file, protocol=pickle.HIGHEST_PROTOCOL)
    tmp_path.replace(cache_path)


def _plugin_cache_uses_legacy_shape(plugin_cache: dict[str, Any]):
    for plugin_payload in plugin_cache.values():
        if not isinstance(plugin_payload, dict):
            continue
        if "trie" in plugin_payload or "transition_flags" in plugin_payload:
            return True

    return False


class CompiledLookupCache:
    def __init__(self, *, filename: str, translations: list[str]):
        self.path = compiled_lookup_cache_path(filename)
        self.base_entry_id = len(translations)
        self.prefix_hash = hash_strings(translations)
        self.__source_path = Path(filename) if filename != "" else None
        self.__source_hash = (
            hash_file(self.__source_path)
            if self.__source_path is not None and self.__source_path.exists()
            else None
        )
        self.source_hash_kind = "file_sha256" if self.__source_hash is not None else "entries_sha256"
        self.__source_hasher = hashlib.sha256() if self.__source_hash is None else None

    @property
    def can_load_before_entries(self):
        return self.__source_hash is not None

    def update_source(self, varname: str, definition_str: str):
        if self.__source_hasher is None:
            return

        self.__source_hasher.update(len(varname).to_bytes(8, "little"))
        self.__source_hasher.update(varname.encode("utf-8", "surrogatepass"))
        self.__source_hasher.update(len(definition_str).to_bytes(8, "little"))
        self.__source_hasher.update(definition_str.encode("utf-8", "surrogatepass"))

    @property
    def source_hash(self):
        if self.__source_hash is not None:
            return self.__source_hash

        if self.__source_hasher is None:
            raise RuntimeError("Compiled lookup cache has no source hash")

        return self.__source_hasher.hexdigest()

    @property
    def __legacy_source_hash_valid(self):
        if self.path is None or self.__source_path is None:
            return False
        if not self.path.exists() or not self.__source_path.exists():
            return False

        return self.path.stat().st_mtime_ns >= self.__source_path.stat().st_mtime_ns

    def load(
        self,
        *,
        hooks: Any,
        states: dict[int, Any],
        translations: list[str],
        reverse_translations: dict[str, list[int]],
        defs_list: list[str],
    ):
        if self.path is None or not self.path.exists():
            return False

        return load_compiled_lookup_cache(
            cache_path=self.path,
            source_hash=self.source_hash,
            source_hash_kind=self.source_hash_kind,
            prefix_hash=self.prefix_hash,
            base_entry_id=self.base_entry_id,
            legacy_source_hash_valid=self.__legacy_source_hash_valid,
            hooks=hooks,
            states=states,
            translations=translations,
            reverse_translations=reverse_translations,
            defs_list=defs_list,
        )

    def save(
        self,
        *,
        hooks: Any,
        states: dict[int, Any],
        translations: list[str],
        reverse_translations: dict[str, list[int]],
        defs_list: list[str],
    ):
        if self.path is None:
            return

        save_compiled_lookup_cache(
            cache_path=self.path,
            source_hash=self.source_hash,
            source_hash_kind=self.source_hash_kind,
            prefix_hash=self.prefix_hash,
            base_entry_id=self.base_entry_id,
            hooks=hooks,
            states=states,
            translations=translations,
            reverse_translations=reverse_translations,
            defs_list=defs_list,
        )
