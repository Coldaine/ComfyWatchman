"""
Integration tests are temporarily disabled for legacy web-search paths.
The project now relies on Qwen's internal web_search capability; these
older integration flows will be reworked in a future PR.
"""

import pytest

pytest.skip(
    "Integration tests disabled: legacy web-search paths removed.",
    allow_module_level=True,
)