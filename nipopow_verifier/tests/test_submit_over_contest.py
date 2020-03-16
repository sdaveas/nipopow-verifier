"""
run with
$ pytest -v -s test_submit_over_contest.py
"""

import sys

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

from contract_api import (
    make_interface,
    submit_event_proof,
    submit_contesting_proof,
    submit_contesting_proof_new,
    finalize_event,
    event_exists,
)
from config import genesis

import pytest

backend = "ganache"


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global big_proof
    global small_proof

    backend = "ganache"
    big_proof = Proof()
    small_proof = Proof()

    proof_tool = ProofTool("../data/proofs/")

    mainblocks = 100
    fork_index = 50
    forkblocks = 30
    # create pkl files for big and small proof
    (big_proof_name, small_proof_name) = proof_tool.create_mainproof_and_forkproof(
        mainblocks, fork_index, forkblocks
    )

    big_proof.set(proof_tool.fetch_proof(big_proof_name), big_proof_name)
    small_proof.set(proof_tool.fetch_proof(small_proof_name), small_proof_name)


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


def test_submit_contest():
    interface = make_interface(backend)

    pt = ProofTool("../data/proofs/")
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof("../data/proofs/proof_200.pkl"))
    contest_proof.set(pt.fetch_proof("../data/proofs/proof_200-100+50.pkl"))

    lca = 55
    block_of_interest_index = 0
    block_of_interest = submit_proof.headers[block_of_interest_index]

    res = submit_event_proof(
        interface,
        submit_proof,
        block_of_interest_index,
        profile=True
    )

    assert res["result"] == True
    res = submit_contesting_proof_new(
        interface,
        submit_proof,
        lca,
        contest_proof,
        block_of_interest_index,
        profile=True,
    )
    # assert res['result'] == False


def test_common_block(init_environment):
    """
    Block of interest contained in both chains
    ---x0---+-------->  Ca
            |
            +--->       Cb
    """

    block_of_interest = big_proof.headers[-1]

    # First Ca, then Cb
    interface = make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest, profile=True)
    assert res["result"] == True, "submit big proof should be True"
    res = submit_contesting_proof(
        interface, small_proof, block_of_interest, profile=True
    )
    assert res["result"] == False, "contest small proof should be False"

    ## First Cb, then Ca
    interface = make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest, profile=True)
    assert res["result"] == True, "submit small proof should be True"
    res = submit_contesting_proof(interface, big_proof, block_of_interest, profile=True)
    assert res["result"] == False, "contest big proof should be False"


def test_block_in_big_chain(init_environment):
    """
    Block of interest contained only in Ca
    --------+---x1--->  Ca
            |
            +--->       Cb
    """

    block_of_interest = big_proof.headers[0]

    # First Ca, then Cb
    interface = make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res["result"] == True, "submit big proof should be True"
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert res["result"] == False, "contest small proof should be False"

    # First Cb, then Ca
    interface = make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res["result"] == False, "submit small proof should be True"
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res["result"] == False, "contest big proof should be True"


def test_block_in_small_chain(init_environment):
    """
    Block of interest contained only in Cb
    --------+---------->  Ca
            |
            +--x2-->      Cb
    """

    block_of_interest = small_proof.headers[0]

    # First Ca, then Cb
    interface = make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res["result"] == False, "submit big proof should be False"
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert res["result"] == False, "submit small proof should be False"

    # First Cb, then Ca
    interface = make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res["result"] == True, "submit small proof should be True"
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res["result"] == True, "contest big proof should be True"


def test_submit_proof_twice(init_environment):
    """
    Test double submission
    """

    block_of_interest = big_proof.headers[0]
    interface = make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res["result"] == True, "submit proof should be True"
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res["result"] == False, "submit same proof again should be False"


def test_event_exists(init_environment):

    k = 6
    block_of_interest = big_proof.headers[-1]
    interface = make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res["result"] == True, "submit small proof should be True"
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res["result"] == False, "contest big proof should be False"
    res = event_exists(interface, block_of_interest)
    assert res == False, "event should exist yet"
    # Spare k rounds. Then the finalize even should be accepted
    for i in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res == True, "event should now exist"


# TODO: see why this fails with k = 1
def test_event_not_exist(init_environment):
    k = 6
    interface = make_interface(backend)
    block_of_interest = small_proof.headers[0]
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res["result"] == True, "submit small proof should be True"
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res["result"] == True, "submit big proof should be True"
    # Spare k rounds. Then the finalize even should be accepted
    for i in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res == False, "event should still not exist"


def test_submit_after_finalize(init_environment):
    k = 6
    interface = make_interface(backend)
    block_of_interest = small_proof.headers[0]
    res = submit_event_proof(interface, small_proof, block_of_interest)
    # Spare k rounds. Then the finalize even should be accepted
    for _ in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res == True, "event should exist"
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert (
        res["result"] == False
    ), "stronger proof should not be accepted because the time expired"
