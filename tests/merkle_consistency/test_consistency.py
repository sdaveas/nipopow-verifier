"""
run with
$ pytest -v -s test_consistency
"""

import sys
from tqdm import tqdm
import pytest
from consistency import *


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """
    global data
    global step
    size = 256
    step = 20
    data = []
    for i in range(size):
        data.append(int(i).to_bytes(32, "big"))


def test_log2_ceiling(init_environment):

    assert log2_ceiling(0)["result"] == 0
    assert log2_ceiling(1)["result"] == 1
    assert log2_ceiling(2)["result"] == 2
    assert log2_ceiling(3)["result"] == 2
    assert log2_ceiling(4)["result"] == 3
    assert log2_ceiling(5)["result"] == 3
    assert log2_ceiling(6)["result"] == 3
    assert log2_ceiling(7)["result"] == 3
    assert log2_ceiling(8)["result"] == 4
