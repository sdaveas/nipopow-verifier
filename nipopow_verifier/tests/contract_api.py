"""
API for NiPoPoW verifier smart contract
"""

import sys
from time import time

from config import profiler, genesis, m, k

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
        constructor_arguments=[genesis, m, k],
    )


# TODO: This is code duplidation with the below function
def submit_event_proof(
    interface,
    proof,
    block_of_interest_index,
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

    my_function = my_contract.functions.submitEventProof(
        proof.headers, proof.siblings, block_of_interest_index
    )

    res = my_function.call({"from": from_address, "value": collateral})

    tx_hash = my_function.transact({"from": from_address, "value": collateral})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)["args"]
            if isinstance(log["value"], bytes):
                value = log["value"].hex()
            else:
                value = log["value"]
            print(log["tag"], "\t", value)

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt["gasUsed"])

    return {"result": res, "gas_used": receipt["gasUsed"], "debug": debug_events}


def dispute_existing_proof(
    interface, existing, block_of_interest_index, invalid_index, profile=True,
):
    """
    Calls disputeExistingProof(existingHeaders, existingHeadersHash, siblings)
    """

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    my_function = my_contract.functions.disputeExistingProof(
        existing.headers, existing.siblings, block_of_interest_index, invalid_index,
    )

    res = my_function.call({"from": from_address})

    tx_hash = my_function.transact({"from": from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)["args"]
            print(log["tag"], "\t", log["value"])

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt["gasUsed"])

    return {"result": res, "gas_used": receipt["gasUsed"], "debug": debug_events}


# bytes32[4][] memory existingHeaders,
# uint256 lca,
# bytes32[4][] memory contestingHeaders,
# bytes32[] memory contestingSiblings,
# bytes32[4] memory blockOfInterest,

# TODO: This is code duplidation with the above function
def submit_contesting_proof_new(
    interface,
    existing,
    lca,
    contesting,
    block_of_interest_index,
    from_address=None,
    profile=False,
):
    """
    Calls contest_event_proof of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    my_function = my_contract.functions.submitContestingProof(
        existing.hashed_headers,
        lca,
        contesting.best_level_subproof_headers,
        contesting.best_level_subproof_siblings,
        contesting.best_level,
        block_of_interest_index,
    )

    res = my_function.call({"from": from_address})

    tx_hash = my_function.transact({"from": from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        print("Contest::")
        for e in debug_events:
            log = dict(e)["args"]
            print(log["tag"], "\t", log["value"])

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt["gasUsed"])

    return {"result": res, "gas_used": receipt["gasUsed"], "debug": debug_events}


# TODO: This is code duplidation with the above function
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
            log = dict(e)["args"]
            print(log["tag"], "\t", log["value"])

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt["gasUsed"])

    return {"result": res, "gas_used": receipt["gasUsed"], "debug": debug_events}


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


def validate_interlink(interface, proof, profile=True):
    """
    Calls validateInterlink of contract
    """

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    my_function = my_contract.functions.validateInterlink(
        proof.headers, proof.hashed_headers, proof.siblings
    )

    res = my_function.call({"from": from_address})

    tx_hash = my_function.transact({"from": from_address})

    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)

    try:
        debug_events = my_contract.events.debug().processReceipt(receipt)
    except Exception as ex:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)["args"]
            if isinstance(log["value"], bytes):
                value = log["value"].hex()
            else:
                value = log["value"]
            print(log["tag"], "\t", value)

    if profile is True:
        filename = str(int(time())) + ".txt"
        interface.run_gas_profiler(profiler, tx_hash, filename)

    print(receipt["gasUsed"])

    return {"result": res, "gas_used": receipt["gasUsed"], "debug": debug_events}
