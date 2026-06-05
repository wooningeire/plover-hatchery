from .read import read_hatchery_dictionary, all_entries


def generate_from_unilex(*args, **kwargs):
    from .generate_from_unilex import generate_from_unilex as _generate_from_unilex

    return _generate_from_unilex(*args, **kwargs)
