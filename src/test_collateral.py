#########################
# run with
# $ pytest -v -s test_collateral.py
#########################

import sys
sys.path.append('../lib/')
import contract_interface
from proof import Proof
from create_proof import get_proof

import pytest

def submit_event_proof(interface, proof, block_of_interest, collateral, from_address):

    my_contract = interface.get_contract()
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

def submit_cont_proof(interface, proof, block_of_interest, from_address):

    my_contract = interface.get_contract()
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

def finalize_event(interface, block_of_interest):
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)
    estimated_gas = my_contract.functions.finalize_event(
                                            block_of_interest,
                                            ).estimateGas()

    res = my_contract.functions.finalize_event(
                                            block_of_interest
                                            ).call({'from' : from_address})

    tx_hash = my_contract.functions.finalize_event(
                                            block_of_interest
                                            ).transact({'from' : from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    events = None

    return {'result': res}

def make_interface(backend):
    return contract_interface.ContractInterface("../contractNipopow.sol", backend=backend)

@pytest.fixture
def init_environment():

    global backend
    global proof
    backend = 'ganache'
    proof = Proof()

    blocks=10
    _proof = get_proof(blocks)
    proof.set(_proof)

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_insufficient_collateral(init_environment):

    interface=make_interface(backend)
    from_address = interface.w3.eth.accounts[0]

    # Collateral defined in contract:
    # uint constant z = 100000000000000000; // 0.1 eth, 10^17

    block_of_interest = proof.headers[-1]
    collateral = pow(10, 17)
    res = submit_event_proof(interface, proof, block_of_interest, collateral, from_address)
    assert res['result']==True

    block_of_interest = proof.headers[-2]
    collateral = pow(10, 17) - 1
    res = submit_event_proof(interface, proof, block_of_interest, collateral, from_address)
    assert res['result']==False


def test_receive_collateral(init_environment):

    interface=make_interface(backend)
    from_address = interface.w3.eth.accounts[0]
    initial_balance = interface.w3.eth.getBalance(from_address)

    # Collateral defined in contract:
    # uint constant z = 100000000000000000; // 0.1 eth, 10^17

    block_of_interest = proof.headers[-1]
    collateral = pow(10, 17)
    res = submit_event_proof(interface, proof, block_of_interest, collateral, from_address)
    assert res['result']==True

    after_submit = interface.w3.eth.getBalance(from_address)
    assert initial_balance - after_submit > collateral

    k = 6
    for i in range(k):
        finalize_event(interface, block_of_interest)

    after_finalize = interface.w3.eth.getBalance(from_address)

    #print(collateral - (after_finalize - after_submit))
    assert after_finalize > after_submit
