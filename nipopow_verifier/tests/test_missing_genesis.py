"""
run with
$ pytest -v -s test_genesis.py
"""

import sys
sys.path.append('../tools/interface/')
import contract_interface
sys.path.append('../tools/proof/')
from proof import Proof
from create_proof import ProofTool
from edit_chain import remove_genesis

from contract_api import make_interface, submit_event_proof, submit_contesting_proof
from config import errors, extract_message_from_error, genesis

import pytest

@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global proof
    global headless_proof
    backend = 'ganache'
    proof = Proof()
    headless_proof = Proof()

    original_proof = ProofTool('../data/proofs/').fetch_proof(100)
    proof.set(original_proof)

    _headless_proof = original_proof.copy()
    remove_genesis(_headless_proof)
    headless_proof.set(_headless_proof)

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    """
    This runs after each test
    """
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_missing_genesis_submit(init_environment):
    """
    Calls the submit_event_proof of the contracts with a proof without genesis
    """

    block_of_interest = proof.headers[-1]
    interface = make_interface(backend)

    with pytest.raises(Exception) as e:
        submit_event_proof(interface, headless_proof, block_of_interest)
    assert extract_message_from_error(e) == errors['genesis']

def test_genesis_block_contest(init_environment):
    """
    Calls the submit_event_proof of the contracts with a correct proof
    and contest_event_proof with a proof without genesis
    """

    block_of_interest = proof.headers[-2]
    interface=make_interface(backend)

    res = submit_event_proof(interface, proof, block_of_interest)
    assert res['result'] == True
    with pytest.raises(Exception) as ex:
        submit_contesting_proof(interface, headless_proof, block_of_interest)
    assert extract_message_from_error(ex) == errors['genesis']
