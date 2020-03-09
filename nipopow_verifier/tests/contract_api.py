"""
API for NiPoPoW verifier smart contract
"""

import sys

from config import genesis

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


def submit_event_proof(
    interface, proof, block_of_interest, collateral=pow(10, 17), from_address=None
):
    """
    Call submit_event_proof of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.submit_event_proof(
        proof.headers, proof.siblings, block_of_interest
    ).call({"from": from_address, "value": collateral})

    tx_hash = my_contract.functions.submit_event_proof(
        proof.headers, proof.siblings, block_of_interest
    ).transact({"from": from_address, "value": collateral})

    interface.w3.eth.waitForTransactionReceipt(tx_hash)

    # interface.run_gas_profiler(profiler, tx_hash)

    return {"result": res}


def submit_contesting_proof(interface, proof, block_of_interest, from_address=None):
    """
    Calls contest_event_proof of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.submit_contesting_proof(
        proof.headers, proof.siblings, block_of_interest
    ).call({"from": from_address})

    tx_hash = my_contract.functions.submit_contesting_proof(
        proof.headers, proof.siblings, block_of_interest
    ).transact({"from": from_address})

    interface.w3.eth.waitForTransactionReceipt(tx_hash)

    # interface.run_gas_profiler(profiler, tx_hash)

    return {"result": res}


def finalize_event(interface, block_of_interest, from_address=None):
    """
    Calls finalize_event of the verifier
    """

    my_contract = interface.get_contract()
    if from_address is None:
        from_address = interface.w3.eth.accounts[0]

    res = my_contract.functions.finalize_event(block_of_interest).call(
        {"from": from_address}
    )

    tx_hash = my_contract.functions.finalize_event(block_of_interest).transact(
        {"from": from_address}
    )

    interface.w3.eth.waitForTransactionReceipt(tx_hash)

    return {"result": res}


def event_exists(interface, block_of_interest):
    """
    Calls event_exists of the contract
    """

    contract = interface.get_contract()
    res = contract.functions.event_exists(block_of_interest).call()
    return res
