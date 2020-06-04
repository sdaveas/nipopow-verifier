"""
Add
- self.export_proof(fixed_fork_proof, fork_proof_name)
+ self.export_proof(fork_proof, fork_proof_name)
at create_proof.py
"""


import sys

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool


def main():
    """
    Test for backends
    """

    proof_tool = ProofTool("../data/proofs/")
    proof_tool.fetch_proof(80)
    (submit_n, contest_n, _, _, _, _) = proof_tool.create_proof_and_forkproof(
        80, 10, 25
    )

    proof = Proof()
    proof.set(proof_tool.fetch_proof_by_name(submit_n))

    c_proof = Proof()
    c_proof.set(proof_tool.fetch_proof_by_name(contest_n))

    interface = ContractInterface(
        contract={"path": "../OldContract.sol", "ctor": []}, backend="geth"
    )

    result = interface.call(
        "submitEventProof",
        function_args=[proof.headers, proof.siblings, proof.headers[-1]],
        value=pow(10, 17),
    )
    sum = 0
    print(result)
    for e in result["events"]:
        print(e[0], "\t", e[1])
        sum += e[1]
    print("Sum:", sum)

    result = interface.call(
        "submitContestingProof",
        function_args=[c_proof.headers, c_proof.siblings, c_proof.headers[-1]],
    )

    interface.end()

    sum = 0
    print(result)
    for e in result["events"]:
        print(e[0], "\t", e[1])
        sum += e[1]
    print("Sum:", sum)


if __name__ == "__main__":
    main()
