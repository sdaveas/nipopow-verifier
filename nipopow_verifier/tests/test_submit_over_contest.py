#########################
# run with
# $ pytest -v -s test_submit_over_contest.py
#########################

import sys
sys.path.append('../src/interface/')
import contract_interface
sys.path.append('../src/proof/')
from proof import Proof
from create_proof import ProofTool
import pytest


profiler = '/home/stelios/Projects/solidity-gas-profiler/profile.js'

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


    return {'result'        : res,
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend}

def submit_contesting_proof(interface, proof, block_of_interest):

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

    # interface.run_gas_profiler(profiler, tx_hash)

    return {'result'        : res,
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend}

def make_interface(backend):
    return contract_interface.ContractInterface("../../contractNipopow.sol",
                                                backend=backend,
                                                genesis_overrides={
                                                                    'gas_limit': 67219750
                                                                    },
                                                )


@pytest.fixture
def init_environment():

    global backend
    global big_proof
    global small_proof

    backend = 'geth'
    big_proof = Proof()
    small_proof = Proof()

    pt = ProofTool('../data/proofs/')

    mainblocks=100
    fork_index= 50
    forkblocks= 30
    # create pkl files for big and small proof
    (big_proof_name, small_proof_name) = pt.create_mainproof_and_forkproof(mainblocks, fork_index, forkblocks)

    big_proof.set(pt.fetch_proof(big_proof_name), big_proof_name)
    small_proof.set(pt.fetch_proof(small_proof_name), small_proof_name)

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session
    interface = make_interface(backend)
    interface.end()

def test_common_block(init_environment):

    block_of_interest = big_proof.headers[-1]
    interface=make_interface(backend)

    #   Block of interest contained in both chains
    #   ---x0---+-------->  Ca
    #           |
    #           +--->       Cb

    # First Ca, then Cb
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==True, 'submit big proof should be True'
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert res['result']==False, 'contest small proof should be False'

    ## First Cb, then Ca
    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res['result']==True, 'submit small proof should be True'
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'contest big proof should be False'

def test_block_in_big_chain(init_environment):

    block_of_interest = big_proof.headers[0]
    interface=make_interface(backend)

    #   Block of interest contained only in Ca
    #   --------+---x1--->  Ca
    #           |
    #           +--->       Cb

    # First Ca, then Cb
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==True, 'submit big proof should be True'
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert res['result']==False, 'contest small proof should be False'

    # First Cb, then Ca
    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res['result']==False, 'submit small proof should be True'
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'contest big proof should be True'

def test_block_in_small_chain(init_environment):

    block_of_interest = small_proof.headers[0]
    interface=make_interface(backend)

    #   Block of interest contained only in Cb
    #   --------+---------->  Ca
    #           |
    #           +--x2-->      Cb

    # First Ca, then Cb
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'submit big proof should be False'
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert res['result']==False, 'submit small proof should be False'

    # First Cb, then Ca
    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res['result']==True, 'submit small proof should be True'
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res['result']==True, 'contest big proof should be True'

def test_submit_proof_twice(init_environment):
    block_of_interest = big_proof.headers[0]
    interface=make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==True, 'submit proof should be True'
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'submit same proof again should be False'

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

    return {'result'        : res,
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend}

def event_exists(interface, block_of_interest):
    contract = interface.get_contract()
    res = contract.functions.event_exists(block_of_interest).call()
    return res

def test_event_exists(init_environment):

    k = 6
    block_of_interest = big_proof.headers[-1]
    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res['result']==True, 'submit small proof should be True'
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'contest big proof should be False'
    res = event_exists(interface, block_of_interest)
    assert res==False, 'event should exist yet'
    # Spare k rounds. Then the finalize even should be accepted
    for i in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res==True, 'event should now exist'

# TODO: see why this fails with k = 1
def test_event_not_exist(init_environment):
    k = 6
    interface=make_interface(backend)
    block_of_interest = small_proof.headers[0]
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert res['result']==True, 'submit small proof should be True'
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert res['result']==True, 'submit big proof should be True'
    # Spare k rounds. Then the finalize even should be accepted
    for i in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res==False, 'event should still not exist'

def test_submit_after_finalize(init_environment):
    k = 6
    interface = make_interface(backend)
    block_of_interest = small_proof.headers[0]
    res = submit_event_proof(interface, small_proof, block_of_interest)
    # Spare k rounds. Then the finalize even should be accepted
    for i in range(k):
        finalize_event(interface, block_of_interest)
    res = event_exists(interface, block_of_interest)
    assert res==True, 'event should exist'
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert res['result']==False, 'stronger proof should not be accepted because the time expired'
