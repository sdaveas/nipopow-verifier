#########################
# run with
# $ pytest -v -s test_security_params.py
#########################

import sys
sys.path.append('../lib/')
import contract_interface
from proof import Proof
from create_proof import fetch_proof
from edit_chain import *

import pytest
import web3
import errors

def submit_event_proof(interface, proof, block_of_interest):

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.submit_event_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest,
                                            ).estimateGas()

    res = my_contract.functions.submit_event_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest
                                            ).call({'from' : from_address,
                                                    'value': collateral})

    tx_hash = my_contract.functions.submit_event_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest
                                            ).transact({'from' : from_address,
                                                        'value': collateral})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)


    return {'result': res}

def submit_cont_proof(interface, proof, block_of_interest):

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.submit_contesting_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest,
                                            ).estimateGas()

    res = my_contract.functions.submit_contesting_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest
                                            ).call({'from' : from_address})

    tx_hash = my_contract.functions.submit_contesting_proof(
                                            proof.headers,
                                            proof.siblings,
                                            block_of_interest
                                            ).transact({'from' : from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    return {'result': res}

def make_interface(backend):
    return contract_interface.ContractInterface("../../contractNipopow.sol", backend=backend)

@pytest.fixture
def init_environment():

    global backend
    backend = 'ganache'

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_smaller_m(init_environment):

    proof = Proof()
    _proof = fetch_proof('../../proofs/proof_100_m1_k16.pkl')
    proof.set(_proof)

    block_of_interest = proof.headers[0]
    interface=make_interface(backend)

    with pytest.raises(Exception) as e:
        res = submit_event_proof(interface, proof, block_of_interest)

def test_smaller_k(init_environment):

    proof = Proof()
    _proof = fetch_proof('../../proofs/proof_100_m16_k1.pkl')
    proof.set(_proof)

    block_of_interest = proof.headers[0]
    interface=make_interface(backend)

    with pytest.raises(Exception) as e:
        res = submit_event_proof(interface, proof, block_of_interest)
