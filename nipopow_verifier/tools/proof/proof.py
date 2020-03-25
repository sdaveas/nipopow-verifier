"""
Store proofs to objects
proof = Proof()
proof.set(import_proof('myproof'))
"""
from bitcoin.core import Hash

from collections import defaultdict
import create_blockchain_new as blockchain_utils
from create_proof import ProofTool


class Proof:
    """
    Class to store a proof.
    The proof must be already exist. Once the Proof() object is created, call
    .set(proof) to initialize it
    """

    def __init__(self):
        self.name = ""
        self.proof = []
        self.headers = []
        self.hashed_headers = []
        self.siblings = []
        self.size = 0
        self.levels = {}
        self.scores = {}
        self.best_level = 0
        self.best_score = 0
        self.best_level_subproof = []
        self.best_level_subproof_headers = []
        self.best_level_subproof_siblings = []
        self.best_level_subproof_size = 0

    @staticmethod
    def str_to_bytes32(string):
        """
        convert string to bytes32
        """
        bytes32 = []
        for start in range(0, len(string), 32):
            bytes32.append(string[start : start + 32])
        return bytes32

    @staticmethod
    def extract_headers_siblings(proof):
        """
        Returns the headers and siblings of a proof
        """

        headers = []
        siblings = []
        # _mp stands for merkle proof
        # hs stands for headers.
        for _p in proof:
            _hs = _p[0]
            _mp = _p[1]
            # Copy the header to an array of 4 bytes32
            header = Proof.str_to_bytes32(_hs)
            # Encode the Merkle bits (_mu) in the largest byte
            # Encode the _mp size in the next largest byte
            assert 0 <= len(_mp) < 256
            _mu = sum(bit << i for (i, (bit, _)) in enumerate(_mp[::-1]))
            assert 0 <= _mu < 256
            # header[3] = chr(len(_mp)) + chr(_mu) + header[3][2:]
            header[3] = (
                header[3] + ("\x00" * 14).encode() + bytes([len(_mp)]) + bytes([_mu])
            )
            headers.append(header)

            for (_, sibling) in _mp:
                siblings.append(sibling)

        return headers, siblings

    def set(
        self, proof, proof_name="", header=None, header_map=None, interlink_map=None,
    ):
        """
        Registers a proof in the object
        """

        self.proof = proof
        self.name = proof_name
        self.headers, self.siblings = self.extract_headers_siblings(self.proof)

        for i in range(len(self.headers)):
            self.hashed_headers.append(Hash(self.proof[i][0]))

        self.size = len(self.proof)

        (
            self.best_level,
            self.best_score,
            self.levels,
            self.scores,
        ) = best_level_and_score(self.proof)

        for level in sorted(self.levels.keys()):
            print(
                "Level", level, "has", self.levels[level], "blocks with score", end=""
            )
            if level == self.best_level:
                print(" " + str(self.best_score) + " <- best")
            else:
                print(" " + str(self.scores[level]))

        if header is None or header_map is None or interlink_map is None:
            print("No interlink provided")
            return
        else:
            print(
                "Interlink provided. Creating isolated proof at level", self.best_level
            )

        self.best_level_subproof = isolate_proof_level(
            self.best_level, proof, header, header_map, interlink_map
        )
        (
            self.best_level_subproof_headers,
            self.best_level_subproof_siblings,
        ) = self.extract_headers_siblings(self.best_level_subproof)
        self.best_level_subproof_size = len(self.best_level_subproof)


def header_level(header):
    """
    Computes the level of a proof block
    """

    n_bits = header[104:108]
    n_bits_int = int().from_bytes(n_bits, "little")
    target = blockchain_utils.bits_to_target(n_bits_int)
    header_hash = blockchain_utils.uint256_from_str(blockchain_utils.Hash(header))
    level = (int(target / header_hash)).bit_length() - 1
    return level


# Linter made me do it
def best_level_and_score(proof, miou=6):
    """
    Returns a proof's best level and score
    """

    levels = defaultdict(lambda: 0)
    for header, _ in proof:
        level = header_level(header)
        levels[level] += 1

    top_level = max(levels.keys())

    print("Top level is", top_level)
    for l in range(top_level):
        if levels[l] == 0:
            levels[l] = 0

    keys = sorted(levels.keys(), reverse=True)
    for i in range(len(keys) - 1):
        levels[keys[i + 1]] += levels[keys[i]]

    scores = defaultdict(lambda: 0)

    max_score = 0
    max_level = 0
    for level in keys:
        curr_score = levels[level] * pow(2, level)
        if levels[level] >= miou and curr_score > max_score:
            max_score = curr_score
            max_level = level
        scores[level] = curr_score

    return max_level, max_score, levels, scores


def change_interlink_bytes(header, new_interlink):
    """
    Changes the header's bytes associated with a blocks's interlink hash.
    Meaning the first 32
    """

    if new_interlink == []:
        return header
    hashed_interlink = blockchain_utils.hash_interlink(new_interlink)
    new_header = hashed_interlink + header[32:]
    return new_header


def isolate_proof_level(level, fork_proof, header, header_map, interlink_map):
    """
    Returns a valid proof consisted by blocks of a certain level and above
    """

    start = []
    for p in fork_proof[::-1]:
        h, _ = p
        if header_level(h) >= level:
            break
        start.append(p)

    anchor = blockchain_utils.CBlockHeaderPopow.deserialize(h)

    interlink = blockchain_utils.list_flatten(interlink_map[header.GetHash()])
    proof = []
    mp = []
    while True:
        proof.append((header.serialize(), mp))
        if header == anchor or level >= len(interlink):
            break
        mp = blockchain_utils.prove_interlink(interlink, level)
        header = header_map[interlink[level]]
        blockchain_utils.verify_interlink(
            header.GetHash(), blockchain_utils.hash_interlink(interlink), mp
        )
        interlink = blockchain_utils.list_flatten(interlink_map[header.GetHash()])

    for s in start[::-1]:
        proof.append(s)

    blockchain_utils.verify_proof(blockchain_utils.Hash(proof[0][0]), proof)

    return proof


def main():
    """
    Test Proof
    """

    proof_tool = ProofTool()
    (
        proof_name,
        fork_proof_name,
        lca,
        fork_header,
        fork_header_map,
        fork_interlink_map,
    ) = proof_tool.create_proof_and_forkproof(100, 10, 20)

    my_proof = Proof()
    my_proof.set(proof_tool.fetch_proof(proof_name))
    p = my_proof.best_level_subproof

    my_fork_proof = Proof()
    my_fork_proof.set(
        proof_tool.fetch_proof(fork_proof_name),
        header=fork_header,
        header_map=fork_header_map,
        interlink_map=fork_interlink_map,
    )
    pp = my_fork_proof.best_level_subproof

    my_proof_tip = Proof()
    my_proof_tip.set(my_proof.proof[:lca])

    print(blockchain_utils.Hash(my_fork_proof.proof[-1][0]).hex())
    print(blockchain_utils.Hash(pp[-1][0]).hex())

    print("Best proof has length", len(my_fork_proof.best_level_subproof))


if __name__ == "__main__":
    main()
