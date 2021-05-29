
"""
run with
$ python measure_submit_contest.py
"""

import sys

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

sys.path.append("../tests/")
from contract_api import (
    make_interface,
    submit_event_proof,
    submit_contesting_proof,
)
from config import errors, extract_message_from_error, genesis

import pytest

def init_proofs(backend, mainchain_blocks, fork_point, additional_blocks):
    """
    create proofs for two contesting chains

    mainchain_blocks
    +-------------+
    v             v

    --------+----->  Chain A
            |
       +->  +-------->  Chain B
       |
       |    ^        ^
       |    |        |
       |    +--------+
       |          |
    fork_point    additional_blocks

    """

    pt = ProofTool()
    pt.fetch_proof(mainchain_blocks)
    (
        submit_proof_name,
        contest_proof_name,
        contest_lca,
        contest_header,
        contest_header_map,
        contest_interlink_map,
    ) = pt.create_proof_and_forkproof(mainchain_blocks, fork_point, additional_blocks)

    submit_proof = Proof()
    submit_proof.set(pt.fetch_proof(submit_proof_name))

    contest_proof = Proof()
    contest_proof.set(
        pt.fetch_proof(contest_proof_name),
        header=contest_header,
        header_map=contest_header_map,
        interlink_map=contest_interlink_map,
    )

    return (submit_proof, contest_lca, contest_proof)

def submit_over_contest(backend, mainchain_blocks, fork_point, additional_blocks):
    """
    Display gas for submit and contest proofs
    Contest must succeed if we want to measure gas for both phases, so be sure contesting proof is bigger
    """

    # compile and deploy smart contract
    interface = make_interface(backend)

    # retrieve submit and contest proof
    (
        submit_proof,
        contest_lca,
        contest_proof
    ) = init_proofs(backend, mainchain_blocks, fork_point, additional_blocks)


    # we want to prove the existance of a block that exists only in submit chain
    # for convinience, we pick the tip of submit proof
    block_of_interest_index = 0

    # start submit phase
    res = submit_event_proof(interface, submit_proof, block_of_interest_index,)
    # get the result. This includes the amount of gas used
    print("Submit proof gas:", res["gas"])
    # be sure that worked
    assert res["result"], "submit proof failed"


    # start contest phase
    res = submit_contesting_proof(
        interface,
        submit_proof,
        contest_lca,
        contest_proof,
        block_of_interest_index,
    )
    # get the result. This includes the amount of gas used
    print("Contest proof gas:", res["gas"])
    # be sure that worked
    assert res["result"], "contest proof failed"

    # close interfase
    interface.end()

def main():
    submit_over_contest("geth", 1000000, 100, 200)

main()
