"""
Store proofs to objects
proof = Proof()
proof.set(import_proof('myproof'))
"""
from bitcoin.core import Hash


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

        for i in range(len(self.headers)):
            self.hashed_headers.append(Hash(self.proof[i][0]))

        self.size = len(self.proof)
