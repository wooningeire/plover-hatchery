from typing import final, TypedDict


HatcheryDictionaryMetaContents = TypedDict("HatcheryDictionaryMetaContents", {
    "hatchery-format-version": str,
})

@final
class HatcheryDictionaryContents(TypedDict):
    meta: HatcheryDictionaryMetaContents
    morphemes: dict[str, str]
    entries: dict[str, str]
