"""
run with
$ pytest -v -s test_consistency
"""

from tqdm import tqdm
import pytest
from merkle_config import deploy, call


log2 = {0: 0, 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 3, 7: 3, 8: 4}
closest = {0: 0, 1: 0, 2: 1, 3: 2, 4: 2, 5: 4, 6: 4, 7: 4, 8: 4, 9: 8, 10: 8}


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """
    global interface
    global backend
    global data
    global start
    global step
    size = 33
    start = 1
    step = 1
    data = []
    for i in range(size):
        data.append(int(i).to_bytes(32, "big"))

    backend = "ganache"
    interface = deploy()


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test is finished
    """

    yield
    session = request.session
    interface = deploy(backend=backend)
    interface.end()


def test_log2_ceiling(init_environment):

    for l in tqdm(log2.keys()):
        assert log2_ceiling(l)["result"] == log2[l]


def test_closest_pow_of_2(init_environment):

    for c in tqdm(closest.keys()):
        assert closest_pow_of_2(c)["result"] == closest[c]


def test_merkle_proof(init_environment):

    _root = call(interface, "merkleTreeHash", [data])["result"]
    for index in tqdm(range(start, len(data), step), desc="Testing paths"):
        merkle_proof, siblings = call(interface, "path", [data, index])[
            "result"
        ]
        root = call(
            interface,
            "rootFromPath",
            [index.to_bytes(32, "big"), merkle_proof, siblings],
        )["result"]
        assert root == _root


def test_consistency_proof(init_environment):

    root1 = call(interface, "merkleTreeHash", [data])["result"]
    for m in tqdm(
        range(start, len(data), step), desc="Testing consistency proof"
    ):
        root0 = call(interface, "merkleTreeHash", [data[:m]])["result"]
        consistency_proof = call(interface, "consProofSub", [data, m])[
            "result"
        ]
        res = call(
            interface,
            "verifyConsistencyProof",
            [consistency_proof, root0, m, root1, len(data)],
        )["result"]
        assert res == True
