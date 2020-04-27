"""
run with
$ pytest -v -s test_level.py
"""

import sys
import pytest
from tqdm import tqdm

sys.path.append("../tools/interface/")
import contract_interface

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool
from create_blockchain_new import CBlockHeaderPopow

from contract_api import make_interface


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global interface
    interface = make_interface("ganache")

    global proof
    blocks = 100
    proof = Proof()
    proof.set(ProofTool("../data/proofs/").fetch_proof(blocks))


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test is finished
    """

    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface.end()


def test_sufficient_collateral(init_environment):
    """
    Test contract call with sufficient collateral
    """

    from collections import defaultdict

    levels = defaultdict(lambda: 0)

    for index in tqdm(range(proof.size)):
        hashed_header = proof.hashed_headers[index].hex()
        level_from_solidity = interface.call(
            "getLevel", function_args=[hashed_header]
        )["result"]

        header, _ = proof.proof[index]
        level_from_python = CBlockHeaderPopow.deserialize(
            header
        ).compute_level()

        assert level_from_solidity == level_from_python
