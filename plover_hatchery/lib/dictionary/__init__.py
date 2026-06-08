from .read import (
    HatcheryEntry,
    all_entries,
    entry_items,
    read_hatchery_dictionary,
)


def generate_from_unilex(*args, **kwargs):
    from .generate_from_unilex import generate_from_unilex as _generate_from_unilex

    return _generate_from_unilex(*args, **kwargs)
