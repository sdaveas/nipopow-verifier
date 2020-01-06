#########################
# run with
# $ pytest -v -k block
#########################

import sys
sys.path.append('../lib/')
import contract_interface
from create_proof import import_proof, create_proof, make_proof_file_name, get_proof, create_mainproof_and_forkproof
import pytest

class Proof:
    def __init__(
            self,
            headers=None,
            siblings=None
            ):
        self.headers=headers
        self.siblings=siblings

# proof data manipulation
def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def extract_headers_siblings(proof):
    headers = []
    hashed_headers = []
    siblings = []
    # mp stands for merkle proof
    # hs stands for headers.
    for p in proof:
        hs = p[0]
        mp = p[1]
        # Copy the header to an array of 4 bytes32
        header = str_to_bytes32(hs)
        # Encode the Merkle bits (mu) in the largest byte
        # Encode the mp size in the next largest byte
        assert 0 <= len(mp) < 256
        mu = sum(bit << i for (i,(bit,_)) in enumerate(mp[::-1]))
        assert 0 <= mu < 256
        #header[3] = chr(len(mp)) + chr(mu) + header[3][2:]
        header[3] = header[3] + ('\x00'*14).encode() + bytes([len(mp)]) + bytes([mu])
        headers.append(header)

        for (_,sibling) in mp:
            siblings.append(sibling)

    return headers, siblings

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

    events = interface.get_contract().events.GasUsed().processReceipt(receipt)

    return {'result'        : res,
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend,
            'events'        : events}

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

    events = interface.get_contract().events.GasUsed().processReceipt(receipt)

    return {'result'        : res,
            'receipt'       : receipt,
            'estimated_gas' : estimated_gas,
            'from'          : from_address,
            'backend'       : interface.backend,
            'events'        : events}

def import_main_proof(big_proof_name='big_proof.pkl', proof_dir='../proofs/'):
    proof_big = import_proof(proof_dir+big_proof_name)
    print('Big proof has length', len(proof_big))
    headers_big, siblings_big = extract_headers_siblings(proof_big)

    return Proof(headers_big, siblings_big)

def import_fork_proof(small_proof_name='small_proof.pkl', proof_dir='../proofs/'):
    proof_small = import_proof(proof_dir+small_proof_name)
    print('Small proof has lenght', len(proof_small))
    headers_small, siblings_small = extract_headers_siblings(proof_small)

    return Proof(headers_small, siblings_small)

def make_interface(backend):
    return contract_interface.ContractInterface("../contractNipopow.sol",
                                                backend=backend,
                                                genesis_overrides={
                                                                    'gas_limit': 67219750
                                                                    },
                                                )

backend = 'ganache'
big_proof = Proof()
small_proof = Proof()
bigger_proof = Proof()

@pytest.fixture
def submit_over_contesting():
    mainblocks=100
    fork_index=50
    forkblocks=25
    create_mainproof_and_forkproof(mainblocks, fork_index, forkblocks)

    big_proof_name = 'proof_'+str(mainblocks)+'.pkl'
    small_proof_name = str(fork_index)+'_fork_of_proof_'+str(mainblocks)+'.pkl'
    b = get_proof(mainblocks+int(mainblocks/2))
    h, s = extract_headers_siblings(b)
    bigger_proof.headers = h
    bigger_proof.siblings = s

    b = Proof()
    b = import_main_proof(big_proof_name)
    big_proof.headers= b.headers
    big_proof.siblings= b.siblings
    s = Proof()
    s = import_fork_proof(small_proof_name)
    small_proof.headers = s.headers
    small_proof.siblings = s.siblings

def test_common_block(submit_over_contesting):
    #   Block of interest contained in both chains
    #   ---x0---+-------->  Ca
    #           |
    #           +--->       Cb

    block_of_interest = big_proof.headers[-1]
    interface=make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert(res['result']==False)

    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)

def test_block_in_big_chain(submit_over_contesting):
    #   Block of interest contained only in Ca
    #   --------+---x1--->  Ca
    #           |
    #           +--->       Cb

    block_of_interest = big_proof.headers[0]
    interface=make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert(res['result']==False)

    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert(res['result']==False)
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert(res['result']==False)

def test_block_in_small_chain(submit_over_contesting):
    #   Block of interest contained only in Cb
    #   --------+---------->  Ca
    #           |
    #           +--x2-->      Cb

    block_of_interest = small_proof.headers[0]
    interface=make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert(res['result']==False)
    res = submit_contesting_proof(interface, small_proof, block_of_interest)
    assert(res['result']==False)

    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)

def test_submit_proof_twice(submit_over_contesting):
    block_of_interest = big_proof.headers[0]
    interface=make_interface(backend)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_event_proof(interface, big_proof, block_of_interest)
    assert(res['result']==False)

def test_contest_proof_twice(submit_over_contesting):
    block_of_interest = bigger_proof.headers[-1]
    interface=make_interface(backend)
    res = submit_event_proof(interface, small_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, big_proof, block_of_interest)
    assert(res['result']==True)
    res = submit_contesting_proof(interface, bigger_proof, block_of_interest)
    assert(res['result']==True)
