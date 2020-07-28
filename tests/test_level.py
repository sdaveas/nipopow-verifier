"""
run with
$ pytest -v -s test_level.py
"""

import sys
import pytest
from tqdm import tqdm

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool
from create_blockchain_new import CBlockHeaderPopow, Hash

from contract_api import make_interface


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global interface
    interface = make_interface("ganache")

    mainblocks = 100
    fork_index = 50
    forkblocks = 100
    pt = ProofTool("../data/proofs/")
    (
        proof_name,
        fork_name,
        lca,
        fork_header,
        fork_header_map,
        fork_interlink_map,
    ) = pt.create_proof_and_forkproof(mainblocks, fork_index, forkblocks)

    global proof
    proof = Proof()
    proof.set(pt.fetch_proof_by_name(proof_name))

    global fork
    fork = Proof()
    fork.set(
        pt.fetch_proof_by_name(fork_name),
        header=fork_header,
        header_map=fork_header_map,
        interlink_map=fork_interlink_map,
    )


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test is finished
    """

    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface("ganache")
    interface.end()


def test_level(init_environment):

    """
    Test level computation
    """

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


def test_scores(init_environment):

    """
    Test score computation
    """

    score_from_solidity = interface.call(
        "bestArg", function_args=[proof.hashed_headers, proof.size]
    )["result"]
    assert score_from_solidity == proof.best_score

    fork_hashed_headers = []
    for (h, _) in fork.best_level_subproof:
        fork_hashed_headers.append(Hash(h))
    score_from_solidity = interface.call(
        "bestArg",
        function_args=[fork_hashed_headers, len(fork_hashed_headers)],
    )["result"]
    assert score_from_solidity == fork.best_score

    score_from_solidity = interface.call(
        "argAtLevel", function_args=[fork_hashed_headers, fork.best_level]
    )["result"]
    assert score_from_solidity == fork.best_score
