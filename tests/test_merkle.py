"""
run with
$ pytest -v -s test_merkle
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface

from tqdm import tqdm

import pytest

contr_dir = "../contracts/"
lib_dir = contr_dir + "lib/"


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """
    global merkle_iface
    global math_iface
    backend = "ganache"
    merkle_iface = contract_interface.ContractInterface(
        contract={"path": lib_dir + "Merkle.sol", "ctor": []},
        libraries=[lib_dir + "Math.sol", lib_dir + "Arrays.sol",],
        backend=backend,
    )
    math_iface = contract_interface.ContractInterface(
        contract={"path": lib_dir + "Math.sol", "ctor": []}, backend=backend,
    )

    global data
    global start
    global step
    size = 33
    start = 1
    step = 1
    data = []
    for i in range(size):
        data.append(int(i).to_bytes(32, "big"))


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test is finished
    """

    yield
    session = request.session
    merkle_iface.end()
    math_iface.end()


def test_log2_ceiling(init_environment):

    log2_ceiling_results = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 3, 8: 4}
    for l in tqdm(log2_ceiling_results.keys()):
        assert (
            math_iface.call("log2Ceiling", function_args=[l])["result"]
            == log2_ceiling_results[l]
        )


def test_closest_pow_of_2(init_environment):

    closest_pow_of_2_results = {
        0: 0, 1: 0, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 4, 9: 8, 10: 8,
    }
    for c in tqdm(closest_pow_of_2_results.keys()):
        assert (
            math_iface.call("closestPow2", function_args=[c])["result"]
            == closest_pow_of_2_results[c]
        )


def test_merkle_proof(init_environment):

    _root = merkle_iface.call("merkleTreeHash", [data])["result"]
    for index in tqdm(range(start, len(data), step), desc="Testing paths"):
        merkle_proof, siblings = merkle_iface.call("path", [data, index])[
            "result"
        ]
        res = merkle_iface.call(
            "verifyMerkleRoot",
            [_root, index.to_bytes(32, "big"), merkle_proof, siblings],
        )["result"]
        assert res == True


def test_consistency_proof(init_environment):

    root1 = merkle_iface.call("merkleTreeHash", [data])["result"]
    for m in tqdm(
        range(start, len(data), step), desc="Testing consistency proof"
    ):
        root0 = merkle_iface.call("merkleTreeHash", [data[:m]])["result"]
        consistency_proof = merkle_iface.call("consProofSub", [data, m])[
            "result"
        ]
        res = merkle_iface.call(
            "verifyConsistencyProof",
            [consistency_proof, root0, m, root1, len(data)],
        )["result"]
        assert res == True
