"""
run with
$ pytest -v -s test_disjoint_proofs.py
"""

import sys

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface
from config import genesis, m, k
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
        {"path": "../contractNipopow.sol", "ctor": [genesis, m, k]},
        backend=backend,
    )

    global submit_proof
    global contest_proof

    pt = ProofTool()
    pt.fetch_proof(20)
    (
        submit_proof_name,
        contest_proof_name,
        contest_lca,
        contest_header,
        contest_header_map,
        contest_interlink_map,
    ) = pt.create_proof_and_forkproof(100, 50, 50)

    submit_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))

    contest_proof = Proof()
    contest_proof.set(
        pt.fetch_proof(contest_proof_name),
        header=contest_header,
        header_map=contest_header_map,
        interlink_map=contest_interlink_map,
    )


def test_create_disjoint_fork_proofs(init_environment):
    """
    Creates a chain and a fork chain

                            lca
                             v
    submit_proof : [0] ------b------ [-1]
                             |
    contest_proof: [0] ------+

    truncated_proof = contest_proof[:lca]
    """

    pt = ProofTool()
    original_proof = submit_proof.proof
    fork_proof = contest_proof.proof
    truncated_proof, lca = pt.truncate_fork_proof(original_proof, fork_proof)
    for o_header, _ in original_proof[:lca]:
        for t_header, _ in truncated_proof:
            assert o_header != t_header


def test_submit_disjoint_proofs(init_environment):
    """
    Test old disjoint with two arrays
    chain_1: [0] ------+------ [-1]
                       |
    chain_2: [0] ------+
    """

    chain_1 = []
    chain_2 = []
    size = 10
    lca = size // 2

    for i in range(size):
        chain_1.append(b"\xaa" + i.to_bytes(31, "big"))
        if i >= lca:
            pref = b"\xaa"
        else:
            pref = b"\xff"
        chain_2.append(pref + i.to_bytes(31, "big"))

    if i in range(size):
        if size >= lca:
            res = call(interface, "disjointProofs", [chain_1, chain_2, i])
            assert res["result"] == False
        else:
            res = call(interface, "disjointProofs", [chain_1, chain_2, i])
            assert res["result"] == True
