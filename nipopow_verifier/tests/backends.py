"""
Run with
python test_backends.py --blocks=10 --backend=Py-EVM
"""

import sys

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface
from timer import Timer

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

from contract_api import submit_event_proof, submit_contesting_proof, make_interface
from config import extract_message_from_error, genesis

import argparse


def run_nipopow(backend, proof):
    """
    Make a call to verifier with proof.
    The block of interest is the last block of the chain.
    """

    block_of_interest = proof.headers[0]
    interface = make_interface(backend)
    _t = Timer()
    try:
        result = submit_event_proof(interface, proof, block_of_interest)
    except Exception as ex:
        print(ex)

        result = {"result": extract_message_from_error(ex)}
    del _t

    interface.end()

    return result["result"]


def main():
    """
    Test for backends
    """

    available_backends = ContractInterface.available_backends()
    parser = argparse.ArgumentParser(description="Benchmark Py-EVM, Ganache and Geth")
    parser.add_argument(
        "--backend",
        choices=available_backends + ["all"],
        required=True,
        type=str,
        help="The name of the EVM",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--blocks", type=int, help="Number of blocks")
    group.add_argument("--proof", type=str, help="Name of proof")
    parser.add_argument("--timer", action="store_true", help="Enable timers")

    args = parser.parse_args()
    backend = args.backend
    blocks = args.blocks
    proof_name = args.proof

    if backend == "all":
        backend = available_backends
    else:
        backend = [backend]

    proof_tool = ProofTool("../data/proofs/")

    if blocks is not None:
        proof = proof_tool.fetch_proof(blocks)
    elif proof_name is not None:
        proof = proof_tool.fetch_proof(proof_name)
    else:
        print("You need to provice --blocks of --proof")

    print("Proof lenght:", len(proof))

    _p = Proof()
    _p.set(proof)

    for _b in backend:
        print("Testing", _b)
        res = run_nipopow(_b, _p)
        print("Result:", res)


if __name__ == "__main__":
    main()
