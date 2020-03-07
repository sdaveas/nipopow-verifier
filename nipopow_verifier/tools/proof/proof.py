"""
Class to store a proof.
The proof must be already exist. Once the Proof() object is created, call .set(proof) to initialize it
"""

class Proof:
    def __init__(self):
        self.name = ""
        self.proof = []
        self.headers = []
        self.siblings = []
        self.size = 0

    @staticmethod
    def str_to_bytes32(s):
        r = []
        for start in range(0,len(s),32):
            r.append(s[start:start+32])
        return r

    @staticmethod
    def extract_headers_siblings(proof):
        headers = []
        hashed_headers = []
        siblings = []
        # mp stands for merkle proof
        # hs stands for headers.
        for p in proof:
            hs = p[0]
            mp = p[1]
            # Copy the header to an array of 4 bytes32
            header = Proof.str_to_bytes32(hs)
            # Encode the Merkle bits (mu) in the largest byte
            # Encode the mp size in the next largest byte
            assert 0 <= len(mp) < 256
            mu = sum(bit << i for (i,(bit,_)) in enumerate(mp[::-1]))
            assert 0 <= mu < 256
            #header[3] = chr(len(mp)) + chr(mu) + header[3][2:]
            header[3] = header[3] + ('\x00'*14).encode() + bytes([len(mp)]) + bytes([mu])
            headers.append(header)

            for (_,sibling) in mp:
                siblings.append(sibling)

        return headers, siblings

    def set(self, proof, proof_name=''):
        self.proof = proof
        self.name = proof_name
        self.headers, self.siblings = self.extract_headers_siblings(self.proof)
        self.size = len(self.proof)
