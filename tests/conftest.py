from typing import cast

import pytest


@pytest.fixture(params=[False, True])
def send_leading_end_byte(request: pytest.FixtureRequest) -> bool:
    return cast(bool, request.param)


@pytest.fixture(params=[False, True])
def receive_leading_end_byte(request: pytest.FixtureRequest) -> bool:
    return cast(bool, request.param)
