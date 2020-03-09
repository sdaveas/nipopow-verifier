"""
run with
$ pytest -v -s test_security_params.py
"""

import sys
sys.path.append('../tools/interface/')
import contract_interface
sys.path.append('../tools/proof/')
from proof import Proof
from create_proof import ProofTool

from contract_api import make_interface, submit_event_proof, submit_contesting_proof
from config import errors, genesis

import pytest

@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global pt
    global backend
    backend = 'ganache'
    pt = ProofTool('../data/proofs/')

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    """
    This runs after every test
    """

    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_smaller_m(init_environment):
    """
    Submit a proof with mu=1
    """

    proof = Proof()
    proof.set(pt.fetch_proof('../data/proofs/proof_100_m1_k15.pkl'))

    block_of_interest = proof.headers[0]
    interface=make_interface(backend)

    with pytest.raises(Exception) as ex:
        submit_event_proof(interface, proof, block_of_interest)

def test_smaller_k(init_environment):
    """
    Submit a proof with k=1
    """

    proof = Proof()
    proof.set(pt.fetch_proof('../data/proofs/proof_100_m15_k1.pkl'))

    block_of_interest = proof.headers[0]
    interface=make_interface(backend)

    with pytest.raises(Exception) as ex:
        submit_event_proof(interface, proof, block_of_interest)
