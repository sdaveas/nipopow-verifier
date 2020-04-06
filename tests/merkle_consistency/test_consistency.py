"""
run with
$ pytest -v -s test_consistency
"""

from tqdm import tqdm
import pytest
from consistency import (
    log2_ceiling,
    closest_pow_of_2,
    merkle_tree_hash,
    path,
    root_from_path,
    cons_proof_sub,
    root_0_from_const_proof,
    root_1_from_const_proof,
)


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """
    global data
    global start
    global step
    size = 33
    start = 1
    step = 1
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

    assert closest_pow_of_2(0)["result"] == 0
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
    for index in tqdm(range(start, len(data), step), desc="Testing paths"):
        merkle_proof, siblings = path(data, index)["result"]
        _root = root_from_path(index, merkle_proof, siblings)["result"]
        assert root == _root


def test_consistency_proof(init_environment):

    for m in tqdm(
        range(start, len(data), step), desc="Testing consistency for 0"
    ):
        root = merkle_tree_hash(data[:m])["result"]
        consistency_proof = cons_proof_sub(data, m)["result"]
        _root = root_0_from_const_proof(consistency_proof, m, len(data))[
            "result"
        ]
        assert root == _root

    root = merkle_tree_hash(data)["result"]
    for m in tqdm(
        range(start, len(data), step), desc="Testing consistency for 1"
    ):
        consistency_proof = cons_proof_sub(data, m)["result"]
        _root = root_1_from_const_proof(consistency_proof, m, len(data))[
            "result"
        ]
        assert root == _root
