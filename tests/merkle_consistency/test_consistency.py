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


def test_closest_pow_of_2(init_environment):

    assert closest_pow_of_2(1)["result"] == 0
    assert closest_pow_of_2(2)["result"] == 1
    assert closest_pow_of_2(3)["result"] == 2
    assert closest_pow_of_2(4)["result"] == 2
    assert closest_pow_of_2(5)["result"] == 4
    assert closest_pow_of_2(6)["result"] == 4
    assert closest_pow_of_2(7)["result"] == 4
    assert closest_pow_of_2(8)["result"] == 4
    assert closest_pow_of_2(9)["result"] == 8
    assert closest_pow_of_2(10)["result"] == 8


def test_merkle_tree_hash(init_environment):

    root = merkle_tree_hash(data)["result"]
    rec_path = merkle_tree_hash_rec(data)["result"]
    assert root == rec_path

    for index in tqdm(range(1, len(data), step), desc="Testing paths"):
        merkle_proof = path(data, index)["result"]
        _root = root_from_path(merkle_proof, len(data), index)["result"]
        assert root == _root
