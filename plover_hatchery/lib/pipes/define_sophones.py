from enum import Enum


def define_sophones(sophone_names: str):
    return Enum("Sophone", {
        name: i
        for i, name in enumerate(sophone_names.split())
    })