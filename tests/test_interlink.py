"""
run with
$ pytest -v -s test_interlink.py
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool
from edit_chain import change_interlink_hash, skip_blocks
import web3

from contract_api import (
    submit_event_proof,
    submit_contesting_proof,
    make_interface,
    validate_interlink,
)
from config import errors, extract_message_from_error, genesis

import pytest


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global proof
    global changed_interlink_proof
    global missing_blocks_proof
    global replaced_blocks_proof
    backend = "ganache"
    proof = Proof()
    changed_interlink_proof = Proof()
    missing_blocks_proof = Proof()
    replaced_blocks_proof = Proof()

    original_proof = ProofTool("../data/proofs/").fetch_proof(100)
    proof.set(original_proof)

    _changed_interlink_proof = change_interlink_hash(
        original_proof, int(changed_interlink_proof.size / 2)
    )
    changed_interlink_proof.set(_changed_interlink_proof)

    _missing_blocks_proof = original_proof.copy()
    _missing_blocks_proof = skip_blocks(_missing_blocks_proof, -3)
    missing_blocks_proof.set(_missing_blocks_proof)

    _pt = ProofTool()
    _replaced_blocks_proof = _pt.fetch_proof(
        "../data/proofs/proof_100_replaced_mid_block.pkl"
    )
    replaced_blocks_proof.set(_replaced_blocks_proof)


@pytest.fixture(scope="session", autouse=True)
def finish_session(request):
    """
    This runs after ever test
    """

    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()


def test_revert_on_submit(init_environment):
    """
    Submits a proof with block with changed interlink
    """

    interface = make_interface(backend)
    res = validate_interlink(interface, changed_interlink_proof)
    assert res["result"] == False


def test_revert_on_missing_blocks_submit(init_environment):
    """
    Submits a proof with a missing block
    """

    interface = make_interface(backend)

    res = validate_interlink(interface, missing_blocks_proof)
    assert res["result"] == False


def test_replaced_block(init_environment):
    """
    Submits a proof with a replaced block
    """

    interface = make_interface(backend)

    res = validate_interlink(interface, replaced_blocks_proof)
    assert res["result"] == False
