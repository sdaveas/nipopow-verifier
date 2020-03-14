pragma solidity ^0.6.2;
pragma experimental ABIEncoderV2;

contract HashSetTest {
    struct HashSet {
        bytes32[8][] buckets;
        uint[] bucketTip;
    }

    function makeHashSet(bytes32[] memory elements) public pure returns (HashSet memory) {
        uint size = elements.length;
        HashSet memory m;
        m.buckets = new bytes32[8][](size);
        m.bucketTip = new uint[](size);
        for (uint i = 0; i < size; ++i) {
            if (existsInHashSet(m, elements[i])) {
                continue;
            }
            uint256 h = hashKey(elements[i], size);
            uint pos = m.bucketTip[h]++;
            m.buckets[h][pos] = elements[i];
        }
        return m;
    }


    function hashKey(bytes32 key, uint modulo) internal pure returns (uint256) {
        return uint256(sha256(abi.encodePacked(key))) % modulo;
    }

    function existsInHashSet(HashSet memory m, bytes32 key) internal pure returns (bool) {
        uint h = hashKey(key, m.buckets.length);
        for (uint i = 0; i < m.bucketTip[h]; ++i) {
            if (m.buckets[h][i] == key) {
                return true;
            }
        }
        return false;
    }
}
