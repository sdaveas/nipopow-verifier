pragma solidity ^0.6.0;


contract Consistency {
    // Returns the ceiling of log2(number) ie the number number's digits
    function log2Ceiling(uint256 _number) public returns (uint256) {
        uint256 _log2;
        uint256 number = _number;
        while (number > 0) {
            number >>= 1;
            _log2++;
        }
        return _log2;
    }

    // Returns 2^i so that number/2 < 2^i < number
    function closestPow2(uint256 number) public pure returns (uint256) {
        if (number == 0 || number == 1) return 0;
        uint256 pow = 1;
        while (pow << 1 < number) {
            pow <<= 1;
        }
        require(pow & (pow - 1) == 0, "Not a power of 2");
        return pow;
    }

    // Substitute for array[start:end] for bool[]
    function subArrayBool(bool[] memory array, uint256 start, uint256 end)
        public
        returns (bool[] memory)
    {
        require(end > start, "Invalid limits");
        require(start < array.length, "Invalid limits");
        require(end <= array.length, "Invalid limits");
        bool[] memory subArray = new bool[](end - start);
        for (uint256 i = start; i < end; i++) {
            subArray[i - start] = array[i];
        }
        return subArray;
    }

    // Returns the root of merkle tree as computed from data (recursive)
    function merkleTreeHashRec(bytes32[] memory data) public returns (bytes32) {
        uint256 n = data.length;
        if (n == 1) {
            return sha256(abi.encodePacked(uint256(0), data[0]));
        }

        uint256 k = closestPow2(n);

        bytes32[] memory left = new bytes32[](k);
        for (uint256 i = 0; i < k; i++) {
            left[i] = data[i];
        }

        bytes32[] memory right = new bytes32[](n - k);
        for (uint256 i = 0; i < n - k; i++) {
            right[i] = data[i + k];
        }

        return
            sha256(
                abi.encodePacked(
                    uint256(1),
                    merkleTreeHashRec(left),
                    merkleTreeHashRec(right)
                )
            );
    }

    // Returns the root of merkle tree as computed from data
    function merkleTreeHash(bytes32[] memory data) public returns (bytes32) {
        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint256 step = 2;
        while (step / 2 < data.length) {
            for (uint256 i = 0; i < data.length - step / 2; i += step) {
                data[i] = sha256(
                    abi.encodePacked(uint256(1), data[i], data[i + step / 2])
                );
            }
            step *= 2;
        }

        return data[0];
    }

    // Returns the merkle proof of node indicated by _index in data
    function path(bytes32[] memory data, uint256 _index)
        public
        returns (bytes32[] memory)
    {
        uint256 index = _index;
        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint256 proofIndex;
        uint256 proofLength = log2Ceiling(data.length);
        bytes32[] memory proof = new bytes32[](proofLength);

        uint256 step = 2;
        while (step / 2 < data.length) {
            for (uint256 i = 0; i < data.length - step / 2; i += step) {
                if (i == index) {
                    proof[proofIndex++] = data[i + step / 2];
                    index = i;
                } else if (i + step / 2 == index) {
                    proof[proofIndex++] = data[i];
                    index = i;
                }
                data[i] = sha256(
                    abi.encodePacked(uint256(1), data[i], data[i + step / 2])
                );
            }
            step *= 2;
        }

        return proof;
    }

    // Creates an array that indicate whether the sibling is left (false) of right (true)
    function createSiblings(uint256 _n, uint256 _m)
        public
        returns (bool[] memory)
    {
        uint256 n = _n;
        uint256 m = _m;
        bool[] memory siblings = new bool[](log2Ceiling(_n));
        uint256 siblingsIndex;
        uint256 k;

        do {
            k = closestPow2(n);
            if (m < k) {
                siblings[siblingsIndex] = true;
                n = k;
            } else {
                siblings[siblingsIndex] = false;
                n = n - k;
                m = m - k;
            }
            siblingsIndex++;
        } while (n != 1);

        bool[] memory rev_siblings = new bool[](siblingsIndex);
        for (uint256 i = 0; i < siblingsIndex; i++) {
            rev_siblings[i] = siblings[siblingsIndex - 1 - i];
        }

        return rev_siblings;
    }

    // Returns the root as calculated from a path
    function rootFromPath(
        bytes32 nodeData,
        uint256 _n,
        bytes32[] memory proof,
        uint256 _m
    ) public returns (bytes32) {
        bytes32 h = sha256(abi.encodePacked(uint256(0), nodeData));
        bool[] memory siblingsPos = createSiblings(_n, _m);
        bytes32 left;
        bytes32 right;
        for (uint256 i = 0; i < siblingsPos.length; i++) {
            if (siblingsPos[i] == true) {
                left = h;
                right = proof[i];
            } else {
                left = proof[i];
                right = h;
            }
            h = sha256(abi.encodePacked(uint256(1), left, right));
        }
        return h;
    }

    // Alternative for array[start:end]
    function subArray(bytes32[] memory array, uint256 start, uint256 end)
        public
        returns (bytes32[] memory)
    {
        require(end > start, "Invalid limits");
        require(start < array.length, "Invalid limits");
        require(end <= array.length, "Invalid limits");
        bytes32[] memory subArray = new bytes32[](end - start);
        for (uint256 i = start; i < end; i++) {
            subArray[i - start] = array[i];
        }
        return subArray;
    }

    // Creates a consistancy proof for prefix _m of data
    function consProofSub(bytes32[] memory data, uint256 _m)
        public
        returns (bytes32[] memory)
    {
        uint256 start = 0;
        uint256 end = data.length;
        uint256 m = _m;
        uint256 k;

        uint256 proofIndex;
        bytes32[] memory proof = new bytes32[](log2Ceiling(data.length) + 1);

        while (m != end - start) {
            k = closestPow2(end - start);

            if (m <= k) {
                proof[proofIndex] = merkleTreeHash(
                    subArray(data, start + k, end)
                );
                end = start + k;
            } else {
                proof[proofIndex] = merkleTreeHash(
                    subArray(data, start, start + k)
                );
                start += k;
                m -= k;
            }
            proofIndex++;
            require(proofIndex < proof.length, "Proof too small");
        }

        proof[proofIndex] = merkleTreeHash(subArray(data, start, start + m));

        return proof;
    }

    // Returns the root hash of the merkle tree as constructed from proof from a
    // prefix of n0 out of n1 nodes
    function root0FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        returns (bytes32)
    {
        require(n0 < n1, "n0 >= n1");
        uint256 k = closestPow2(n1);
        if (n0 < k) {
            return
                root0FromConsProof(subArray(proof, 0, proof.length - 1), n0, k);
        }
        if (n0 == k) {
            return proof[proof.length - 2];
        }
        bytes32 left = proof[proof.length - 1];
        bytes32 right = root0FromConsProof(
            subArray(proof, 0, proof.length - 1),
            n0 - k,
            n1 - k
        );
        return sha256(abi.encodePacked(uint256(1), left, right));
    }

    // Returns the root hash of the merkle tree as constructed from proof from n1 nodes
    function root1FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        returns (bytes32)
    {
        if (proof.length == 2)
            return sha256(abi.encodePacked(uint256(1), proof[0], proof[1]));

        uint256 k = closestPow2(n1);
        bytes32 left;
        bytes32 right;

        if (n0 < k) {
            left = root1FromConsProof(
                subArray(proof, 0, proof.length - 1),
                n0,
                k
            );
            right = proof[proof.length - 1];
        } else {
            left = proof[proof.length - 1];
            right = root1FromConsProof(
                subArray(proof, 0, proof.length - 1),
                n0 - k,
                n1 - k
            );
        }
        return sha256(abi.encodePacked(uint256(1), left, right));
    }
}
