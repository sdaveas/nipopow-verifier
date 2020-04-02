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

    function log2Ceiling(uint256 number) public returns (uint256) {
        uint256 log2;
        while (number > 0) {
            number >>= 1;
            log2++;
        }
        return log2;
    }

    function concatArrays(bytes32[] memory a1, bytes32[] memory a2) public returns(bytes32[] memory) {
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

        return sha256(abi.encodePacked(uint256(1), merkleTreeHashRec(left), merkleTreeHashRec(right)));
    }

    function merkleTreeHash(bytes32[] memory data) public returns (bytes32) {

        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint256 step = 2;
        while(step/2 < data.length) {
            for (uint256 i = 0; i < data.length - step/2; i+=step) {
                data[i] = sha256(abi.encodePacked(uint256(1), data[i], data[i+step/2]));
            }
            step *= 2;
        }

        return data[0];
    }

    // untested
    function path(bytes32[] memory data, uint256 index) public returns (bytes32[] memory) {

        emit debug("Looking for", index);
        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint proofIndex;
        uint256 proofLength = log2Ceiling(data.length);
        bytes32[] memory proof = new bytes32[](proofLength);

        uint256 step = 2;
        while(step/2 < data.length) {
            emit debug("Round", proofIndex);
            for (uint256 i = 0; i < data.length - step/2; i+=step) {
                data[i] = sha256(abi.encodePacked(uint256(1), data[i], data[i+step/2]));
                if (i == index) {
                    emit debug("Sibling index", i + step/2);
                    proof[proofIndex++] = data[i + step/2];
                    index = i;
                }
                else if (i + step/2 == index) {
                    emit debug("Sibling index", i);
                    proof[proofIndex++] = data[i];
                    index = i;
                }
            }
            step *= 2;
        }

        return proof;
    }
}
