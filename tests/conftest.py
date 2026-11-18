import os

import pytest

from platform_app.config import Settings
from platform_app.generate import generate


@pytest.fixture(scope="session")
def sample(tmp_path_factory):
    config = Settings(root=tmp_path_factory.mktemp("synthetic"), users=120)
    manifest = generate(config)
    return config, manifest


def pytest_collection_modifyitems(config, items):
    if os.getenv("RUN_INTEGRATION") != "1":
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(
                    pytest.mark.skip(
                        reason="Set RUN_INTEGRATION=1 after running the PostgreSQL pipeline"
                    )
                )
