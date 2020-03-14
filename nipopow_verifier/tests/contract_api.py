"""
API for NiPoPoW verifier smart contract
"""

import sys
from time import time

from config import profiler, genesis

sys.path.append("../tools/interface/")
import contract_interface


def make_interface(backend):
    """
    Creates a contract interface
    """
    return contract_interface.ContractInterface(
        "../../contractNipopow.sol",
        backend=backend,
        genesis_overrides={"gas_limit": 67219750},
        constructor_arguments=[genesis],
    )


# TODO: This is sode duplidation with the below function
def submit_event_proof(
    interface,
    proof,
    block_of_interest,
    collateral=pow(10, 17),
    from_address=None,
    profile=False,
):
    """
    Call submit_event_proof of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.submitEventProof(
        proof.headers, proof.siblings, block_of_interest
    ).call({"from": from_address, "value": collateral})

    tx_hash = my_contract.functions.submitEventProof(
        proof.headers, proof.siblings, block_of_interest
    ).transact({"from": from_address, "value": collateral})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)['args']
            print(log['tag'],"\t", log['value'])

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt['gasUsed'])

    return {"result": res, 'gas_used': receipt['gasUsed'], 'debug': debug_events}


# TODO: This is sode duplidation with the above function
def submit_contesting_proof(
    interface, proof, block_of_interest, from_address=None, profile=False
):
    """
    Calls contest_event_proof of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.submitContestingProof(
        proof.headers, proof.siblings, block_of_interest
    ).call({"from": from_address})

    tx_hash = my_contract.functions.submitContestingProof(
        proof.headers, proof.siblings, block_of_interest
    ).transact({"from": from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        print("Contest::")
        for e in debug_events:
            log = dict(e)['args']
            print(log['tag'],"\t", log['value'])

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt['gasUsed'])

    return {"result": res, 'gas_used': receipt['gasUsed'], 'debug': debug_events}


def finalize_event(interface, block_of_interest, from_address=None):
    """
    Calls finalize_event of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.finalizeEvent(block_of_interest).call(
        {"from": from_address}
    )

    tx_hash = my_contract.functions.finalizeEvent(block_of_interest).transact(
        {"from": from_address}
    )

    interface.w3.eth.waitForTransactionReceipt(tx_hash)

    return {"result": res}


def event_exists(interface, block_of_interest):
    """
    Calls event_exists of the contract
    """

    contract = interface.get_contract()
    res = contract.functions.eventExists(block_of_interest).call()
    return res
