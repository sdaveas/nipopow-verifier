#########################
# run with
# $ pytest -v -s test_interlink.py
#########################

import sys
sys.path.append('../lib/')
import contract_interface
from proof import Proof
from create_proof import get_proof, import_proof
from edit_chain import *
import web3

import pytest
import errors

def submit_event_proof(interface, proof, block_of_interest):

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    collateral = pow(10, 17)

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
    return contract_interface.ContractInterface("../contractNipopow.sol", backend=backend)

@pytest.fixture
def init_environment():

    global backend
    global proof
    global changed_interlink_proof
    global missing_blocks_proof
    global replaced_blocks_proof
    backend = 'ganache'
    proof = Proof()
    changed_interlink_proof = Proof()
    missing_blocks_proof = Proof()
    replaced_blocks_proof = Proof()

    blocks=10
    original_proof = get_proof(blocks)
    proof.set(original_proof)

    _changed_interlink_proof = change_interlink_hash(original_proof, -1)
    changed_interlink_proof.set(_changed_interlink_proof)

    _missing_blocks_proof = original_proof.copy()
    _missing_blocks_proof = skip_blocks(_missing_blocks_proof, -3)
    missing_blocks_proof.set(_missing_blocks_proof)

    _replaced_blocks_proof = import_proof('../proofs/removed_block_proof.pkl')
    replaced_blocks_proof.set(_replaced_blocks_proof)

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_revert_on_submit(init_environment):

    block_of_interest = proof.headers[-1]
    interface=make_interface(backend)

    transaction_failed = False
    try:
        res = submit_event_proof(interface, changed_interlink_proof, block_of_interest)
    except web3.exceptions.BadFunctionCallOutput:
        transaction_failed = True
    finally:
        assert transaction_failed == True

def test_revert_on_contest(init_environment):

    block_of_interest = proof.headers[-1]
    interface=make_interface(backend)

    res = submit_event_proof(interface, proof, block_of_interest)
    assert res['result'] == True

    transaction_failed = False
    try:
        res = submit_cont_proof(interface, changed_interlink_proof, block_of_interest)
    except ValueError:
        transaction_failed = True
    finally:
        assert transaction_failed == True

def test_revert_on_missing_blocks_submit(init_environment):

    block_of_interest = proof.headers[-3]
    interface=make_interface(backend)

    transaction_failed = False
    try:
        res = submit_event_proof(interface, missing_blocks_proof, block_of_interest)
    except web3.exceptions.BadFunctionCallOutput:
        transaction_failed = True
    finally:
        assert transaction_failed == True


def test_revert_on_missing_blocks_contest(init_environment):

    block_of_interest = proof.headers[-3]
    interface=make_interface(backend)

    res = submit_event_proof(interface, proof, block_of_interest)

    transaction_failed = False
    try:
        res = submit_cont_proof(interface, missing_blocks_proof, block_of_interest)
        assert res == True
    except Exception as e:
        print(e)
        transaction_failed = True
    finally:
        assert transaction_failed == True

def test_replaced_block(init_environment):

    block_of_interest = proof.headers[0]
    interface = make_interface(backend)

    print(replaced_blocks_proof.proof[52][0][:32].hex())

    with pytest.raises(Exception) as e:
        res = submit_event_proof(interface, replaced_blocks_proof, block_of_interest)

    assert errors.extract_message_from_error(e) == errors.errors['merkle']
