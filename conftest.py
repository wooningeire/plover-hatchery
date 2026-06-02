# Copied from https://github.com/openstenoproject/plover_python_dictionary/blob/master/test/conftest.py

import pytest

from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


def _setup_plover() -> None:
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)


# Some modules build Stroke constants while pytest is still importing tests.
_setup_plover()

pytest.register_assert_rewrite('plover_build_utils.testing')
