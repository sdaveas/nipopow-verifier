"""
run with
$ pytest -v -s test_submit_over_contest.py
"""

import sys

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface
from config import errors, extract_message_from_error, genesis, m, k
import pytest


def call(interface, function_name, function_args=[], collateral=0):
    """
    Runs the output of a function
    """

    contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]
    function = contract.get_function_by_name(function_name)(*function_args)
    res = function.call({"from": from_address, "value": collateral})
    tx_hash = function.transact({"from": from_address, "value": collateral})
    receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    return {"result": res, "gas": receipt["gasUsed"]}


@pytest.fixture
def init_environment():
    """
    This runs before every test
    """

    global backend
    global interface

    backend = "ganache"
    interface = ContractInterface(
        "../contractNipopow.sol",
        backend=backend,
        constructor_arguments=[genesis, m, k],
    )


def test_submit_disjoint_proofs(init_environment):
    """
    Test old disjoint with two arrays
    array_1: [0] ------+------ [-1]
                       |
    array_2: [0] ------+
    """

    array_1 = []
    array_2 = []
    size = 10
    lca = int(size / 2)

    for i in range(size):
        array_1.append(b"\xaa" + i.to_bytes(31, "big"))
        if i >= lca:
            pref = b"\xaa"
        else:
            pref = b"\xff"
        array_2.append(pref + i.to_bytes(31, "big"))

    res = call(interface, "disjointProofs", [array_1, array_2, lca])
    assert res["result"] == False

    res = call(interface, "disjointProofsFixed", [array_1, array_2, lca])
    assert res["result"] == True
