"""
run with
$ python consistency.py
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler


def deploy(
    contract_path="./consistency.sol",
    backend="ganache",
    constructor_arguments=[],
):
    """
    Deploys a contract with a name and returns the interface
    """

    interface = contract_interface.ContractInterface(
        contract_path,
        backend=backend,
        constructor_arguments=constructor_arguments,
    )
    return interface


def finalize(interface):
    """
    Finalized an interface
    """

    interface.end()


def print_debug_events(contract, receipt):
    """
    Prints 'debug' events
    """

    try:
        debug_events = contract.events.debug().processReceipt(receipt)
    except Exception:
        debug_events = {}
    if len(debug_events) > 0:
        for e in debug_events:
            log = dict(e)["args"]
            if isinstance(log["value"], bytes):
                value = log["value"].hex()
            else:
                value = log["value"]
            print(log["tag"], "\t", value)
    return debug_events


def call(interface, function_name, function_args=[]):
    """
    Runs the output of a function
    """

    contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    function = contract.get_function_by_name(function_name)(*function_args)
    res = function.call({"from": from_address})
    tx_hash = function.transact({"from": from_address})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.run_gas_profiler(profiler, tx_hash, function_name)
    print_debug_events(contract, receipt)
    return {"result": res, "gas": receipt["gasUsed"]}


def log2_ceiling(number):
    """
    Returns the ceiling[log2(number)] ie the number of binary digits
    """

    interface = deploy()
    result = call(interface, "log2Ceiling", function_args=[number])
    finalize(interface)
    return result


def closest_pow_of_2(number):
    """
    Returns n sos that number/2 < n < number
    """

    interface = deploy()
    result = call(interface, "closestPow2", function_args=[number])
    finalize(interface)
    return result


def merkle_tree_hash(data):
    """
    Returns the merkle roof of data
    """

    interface = deploy()
    result = call(interface, "merkleTreeHash", function_args=[data])
    finalize(interface)
    return result


def path(data, index):
    """
    Returns the merkle proof for index in data
    """

    interface = deploy()
    result = call(interface, "path", function_args=[data, index])
    finalize(interface)
    return result


def create_siblings(n, m):
    """
    Creates a bool siblings array to facilitate merkle proof validation
    """

    interface = deploy()
    result = call(interface, "createSiblings", function_args=[n, m])
    finalize(interface)
    return result


def root_from_path(index, path, siblings):
    """
    Returns the root as calculated following path
    """

    interface = deploy()
    result = call(
        interface,
        "rootFromPath",
        function_args=[int(index).to_bytes(32, "big"), path, siblings],
    )
    finalize(interface)
    return result


def subArray(data, start, end):
    """
    Returns data[start:end]
    """

    interface = deploy()
    result = call(
        interface, "subArrayBytes32", function_args=[data, start, end]
    )
    return result


def cons_proof_sub(data, m):
    """
    Returns the consistency proof for range m of data
    Note this returns the proof reversed and possibly with void records
    """

    interface = deploy()
    result = call(interface, "consProofSub", function_args=[data, m])

    proof = result["result"]
    rev_proof = []
    for p in proof[::-1]:
        if p == int(0).to_bytes(32, "big"):
            continue
        rev_proof.append(p)

    return {"result": rev_proof, "gas": result["gas"]}


def root_0_from_const_proof(proof, n0, n1):
    """
    Returns the root hash of the merkle tree as constructed from proof from a
    range of n0 out of n1 nodes
    """

    interface = deploy()
    result = call(
        interface, "root0FromConsProof", function_args=[proof, n0, n1]
    )
    return result


def root_1_from_const_proof(proof, n0, n1):
    """
    Returns the root hash of the merkle tree as constructed from proof from a
    range of n1 nodes
    """

    interface = deploy()
    result = call(
        interface, "root1FromConsProof", function_args=[proof, n0, n1]
    )
    return result
