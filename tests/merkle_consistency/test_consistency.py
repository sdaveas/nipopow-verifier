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
