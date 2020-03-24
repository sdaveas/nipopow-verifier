"""
Store proofs to objects
proof = Proof()
proof.set(import_proof('myproof'))
"""

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

    def set(self, proof, proof_name=""):
        """
        Registers a proof in the object
        """

        self.proof = proof
        self.name = proof_name
        self.headers, self.siblings = self.extract_headers_siblings(self.proof)
        self.size = len(self.proof)

        (
            self.best_level,
            self.best_score,
            self.levels,
            self.scores,
        ) = best_level_and_score(self.proof)

        for level in sorted(self.levels.keys()):
            print(
                "Levle", level, "has", self.levels[level], "blocks with score", end=""
            )
            if level == self.best_level:
                print(" " + str(self.best_score) + " <- best")
            else:
                print(" " + str(self.scores[level]))

        self.best_level_subproof = isolate_proof_level(proof, self.best_level)
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
    Returns a proof's best level and its score
    """

    levels = defaultdict(lambda: 0)
    for header, _ in proof:
        level = header_level(header)
        levels[level] += 1

    keys = sorted(levels.keys(), reverse=True)
    for i in range(len(keys) - 1):
        levels[keys[i + 1]] += levels[keys[i]]

    scores = defaultdict(lambda: 0)

    max_score = 0
    max_level = 0
    for level in keys:
        curr_score = levels[level] * pow(2, level)
        if levels[level] > miou and curr_score > max_score:
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


def isolate_proof_level(proof, level):
    """
    Returns a valid proof consisted by blocks of a certain level and above
    """

    isolated_proof = []

    rev_proof = proof[::-1]

    start_index = None

    for i, block in enumerate(rev_proof):
        header, _ = block
        if header_level(header) >= level:
            start_index = i
            break

    if start_index is None:
        return []

    for p in rev_proof:
        isolated_proof.append(p)
        if header_level(header) >= level:
            break

    new_interlink = []

    for i in range(start_index + 1, len(rev_proof)):
        if header_level(rev_proof[i][0]) < level:
            continue
        new_header = change_interlink_bytes(rev_proof[i][0], new_interlink)
        #        if new_interlink == []:
        #            new_merkle_tree = rev_proof[i][1]
        #        else:
        #            new_merkle_tree = blockchain_utils.prove_interlink(new_interlink, 0)
        isolated_proof.append((new_header, []))
        new_interlink = [blockchain_utils.Hash(new_header)]

    isolated_proof = isolated_proof[::-1]
    blockchain_utils.verify_proof(
        blockchain_utils.Hash(isolated_proof[0][0]), isolated_proof[:-1]
    )

    return isolated_proof


def main():
    """
    Test Proof
    """

    proof_tool = ProofTool()
    proof_name, fork_proof_name, _ = proof_tool.create_proof_and_forkproof(10, 5, 10)

    my_proof = Proof()
    my_proof.set(proof_tool.fetch_proof(proof_name))
    p = my_proof.best_level_subproof

    my_fork_proof = Proof()
    my_fork_proof.set(proof_tool.fetch_proof(fork_proof_name))
    pp = my_fork_proof.best_level_subproof
    print(blockchain_utils.Hash(my_fork_proof.proof[-1][0]).hex())
    print(blockchain_utils.Hash(pp[-1][0]).hex())

    print("Best proof has length", len(my_fork_proof.best_level_subproof))


if __name__ == "__main__":
    main()
