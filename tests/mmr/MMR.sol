pragma solidity ^0.6.0;


contract MMR {
    event debug(string tag, uint256 value);

    struct Tree {
        bytes32 root;
    }

    bytes32 root;

    function testMMR(bytes32[] memory data)
        public
        returns (bytes32, bytes32[] memory, bytes32[] memory)
    {
        // Create array for hashes of leafs and internal nodes
        bytes32[] memory hashes = new bytes32[](getSize(data.length) + 1);

        // Populate hashes with leafs
        for (uint256 index = 0; index < data.length; index++) {
            // Hash the data of the node
            bytes32 dataHash = sha256(abi.encodePacked(data[index]));
            // Create leaf
            bytes32 leaf = hashLeaf(getSize(index) + 1, dataHash);
            // Put the hashed leaf to the array
            hashes[getSize(index) + 1] = leaf;
        }

        // Find peaks for the tree
        uint256[] memory peakIndexes = getPeakIndexes(data.length);
        // Starting from the left-most peak, get all peak hashes using _getOrCreateNode() function.
        bytes32[] memory peaks = new bytes32[](peakIndexes.length);
        for (uint256 i = 0; i < peakIndexes.length; i++) {
            peaks[i] = _getOrCreateNode(peakIndexes[i], hashes, 0);
        }
        root = peakBagging(data.length, peaks);

        (
            bytes32[] memory peakBaggingArray,
            bytes32[] memory siblings
        ) = getMerkleProof(hashes, data.length, 1);

        return (root, peakBaggingArray, siblings);
    }

    function getSize(uint256 width) public pure returns (uint256) {
        return (width << 1) - numOfPeaks(width);
    }

    function peakBagging(uint256 width, bytes32[] memory peaks)
        public
        pure
        returns (bytes32)
    {
        uint256 size = getSize(width);
        require(
            numOfPeaks(width) == peaks.length,
            "Received invalid number of peaks"
        );
        return
            sha256(
                abi.encodePacked(size, sha256(abi.encodePacked(size, peaks)))
            );
    }

    /** Pure functions */

    /**
     * @dev It returns the hash a parent node with hash(M | Left child | Right child)
     *      M is the index of the node
     */
    function hashBranch(uint256 index, bytes32 left, bytes32 right)
        public
        pure
        returns (bytes32)
    {
        return sha256(abi.encodePacked(index, left, right));
    }

    /**
     * @dev it returns the hash of a leaf node with hash(M | DATA )
     *      M is the index of the node
     */
    function hashLeaf(uint256 index, bytes32 dataHash)
        public
        pure
        returns (bytes32)
    {
        return sha256(abi.encodePacked(index, dataHash));
    }

    /**
     * @dev It returns the height of the highest peak
     */
    function mountainHeight(uint256 size) public pure returns (uint8) {
        uint8 height = 1;
        while (uint256(1) << height <= size + height) {
            height++;
        }
        return height - 1;
    }

    /**
     * @dev It returns the height of the index
     */
    function heightAt(uint256 index) public pure returns (uint8 height) {
        uint256 reducedIndex = index;
        uint256 peakIndex;
        // If an index has a left mountain subtract the mountain
        while (reducedIndex > peakIndex) {
            reducedIndex -= (uint256(1) << height) - 1;
            height = mountainHeight(reducedIndex);
            peakIndex = (uint256(1) << height) - 1;
        }
        // Index is on the right slope
        height = height - uint8((peakIndex - reducedIndex));
    }

    /**
     * @dev It returns the children when it is a parent node
     */
    function getChildren(uint256 index)
        public
        pure
        returns (uint256 left, uint256 right)
    {
        left = index - (uint256(1) << (heightAt(index) - 1));
        right = index - 1;
        require(left != right, "Not a parent");
    }

    /**
     * @dev It returns all peaks of the smallest merkle mountain range tree which includes
     *      the given index(size)
     */
    function getPeakIndexes(uint256 width)
        public
        pure
        returns (uint256[] memory peakIndexes)
    {
        peakIndexes = new uint256[](numOfPeaks(width));
        uint256 count;
        uint256 size;
        for (uint256 i = 255; i > 0; i--) {
            if (width & (1 << (i - 1)) != 0) {
                // peak exists
                size = size + (1 << i) - 1;
                peakIndexes[count++] = size;
            }
        }
        require(count == peakIndexes.length, "Invalid bit calculation");
    }

    function numOfPeaks(uint256 width) public pure returns (uint256 num) {
        uint256 bits = width;
        while (bits > 0) {
            if (!(bits % 2 == 0)) num++;
            bits = bits >> 1;
        }
        return num;
    }

    /**
     * @dev It returns the hash value of the node for the index.
     *      If the hash already exists it simply returns the stored value. On the other hand,
     *      it computes hashes recursively downward.
     *      Only appending an item calls this function
     */
    function _getOrCreateNode(
        uint256 index,
        bytes32[] memory hashes,
        uint256 offset
    ) private returns (bytes32) {
        require(index <= getSize(index), "Out of range");
        if (hashes[index - offset] == bytes32(0)) {
            (uint256 leftIndex, uint256 rightIndex) = getChildren(index);
            bytes32 leftHash = _getOrCreateNode(leftIndex, hashes, offset);
            bytes32 rightHash = _getOrCreateNode(rightIndex, hashes, offset);
            hashes[index - offset] = hashBranch(index, leftHash, rightHash);
        }
        return hashes[index - offset];
    }

    function isLeaf(uint256 index) public pure returns (bool) {
        return heightAt(index) == 1;
    }

    /**
     * @dev It returns a merkle proof for a leaf. Note that the index starts from 1
     */
    function getMerkleProof(
        bytes32[] memory hashes,
        uint256 width,
        uint256 index
    ) public pure returns (bytes32[] memory, bytes32[] memory) {
        require(index < hashes.length, "Out of range");
        require(isLeaf(index), "Not a leaf");

        // Find all peaks for bagging
        uint256[] memory peaks = getPeakIndexes(width);

        bytes32[] memory peakBaggingArray = new bytes32[](peaks.length);
        uint256 cursor;
        for (uint256 i = 0; i < peaks.length; i++) {
            // Collect the hash of all peaks
            peakBaggingArray[i] = hashes[peaks[i]];
            // Find the peak which includes the target index
            if (peaks[i] >= index && cursor == 0) {
                cursor = peaks[i];
            }
        }
        uint256 left;
        uint256 right;

        // Get hashes of the siblings in the mountain which the index belongs to.
        // It moves the cursor from the summit of the mountain down to the target index
        uint8 height = heightAt(cursor);
        bytes32[] memory siblings = new bytes32[](height - 1);
        while (cursor != index) {
            height--;
            (left, right) = getChildren(cursor);
            // Move the cursor down to the left side or right side
            cursor = index <= left ? left : right;
            // Remaining node is the sibling
            siblings[height - 1] = hashes[index <= left ? right : left];
        }

        return (peakBaggingArray, siblings);
    }

    // Returns the closest power of two for a number
    function closestPow2(uint256 number) public pure returns (uint256) {
        uint256 closest = 1;
        while ((closest << 1) <= number) {
            closest <<= 1;
        }
        require(closest & (closest - 1) == 0, "Not power of 2");
        return closest;
    }

    // Returns the sub-peak of a range
    function getSubpeak(bytes32[] memory data, uint256 offset)
        public
        returns (bytes32, uint256)
    {
        uint256 subpeakWidth = closestPow2(data.length - offset);
        bytes32[] memory hashes = new bytes32[](getSize(subpeakWidth) + 1);
        // Populate hashes with leafs
        for (uint256 index = 0; index < subpeakWidth; index++) {
            // Hash the data of the node
            bytes32 dataHash = sha256(abi.encodePacked(data[index + offset]));
            // Create leaf
            bytes32 leaf = hashLeaf(getSize(index + offset) + 1, dataHash);
            // Put the hashed leaf to the array
            hashes[getSize(index) + 1] = leaf;
        }
        bytes32 subpeak = _getOrCreateNode(
            getSize(subpeakWidth + offset),
            hashes,
            getSize(offset)
        );
        return (subpeak, offset + subpeakWidth);
    }

    function getAllSubpeaks(bytes32[] memory data)
        public
        returns (bytes32[] memory)
    {
        uint256 offset;
        bytes32 subpeak;
        uint256 subpeaksNumber = numOfPeaks(data.length);
        bytes32[] memory subpeaks = new bytes32[](subpeaksNumber);
        for (uint256 i = 0; i < subpeaksNumber; i++) {
            (subpeak, offset) = getSubpeak(data, offset);
            subpeaks[i] = subpeak;
        }
        return subpeaks;
    }

    // to test
    function getProofContent(
        bytes32[4][] memory proof,
        uint256 proofIndex,
        bytes32 subpeak
    )
        public
        pure
        returns (
            uint256 parentIndex,
            bytes32 leftSibling,
            bytes32 rightSibling,
            uint256 peakIndex
        )
    {
        return (
            uint256(proof[proofIndex][0]),
            leftSibling = proof[proofIndex][1] == bytes32(proofIndex)
                ? subpeak
                : proof[proofIndex][1],
            rightSibling = proof[proofIndex][2] == bytes32(proofIndex)
                ? subpeak
                : proof[proofIndex][2],
            peakIndex = uint256(proof[proofIndex][3])
        );
    }

    // to test
    function verifySubpeak(
        bytes32 subpeak,
        bytes32[4][] memory proof,
        uint256 proofIndex,
        bytes32[] memory peaks
    ) public pure returns (bool) {

        bytes32 h = subpeak;

        uint256 parentIndex;
        bytes32 leftSibling;
        bytes32 rightSibling;
        uint256 rootpeakIndex;

        do {
            (
                parentIndex,
                leftSibling,
                rightSibling,
                rootpeakIndex
            ) = getProofContent(proof, proofIndex, h);

            h = sha256(
                abi.encodePacked(parentIndex, leftSibling, rightSibling)
            );
        } while (rootpeakIndex == peaks.length);
    }
}
