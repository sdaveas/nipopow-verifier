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
submit_proof = Proof()
small_contest_proof = Proof()
large_contest_proof = Proof()
small_lca = None
large_lca = None


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global submit_proof
    global small_contest_proof
    global small_lca
    global large_contest_proof
    global large_lca

    backend = "ganache"

    pt = ProofTool("../data/proofs/")
    (
        submit_proof_name,
        small_contest_proof_name,
        small_lca,
        small_header,
        small_header_map,
        small_interlink_map,
    ) = pt.create_proof_and_forkproof(1000, 200, 100)
    (
        submit_proof_name,
        large_contest_proof_name,
        large_lca,
        large_header,
        large_header_map,
        large_interlink_map,
    ) = pt.create_proof_and_forkproof(1000, 100, 200)

    submit_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))

    small_contest_proof = Proof()
    small_contest_proof.set(
        pt.fetch_proof(small_contest_proof_name),
        header=small_header,
        header_map=small_header_map,
        interlink_map=small_interlink_map,
    )

    large_contest_proof = Proof()
    large_contest_proof.set(
        pt.fetch_proof(large_contest_proof_name),
        header=large_header,
        header_map=large_header_map,
        interlink_map=large_interlink_map,
    )


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


def test_boi_in_large(init_environment):
    """
    Block of interest contained in both chains
    --------+---x---->  Ca
            |
            +--->       Cb
    """
    block_of_interest_index = 0
    interface = make_interface(backend)

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )

    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            small_lca,
            small_contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["low score"]


def test_boi_in_small(init_environment):
    """
    Block of interest contained in both chains
    --------+--x-->  Ca
            |
            +-------->  Cb
    """

    block_of_interest_index = 0
    interface = make_interface(backend)

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )

    assert res["result"] == True

    return

    res = submit_contesting_proof_new(
        interface,
        submit_proof,
        large_lca,
        large_contest_proof,
        block_of_interest_index,
        profile=True,
    )
    assert res["result"] == True


def test_boi_in_common_submit_small(init_environment):
    """
    Block of interest contained in both chains
    ----x---+---->  Ca
            |
            +------->  Cb
    """

    pt = ProofTool("../data/proofs/")
    interface = make_interface(backend)

    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            large_lca,
            large_contest_proof,
            block_of_interest_index,
            profile=True,
        )
    print(ex)
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_boi_in_common_submit_big(init_environment):
    """
    Block of interest contained in both chains
    ----x---+------->  Ca
            |
            +---->  Cb
    """

    interface = make_interface(backend)
    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            small_lca,
            small_contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_boi_out_of_index(init_environment):
    """
    Block of interest contained in both chains
    ---------------->  Ca    x
    """

    interface = make_interface(backend)
    block_of_interest_index = submit_proof.size

    with pytest.raises(Exception) as ex:
        res = submit_event_proof(
            interface, submit_proof, block_of_interest_index, profile=True
        )
    assert extract_message_from_error(ex) == errors["boi not exist"]


def test_boi_out_of_index_contest(init_environment):
    """
    Block of interest is in submit but not in contest proof
    """

    interface = make_interface(backend)
    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            large_lca,
            large_contest_proof,
            submit_proof.size,  # This is out of range
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi not exist"]


def test_same_proofs(init_environment):
    """
    Submit proof is the same as contest proof
    """

    interface = make_interface(backend)
    block_of_interest_index = submit_proof.size - 1

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            0,
            submit_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["boi in sub-chain"]


def test_wrong_lca(init_environment):
    """
    Contest proof lies about lca
    """

    interface = make_interface(backend)
    block_of_interest_index = 0

    res = submit_event_proof(
        interface, submit_proof, block_of_interest_index, profile=True
    )
    assert res["result"] == True

    with pytest.raises(Exception) as ex:
        res = submit_contesting_proof_new(
            interface,
            submit_proof,
            large_lca - 1,  # this is wrong
            large_contest_proof,
            block_of_interest_index,
            profile=True,
        )
    assert extract_message_from_error(ex) == errors["wrong lca"]


def test_proof_exists(init_environment):
    """
    Contest proof exists
    """

    interface = make_interface(backend)

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
