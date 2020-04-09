"""
run with
$ pytest -v -s test_verifier
"""

import sys

sys.path.append("../../tools/proof/")
from proof import Proof
from create_proof import ProofTool

from tqdm import tqdm
import pytest
from verifier_config import deploy, call


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """
    global backend
    backend = "geth"

    global submit_proof
    global small_contest_proof
    global small_lca
    pt = ProofTool()
    (
        submit_proof_name,
        small_contest_proof_name,
        small_lca,
        small_header,
        small_header_map,
        small_interlink_map,
    ) = pt.create_proof_and_forkproof(500000, 100000, 200000)
    submit_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))

    small_contest_proof = Proof()
    small_contest_proof.set(
        pt.fetch_proof(small_contest_proof_name),
        header=small_header,
        header_map=small_header_map,
        interlink_map=small_interlink_map,
    )


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test is finished
    """

    yield
    session = request.session
    interface = deploy(backend=backend)
    interface.end()


def test_consistent_proof(init_environment):

    interface = deploy(
        {"path": "../../contracts/lib/Merkle.sol", "ctor": [1]},
        libraries=[
            "../../contracts/lib/Math.sol",
            "../../contracts/lib/Arrays.sol",
            "../../contracts/lib/Merkle.sol",
        ],
        backend=backend,
    )

    merkle_root_0 = call(
        interface, "merkleTreeHash", [submit_proof.hashed_headers[:small_lca]]
    )["result"]

    merkle_root_1 = call(
        interface, "merkleTreeHash", [submit_proof.hashed_headers]
    )["result"]

    consistency_proof = call(
        interface, "consProofSub", [submit_proof.hashed_headers, small_lca],
    )["result"]

    res = call(
        interface,
        "verifyConsistencyProof",
        [
            consistency_proof,
            merkle_root_0,
            small_lca,
            merkle_root_1,
            submit_proof.size,
        ],
    )["result"]
    assert res == True


def test_consistent_contest(init_environment):

    interface = deploy(
        {"path": "../../contracts/lib/Merkle.sol", "ctor": [1]},
        libraries=[
            "../../contracts/lib/Math.sol",
            "../../contracts/lib/Arrays.sol",
            "../../contracts/lib/Merkle.sol",
        ],
        backend=backend,
    )
    consistency_proof = call(
        interface, "consProofSub", [submit_proof.hashed_headers, small_lca+1],
    )["result"]

    interface = deploy(backend=backend)
    res = call(
        interface,
        "submitEventProof",
        [submit_proof.headers, submit_proof.siblings, submit_proof.size - 1,],
    )["result"]
    assert res == True

    res = call(
        interface,
        "submitContestingProof",
        [
            submit_proof.hashed_headers[:small_lca+1],
            consistency_proof,
            small_contest_proof.best_level_subproof_headers,
            small_contest_proof.best_level_subproof_siblings,
            small_contest_proof.best_level,
            submit_proof.hashed_headers[-1],
        ],
        0
    )

    print(res["gas"])

    assert res["result"] == True
