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

}
