#########################
# run with
# $ pytest -v -s test_genesis.py
#########################

import sys
sys.path.append('../src/interface/')
import contract_interface
sys.path.append('../src/proof/')
from proof import Proof
from create_proof import ProofTool
from edit_chain import remove_genesis

import pytest

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
    global proof
    global headless_proof
    backend = 'geth'
    proof = Proof()
    headless_proof = Proof()

    pt = ProofTool('../data/proofs/')

    blocks=10
    original_proof = pt.fetch_proof(blocks)
    proof.set(original_proof)

    _headless_proof = original_proof.copy()
    remove_genesis(_headless_proof)
    headless_proof.set(_headless_proof)

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_missing_genesis_submit(init_environment):

    block_of_interest = proof.headers[-1]
    interface=make_interface(backend)

    res = submit_event_proof(interface, headless_proof, block_of_interest)
    assert res['result']==False

def test_genesis_block_contest(init_environment):

    block_of_interest = proof.headers[-2]
    interface=make_interface(backend)

    res = submit_event_proof(interface, headless_proof, block_of_interest)
    # This fails
    assert res['result']==False
    res =  submit_cont_proof(interface, proof, block_of_interest)
    assert res['result']==True
