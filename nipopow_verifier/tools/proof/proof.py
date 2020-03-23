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

    def set(self, proof, proof_name="", header_map=None, interlink_map=None):
        """
        Registers a proof in the object
        """

        self.proof = proof
        self.name = proof_name
        self.headers, self.siblings = self.extract_headers_siblings(self.proof)
        self.size = len(self.proof)

        self.best_level, self.best_score = best_level_and_score(self.proof)
        print("Best level:", self.best_level)
        print("Best score:", self.best_score)

        if header_map is None or interlink_map is None:
            print(" No interlink. Cannot create max level subproof.")
            return

        prefix = []
        prefix = self._best_level_subproof(
            self.proof, self.best_level, header_map, interlink_map
        )

        # self.best_level_subproof = best_level_subproof
        # self.best_level_subproof_size = len(self.best_level_subproof)


def header_level(p):
    """
        Computes the level of a proof block
        """

    n_bits = p[104:108]
    n_bits_int = int().from_bytes(n_bits, "little")
    target = blockchain_utils.bits_to_target(n_bits_int)
    hash = blockchain_utils.uint256_from_str(blockchain_utils.Hash(p))
    level = (int(target / hash)).bit_length() - 1
    return level


def best_level_and_score(proof, m=1):
    """
    Returns a proof's best level and its score
    """

    from collections import defaultdict

    levels = defaultdict(lambda: 0)
    for p in proof:
        level = header_level(p)
        levels[level] += 1
        # for l in range(level):
        #     levels[l] += 1

    keys = sorted(levels.keys(), reverse=True)
    for i in range(len(keys) - 1):
        levels[keys[i + 1]] += levels[keys[i]]

    max_score = 0
    max_level = 0
    curr_level = 0
    for l in keys:
        curr_score = levels[l] * pow(2, l)
        if levels[l] > m and curr_score > max_score:
            max_score = curr_score
            max_level = l

    print("Levels:", levels)
    print("Level:", max_level)
    print("Score:", max_score)
    return max_level, max_score


def get_first_blocks_below_level(proof, max_level):
    """
    Return the first blocks that have level < max_level
    """

    suffix = []
    for p in proof:
        if header_level(p) >= max_level:
            break
        else:
            suffix.append(p)
    return suffix.reverse()


def array_to_list(array):
    if len(array) == 0:
        return ()
    return (array[0], array_to_list(array[1:]))


def skip_headers_below_level(header, header_map, interlink_map, level):

    header = header.GetHash()
    interlink_list = blockchain_utils.list_flatten(interlink_map[header])
    while len(interlink_list) >= level:
        new_interlink_list = interlink_list

        for i in range(level):
            new_interlink_list[i] = interlink_list[level]

        hashed_interlink = blockchain_utils.hash_interlink(new_interlink_list)
        print(header_map[header].GetHash().hex())
        print(header_map[header].hashInterlink.hex())
        h = header_map[header]
        header_map[header] = blockchain_utils.CBlockHeaderPopow(
            nVersion=h.nVersion,
            hashPrevBlock=h.hashPrevBlock,
            nTime=h.nTime,
            nBits=h.nBits,
            nNonce=h.nNonce,
            hashInterlink=h.hashInterlink,
        )

        interlink_map[header] = array_to_list(new_interlink_list)
        prev_header = header
        header = new_interlink_list[0]
        print("Next", header_map[header].GetHash().hex())
        interlink_list = blockchain_utils.list_flatten(interlink_map[header])

    new_header = prev_header

    return new_header, header_map, interlink_map


def change_interlink_bytes(header, new_interlink):
    if new_interlink == []:
        return header
    hashed_interlink = blockchain_utils.hash_interlink(new_interlink)
    new_header = hashed_interlink + header[32:]
    return new_header


def isolate_proof_level(proof, level):

    isolated_proof = []

    rev_proof = proof[::-1]

    start_index = None

    for i, r in enumerate(rev_proof):
        if header_level(r[0]) >= level:
            start_index = i
            break

    if start_index is None:
        return []

    isolated_proof.append(rev_proof[start_index])
    new_interlink = []

    for i in range(start_index + 1, len(rev_proof)):

        if header_level(rev_proof[i][0]) < level:
            continue

        new_header = change_interlink_bytes(rev_proof[i][0], new_interlink)
        if new_interlink == []:
            new_merkle_tree = rev_proof[i][1]
        else:
            new_merkle_tree = blockchain_utils.prove_interlink(new_interlink, 0)

        isolated_proof.append((new_header, ()))

        new_interlink = [blockchain_utils.Hash(new_header)]

        # blockchain_utils.verify_interlink(
        #     blockchain_utils.Hash(isolated_proof[-1][0]),
        #     blockchain_utils.hash_interlink(new_interlink),
        #     new_merkle_tree,
        # )

    return isolated_proof[::-1]


def main():
    pt = ProofTool()
    (
        proof_name,
        fork_proof_name,
        lca,
        header,
        header_map,
        interlink_map,
        fork_header_map,
        fork_interlink_map,
    ) = pt.create_proof_and_forkproof(3, 1, 1)

    level = 3
    new_header, new_header_map, new_interlink_map = skip_headers_below_level(
        header, header_map, interlink_map, level
    )

    proof = blockchain_utils.make_proof(
        header_map[new_header], new_header_map, new_interlink_map
    )
    print(len(proof))
    blockchain_utils.verify_proof(blockchain_utils.Hash(proof[0][0]), proof)

    # p = Proof()
    # p.set(
    #     pt.fetch_proof(proof_name), header_map=header_map, interlink_map=interlink_map
    # )
    # fp.set(pt.fetch_proof(fork_proof_name), interlink_map=fork_interlink_map)


if __name__ == "__main__":
    main()
