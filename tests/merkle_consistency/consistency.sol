pragma solidity ^0.6.0;


contract consistency {
    function closestPow2(uint256 number) public pure returns (uint256) {
        uint256 closest = 1;
        while ((closest << 1) <= number) {
            closest <<= 1;
        }
        require(closest & (closest - 1) == 0, "Not power of 2");
        if (closest == number) {
            closest /= 2;
        }
        return closest;
    }

    function log2Ceiling(uint256 _number) public returns (uint256) {
        uint256 log2;
        uint256 number = _number;
        while (number > 0) {
            number >>= 1;
            log2++;
        }
        return log2;
    }

    function concatArrays(bytes32[] memory a1, bytes32[] memory a2)
        public
        returns (bytes32[] memory)
    {
        bytes32[] memory a = new bytes32[](a1.length + a2.length);

        for (uint256 i = 0; i < a1.length; i++) {
            a[i] = a1[i];
        }

        for (uint256 i = 0; i < a2.length; i++) {
            a[i + a1.length] = a2[i];
        }
        return a;
    }

    function merkleTreeHashRec(bytes32[] memory data) public returns (bytes32) {
        uint256 n = data.length;
        if (n == 1) {
            return sha256(abi.encodePacked(uint256(0), data[0]));
            // return data;
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

    function createSiblings(uint256 _n, uint256 _m)
        public
        returns (bool[] memory)
    {
        uint256 n = _n;
        uint256 m = _m;
        bool[] memory siblings = new bool[](log2Ceiling(_n));
        uint256 siblingsIndex;

        do {
            uint256 k = closestPow2(n);
            if (m < k) {
                siblings[siblingsIndex++] = true;
                n = k;
            } else {
                siblings[siblingsIndex++] = false;
                n = n - k;
                m = m - k;
            }
        } while (n != 1);

        bool[] memory rev_siblings = new bool[](siblingsIndex);
        for (uint256 i = 0; i < siblingsIndex; i++) {
            rev_siblings[i] = siblings[siblingsIndex - 1 - i];
        }

        return rev_siblings;
    }

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

}
