pragma solidity ^0.6.2;

//import "strings.sol";

contract Crosschain {

    constructor(bytes32 genesis) public {
        genesis_block_hash = genesis;
    }

    // The genesis block hash
    bytes32 genesis_block_hash;
    // Collateral to pay.
    uint constant z = 100000000000000000; // 0.1 eth

    // Nipopow proof.
    struct Nipopow {
        mapping (bytes32 => bool) curProofMap;
        mapping (uint => uint) levelCounter;
        bytes32[] best_proof;
    }

    struct Event {
        address payable author;
        uint expire;
        Nipopow proof;
    }

    // The key is the key value used for the predicate. In our case
    // the block header hash.
    mapping (bytes32 => Event) events;
    mapping (bytes32 => bool) finalized_events;

    // Security parameters.
    uint constant m = 15;
    uint constant k = 6; // Should be bigger.

    function memcpy(uint dest, uint src, uint len) private pure {
        // Copy word-length chunks while possible
        for(; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }
        // Copy remaining bytes.
        uint mask = 256 ** (32 - len) - 1;
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    // Hash the header using double SHA256
    function hash_header(
        bytes32[4] memory header
    )
        internal
        pure
        returns(bytes32)
    {
        // Compute the hash of 112-byte header.
        string memory s = new string(112);
        uint sptr;
        uint hptr;
        assembly { sptr := add(s, 32) }
        assembly { hptr := add(header, 0) }
        memcpy(sptr, hptr, 112);
        return sha256(abi.encodePacked(sha256(abi.encodePacked(s))));

    }

    function predicate(
        Nipopow storage proof,
        bytes32 block_of_interest
    )
        internal
        view
        returns (bool)
    {

        bool _predicate = false;
        for (uint i = 0; i < proof.best_proof.length; i++) {
            if (proof.best_proof[i] == block_of_interest) {
                _predicate = true;
                break;
            }
        }
        return _predicate;
    }

    function get_lca(
        Nipopow storage nipopow,
        bytes32[] memory c_proof
    )
        internal
        returns(uint, uint)
    {

        for (uint i = 0; i < c_proof.length; i++) {
            nipopow.curProofMap[c_proof[i]] = true;
        }

        bytes32 lca_hash;

        uint b_lca = 0;
        uint c_lca = 0;
        for (uint i = 0; i < nipopow.best_proof.length; i++) {
            if (nipopow.curProofMap[nipopow.best_proof[i]]) {
                b_lca = i;
                lca_hash = nipopow.best_proof[i];
                break;
            }
        }

        // Get the index of lca in the current_proof.
        for (uint i = 0; i < c_proof.length; i++) {
            if (lca_hash == c_proof[i]) {
                c_lca = i;
                break;
            }
        }

        // Clear the map. We don't need it anymore.
        for (uint i = 0; i < c_proof.length; i++) {
            nipopow.curProofMap[c_proof[i]] = false;
        }

        return (b_lca, c_lca);
    }

    // TODO: Implement the O(log(max_level)) algorithm.
    function get_level(
        bytes32 hashed_header
    )
        internal
        pure
        returns(uint256)
    {
        uint256 hash = uint256(hashed_header);

        for (uint i = 0; i <= 255; i++) {
            // Change endianess.
            uint pow = (i/8) * 8 + 8 - (i % 8) - 1;
            uint256 mask = 2 ** pow;
            if ((hash & mask) != 0) {
                return uint8(i);
            }
        }
        return 0;
    }

    function best_arg(
        Nipopow storage nipopow,
        bytes32[] memory proof,
        uint al_index
    )
        internal returns(uint256)
    {
        uint max_level = 0;
        uint256 max_score = 0;
        uint cur_level = 0;

        // Count the frequency of the levels.
        for (uint i = 0; i < al_index; i++) {
            cur_level = get_level(proof[i]);

            // Superblocks of level m are also superblocks of level m - 1.
            for (uint j  = 0; j <= cur_level; j++) {
                nipopow.levelCounter[j]++;
            }

            if (max_level < cur_level) {
                max_level = cur_level;
            }
        }

        for (uint i = 0; i <= max_level; i++) {
            uint256 cur_score = uint256(nipopow.levelCounter[i] * 2 ** i);
            if (nipopow.levelCounter[i] >= m && cur_score > max_score) {
                max_score = nipopow.levelCounter[i] * 2 ** i;
            }
            // clear the map.
            nipopow.levelCounter[i] = 0;
        }

        return max_score;
    }

    function compare_proofs(
        Nipopow storage nipopow,
        bytes32[] memory contesting_proof
    )
        internal
        returns(bool)
    {
        if (nipopow.best_proof.length == 0) {
            return true;
        }
        uint proof_lca_index;
        uint contesting_lca_index;
        (proof_lca_index, contesting_lca_index)
        = get_lca(nipopow, contesting_proof);
        return best_arg(nipopow, contesting_proof, contesting_lca_index) >
        best_arg(nipopow, nipopow.best_proof, proof_lca_index);
    }

    function verify_merkle(
        bytes32 roothash,
        bytes32 leaf,
        uint8 mu,
        bytes32[] memory siblings
    )
        pure
        internal
    {
        bytes32 h = leaf;
        for (uint i = 0; i < siblings.length; i++) {
            uint8 bit = mu & 0x1;
            if (bit == 1) {
                h = sha256(abi.encodePacked(
                    sha256(abi.encodePacked(siblings[siblings.length-i-1], h)
                          )));
            } else {
                h = sha256(abi.encodePacked(
                    sha256(abi.encodePacked(h, siblings[siblings.length-i-1])
                          )));
            }
            mu >>= 1;
        }
        require(h == roothash, 'Merkle verification failed');
    }

    // shift bits to the most segnificant byte (256-8 = 248)
    // and cast it to a 8-bit uint
    function b32_to_uint8(bytes32 _b) private pure returns (uint8) {
        return uint8(byte(_b << 248));
    }

    function validate_interlink(
        bytes32[4][] memory headers,
        bytes32[] memory hashed_headers,
        bytes32[] memory siblings
    )
        internal
        pure
    {
        uint ptr = 0; // Index of the current sibling
        for (uint i = 1; i < headers.length; i++) {
            // hold the 3rd and 4th least significant bytes
            uint8 branch_length = b32_to_uint8((headers[i][3] >> 8) & bytes32(uint(0xff)));
            uint8 merkle_index  = b32_to_uint8((headers[i][3] >> 0) & bytes32(uint(0xff)));

            require(branch_length <= 5, 'Branch length too big');
            require(merkle_index <= 32, 'Merkle index too big');

            // Copy siblings.
            bytes32[] memory _siblings = new bytes32[](branch_length);
            for (uint8 j = 0; j < branch_length; j++) _siblings[j] = siblings[ptr+j];
            ptr += branch_length;

            // Verify the merkle tree proof
            verify_merkle(headers[i - 1][0], hashed_headers[i],
                          merkle_index, _siblings);
        }
    }

    // Genesis is the last element of headers at index headers[headers.length-1].
    function verify_genesis(bytes32 _genesis) internal view {
        require(genesis_block_hash == _genesis, "Invalid genesis");
    }

    // If existing_proof[ex_lca:] is subset of contesting_proof[cont_lca:]
    // returns true, false otherwise
    function subset_proof(
        bytes32[] memory existing, uint existing_lca,
        bytes32[] memory contesting, uint contesting_lca
    ) internal pure returns(bool)
    {
        // If existing proof does not yet exists, return true
        if (existing.length == 0 && contesting.length != 0) {
            return true;
        }

        bool subset = true;
        uint j = contesting_lca;

        for (uint i = existing_lca; subset == true && i < existing.length; i++) {
            while (existing[i] != contesting[j]) {
                j++;
                if (j >= contesting.length) {
                    subset = false;
                    break;
                }
            }
        }

        return subset;
    }

    // contesting_proof -> contesting_proof_hashed_headers
    // headers -> contesting proof headers
    function verify(
        Nipopow storage proof,
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory block_of_interest
    )
        internal
        returns(bool)
    {

        verify_genesis(hash_header(headers[headers.length-1]));

        bytes32[] memory contesting_proof = new bytes32[](headers.length);
        for (uint i = 0; i < headers.length; i++) {
            contesting_proof[i] = hash_header(headers[i]);
        }

        // Throws if invalid.
        validate_interlink(headers, contesting_proof, siblings);

        if (compare_proofs(proof, contesting_proof)) {
            uint existing_lca;
            uint contesting_lca;
            (existing_lca, contesting_lca) = get_lca(proof, contesting_proof);

            if (subset_proof(proof.best_proof, existing_lca, contesting_proof, contesting_lca) == false) {
                return false;
            }
            // require(subset_proof(proof.best_proof, p_lca, contesting_proof, c_lca), "Subset");

            proof.best_proof = contesting_proof;
        }
        else {
            return true;
        }

        return predicate(proof, hash_header(block_of_interest));
    }

    // TODO: Deleting a mapping is impossible without knowing
    // beforehand all the keys of the mapping. That costs gas
    // and it may be in our favor to never delete this stored memory.
    function submit_event_proof(
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory block_of_interest
    )
        public
        payable
        returns(bool)
    {

        bytes32 hashed_block = hash_header(block_of_interest);

        if (msg.value < z) {
            return false;
        }

        // No proof for that event for the moment.
        if (events[hashed_block].expire == 0
            && events[hashed_block].proof.best_proof.length == 0
        && verify(events[hashed_block].proof, headers,
                  siblings, block_of_interest)) {
                      events[hashed_block].expire = block.number + k;
                      events[hashed_block].author = msg.sender;

                      return true;
                  }

                  return false;
    }

    function finalize_event(
        bytes32[4] memory block_of_interest
    ) public
        returns(bool)
    {
        bytes32 hashed_block = hash_header(block_of_interest);

        if (events[hashed_block].expire == 0 ||
            block.number < events[hashed_block].expire) {
            return false;
        }
        finalized_events[hashed_block] = true;
        events[hashed_block].expire = 0;
        events[hashed_block].author.transfer(z);

        return true;
    }


    function submit_contesting_proof(
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory block_of_interest
    )
        public
        returns(bool)
    {
        bytes32 hashed_block = hash_header(block_of_interest);

        if (events[hashed_block].expire <= block.number) {
            return false;
        }


        if (!verify(events[hashed_block].proof, headers,
                    siblings, block_of_interest)) {
                        events[hashed_block].expire = 0;
                        msg.sender.transfer(z);
                        return true;
                    }

                    return false;
    }

    function event_exists(
        bytes32[4] memory block_header
    )
        public
        view
        returns(bool)
    {
        bytes32 hashed_block = hash_header(block_header);
        return finalized_events[hashed_block];
    }
}
