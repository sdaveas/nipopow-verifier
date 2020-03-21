"""
run with
$ pytest -v -s test_dispute_existing.py
"""

import sys

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool
from edit_chain import change_interlink_hash

from contract_api import (
    make_interface,
    submit_event_proof,
    dispute_existing_proof,
)
from config import errors, extract_message_from_error, genesis

import pytest


backend = "geth"


@pytest.fixture
def init_environment():
    pass


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after every test
    """

    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()


def test_dispute_valid(init_environment):
    """
    Try to dispute valid proof
    """

    block_of_interest_index = 0
    pt = ProofTool("../data/proofs/")
    proof = Proof()
    proof.set(pt.fetch_proof(500000))

    interface = make_interface(backend)

    res = submit_event_proof(interface, proof, block_of_interest_index, profile=True)

    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = dispute_existing_proof(
            interface, proof, block_of_interest_index, 1, proof.size - 1, profile=True
        )
    assert extract_message_from_error(ex) == errors["valid existing"]


def test_dispute_invalid(init_environment):
    """
    Try to dispute valid proof
    """

    interface = make_interface(backend)
    block_of_interest_index = 0
    pt = ProofTool("../data/proofs/")
    original_proof = pt.fetch_proof(500)

    invalid_index = int(len(original_proof) / 2)
    print("invalid index:", invalid_index)
    invalid_proof = Proof()
    invalid_proof.set(change_interlink_hash(original_proof, invalid_index))

    res = submit_event_proof(
        interface, invalid_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    res = dispute_existing_proof(
        interface,
        invalid_proof,
        block_of_interest_index,
        invalid_index_start=invalid_index,
        invalid_index_stop=invalid_index,
        profile=True,
    )
    assert res["result"] == True
