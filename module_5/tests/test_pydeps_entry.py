# Tests for _pydeps_entry (pydeps dependency graph entry point)

import pytest


@pytest.mark.analysis
def test_pydeps_entry_imports():
    """Import _pydeps_entry so it is covered; used by pydeps for dependency graph."""
    import _pydeps_entry
    assert _pydeps_entry._DEPS is not None
    assert len(_pydeps_entry._DEPS) == 7
