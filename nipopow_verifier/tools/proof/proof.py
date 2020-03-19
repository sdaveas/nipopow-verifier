import create_blockchain_new as blockchain_utils

"""
Store proofs to objects
proof = Proof()
proof.set(import_proof('myproof'))
"""


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

    @staticmethod
    def _best_level_subproof(proof, max_level):
        """
        Returns all blocks of the indicated level
        """

        best_proof = []
        for p in proof:
            if header_level(p) == max_level:
                best_proof.append(p)

        return best_proof

    def set(self, proof, proof_name=""):
        """
        Registers a proof in the object
        """

        self.proof = proof
        self.name = proof_name
        self.headers, self.siblings = self.extract_headers_siblings(self.proof)
        self.size = len(self.proof)


def header_level(p):
    """
        Computes the level of a proof block
        """

    n_bits = p[0][104:108]
    n_bits_int = int().from_bytes(n_bits, "little")
    target = blockchain_utils.bits_to_target(n_bits_int)
    hash = blockchain_utils.uint256_from_str(blockchain_utils.Hash(p[0]))
    level = (int(target / hash)).bit_length() - 1
    return level


def best_level_and_score(proof):
    """
    Returns a proof's best level and its score
    """

    from collections import defaultdict

    levels = defaultdict(lambda: 0)
    for p in proof:
        level = header_level(p)
        levels[level] += 1
        for l in range(level):
            levels[l] += 1

    max_score = 0
    max_level = 0
    curr_level = 0
    for l in sorted(levels.keys(), reverse=True):
        curr_score = levels[l] * pow(2, l)
        if curr_score > max_score:
            max_score = curr_score
            max_level = l

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
