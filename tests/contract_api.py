"""
API for NiPoPoW verifier smart contract
"""

import sys

from config import contract_path, genesis, m, k, collateral, profiler

sys.path.append("../tools/interface/")
import contract_interface


def make_interface(backend):
    """
    Creates a contract interface
    """
    return contract_interface.ContractInterface(
        {"path": contract_path, "ctor": [genesis, m, k]},
        backend=backend,
        profiler=profiler,
    )


# TODO: This is code duplidation with the below function
def submit_event_proof(
    interface,
    proof,
    block_of_interest_index,
    collateral=collateral,
    from_address=None,
):
    """
    Call submit_event_proof of the verifier
    """

    return interface.call(
        "submitEventProof",
        function_args=[proof.headers, proof.siblings, block_of_interest_index],
        value=collateral,
        from_address=from_address,
    )


def dispute_existing_proof(
    interface, existing, block_of_interest_index, invalid_index
):
    """
    Calls disputeExistingProof(existingHeaders, existingHeadersHash, siblings)
    """

    return interface.call(
        "disputeProof",
        function_args=[
            proof.headers,
            proof.siblings,
            block_of_interest_index,
            invalid_index,
        ],
    )


# TODO: This is code duplidation with the above function
def submit_contesting_proof(
    interface, existing, lca, contesting, block_of_interest_index,
):
    """
    Calls contest_event_proof of the verifier
    """

    return interface.call(
        "submitContestingProof",
        function_args=[
            existing.hashed_headers,
            lca,
            contesting.best_level_subproof_headers,
            contesting.best_level_subproof_siblings,
            contesting.best_level,
            block_of_interest_index,
        ],
    )


def finalize_event(interface, block_of_interest):
    """
    Calls finalize_event of the verifier
    """

    return interface.call("finalizeEvent", function_args=[block_of_interest])


def event_exists(interface, block_of_interest):
    """
    Calls event_exists of the contract
    """

    return interface.call("eventExist", function_args=[block_of_interest])


def validate_interlink(interface, proof, profile=True):
    """
    Calls validateInterlink of contract
    """

    return interface.call(
        "validateInterlinks",
        function_args=[proof.headers, proof.hashed_headers, proof.siblings],
    )
