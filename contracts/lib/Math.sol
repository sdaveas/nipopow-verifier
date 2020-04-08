// Some math utils

pragma solidity ^0.6.0;


library Math {
    // Returns the ceiling of log2(number) ie the number number's digits
    function log2Ceiling(uint256 _number) public pure returns (uint256) {
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
        if (number <= 1) return 0;
        uint256 pow = 1;
        while (pow << 1 < number) {
            pow <<= 1;
        }
        require(pow & (pow - 1) == 0, "Not a power of 2");
        return pow;
    }
}
