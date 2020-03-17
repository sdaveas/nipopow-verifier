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
from config import errors, extract_message_from_error, genesis

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


def test_boi_in_large():
    """
    Block of interest contained in both chains
    --------+---x---->  Ca
            |
            +--->       Cb
    """
    block_of_interest_index = 0
    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )

    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca,
            contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["low score"]


def test_boi_in_small():
    """
    Block of interest contained in both chains
    --------+--x-->  Ca
            |
            +-------->  Cb
    """

    block_of_interest_index = 0
    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 100, 200
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
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
    assert res["result"] == True


def test_boi_in_common_submit_small():
    """
    Block of interest contained in both chains
    ----x---+---->  Ca
            |
            +------->  Cb
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 100, 200
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca,
            contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_boi_in_common_submit_big():
    """
    Block of interest contained in both chains
    ----x---+------->  Ca
            |
            +---->  Cb
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca,
            contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_boi_out_of_index():
    """
    Block of interest contained in both chains
    ---------------->  Ca    x
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = submit_proof.size

    with pytest.raises(Exception) as ex:
        res = submit_event_proof(
            interface, submit_proof, block_of_interest_index, profile=True
        )
    assert extract_message_from_error(ex) == errors["boi not exist"]


def test_boi_out_of_index_contest():
    """
    Block of interest is in submit but not in contest proof
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca,
            contest_proof,
            submit_proof.size,  # This is out of range
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi not exist"]


def test_same_proofs():
    """
    Submit proof is the same as contest proof
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca,
            submit_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_wrong_lca():
    """
    Contest proof lies about lca
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = 0

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            lca - 1,  # this is wrong
            contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["wrong lca"]


def test_proof_exists():
    """
    Contest proof lies about lca
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    submit_proof_name, contest_proof_name, lca = pt.create_proof_and_forkproof(
        1000, 200, 100
    )
    submit_proof = Proof()
    contest_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))
    contest_proof.set(pt.fetch_proof(contest_proof_name))

    block_of_interest_index = 0

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_event_proof(
            interface, submit_proof, block_of_interest_index, profile=True
        )
    assert extract_message_from_error(ex) == errors["period expired"]
