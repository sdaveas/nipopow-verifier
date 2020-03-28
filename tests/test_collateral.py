"""
run with
$ pytest -v -s test_collateral.py
"""

import sys
import pytest

sys.path.append("../tools/interface/")
import contract_interface

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

from contract_api import (
    make_interface,
    submit_event_proof,
    submit_contesting_proof,
    finalize_event,
)

from config import errors, extract_message_from_error


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global proof
    backend = "ganache"

    blocks = 10

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
    interface = make_interface(backend)
    interface.end()


def test_sufficient_collateral(init_environment):
    """
    Test contract call with sufficient collateral
    """

    interface = make_interface(backend)

    # Collateral defined in contract:
    # uint constant z = 100000000000000000; // 0.1 eth, 10^17

    res = submit_event_proof(interface, proof, proof.size - 1, collateral=pow(10, 17))
    assert res["result"] == True


def test_insufficient_collateral(init_environment):
    """
    Test contract call with insufficient collateral
    """

    interface = make_interface(backend)

    # Collateral defined in contract:
    # uint constant z = 100000000000000000; // 0.1 eth, 10^17

    collateral = pow(10, 17) - 1

    with pytest.raises(Exception) as ex:
        submit_event_proof(interface, proof, proof.size - 1, collateral=collateral)
    print(ex)
    assert extract_message_from_error(ex) == errors["ante up"]


def test_receive_collateral(init_environment):

    interface = make_interface(backend)

    from_address = interface.w3.eth.accounts[0]
    initial_balance = interface.w3.eth.getBalance(from_address)

    # Collateral defined in contract:
    # uint constant z = 100000000000000000; // 0.1 eth, 10^17

    block_of_interest_index = proof.size - 1
    collateral = pow(10, 17)
    res = submit_event_proof(
        interface, proof, block_of_interest_index, collateral, from_address
    )
    assert res["result"] == True

    after_submit = interface.w3.eth.getBalance(from_address)
    assert initial_balance - after_submit > collateral

    k = 6
    for _ in range(k):
        finalize_event(interface, proof.headers[block_of_interest_index])

    after_finalize = interface.w3.eth.getBalance(from_address)

    assert after_finalize > after_submit
