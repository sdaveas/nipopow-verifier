"""
run with
$ python mmr.py

if everything works OK, root of
10  should be ee943d2cc1a3b3728349c86d6a65a80bd4011f6e58c9c49772b9533ee2d6506d
100 should be 37ff9d8ccc1acb194f8a56b06592bca6381260d6c44abe018795751bea43eddf
"""

import sys

sys.path.append("../../tools/interface/")
import contract_interface

sys.path.append("..")
from config import profiler

import pickle


def export_pkl(data, filename):
    with open(filename, "wb") as f:
        pickle.dump(data, f)


def import_pkl(filename):
    with open(filename, "rb") as f:
        return pickle.load(f)


def int_to_bytes(integer, bytessize=32, endian="big"):
    return int(integer).to_bytes(bytessize, endian)


def zero_bytes(bytessize=32):
    return b"\x00" * bytessize


def deploy(constructor_arguments=[]):
    contract_path = "./MMR.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="geth", constructor_arguments=constructor_arguments
    )
    return interface


def finalize(interface):
    interface.end()


def print_debug_events(contract, receipt):
    try:
        debug_events = contract.events.debug().processReceipt(receipt)
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
    return debug_events


def call(interface, function_name, function_args=[]):
    """
    Runs a function with function_args
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


def test_mmr():
    size = 231
    data = [b"\xaa" * 32] * size

    interface = deploy()

    result = call(interface, "testMMR", function_args=[data])
    print(result["result"].hex())
    print(result["gas"])


def verify_subpeak():
    size = 10
    data = [b"\xaa" * 32] * size

    interface = deploy()

    hashes = import_pkl("hashes_10.pkl")
    peaks = import_pkl("peaks_10.pkl")

    mmr_proof = [
        [int_to_bytes(3), hashes[1], zero_bytes(), int_to_bytes(2)],
        [int_to_bytes(7), zero_bytes(), hashes[6], int_to_bytes(2)],
        [int_to_bytes(15), zero_bytes(), hashes[14], int_to_bytes(0)],
    ]
    result = call(
        interface, "verifySubpeak", function_args=[hashes[2], mmr_proof, 0, peaks],
    )

    mmr_proof = [
        [int_to_bytes(3), hashes[1], zero_bytes(), int_to_bytes(2)],
        [int_to_bytes(7), zero_bytes(), hashes[6], int_to_bytes(2)],
        [int_to_bytes(15), zero_bytes(), hashes[14], int_to_bytes(0)],
        [int_to_bytes(18), hashes[16], zero_bytes(), int_to_bytes(1)],
    ]
    result = call(
        interface, "verifySubpeak", function_args=[hashes[17], mmr_proof, 3, peaks],
    )

    result = call(interface, "verifySubpeak", function_args=[hashes[18], [], 4, peaks],)

    finalize(interface)


# verify_subpeak()
test_mmr()
