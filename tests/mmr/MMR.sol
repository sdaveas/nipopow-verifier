pragma solidity ^0.6.0;


contract MMR {
    event debug(string tag, uint256 value);

    struct Tree {
        bytes32 root;
    }

    bytes32 root;

    function testMMR(bytes32[] memory data) public returns (bytes32) {

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
            peaks[i] = _getOrCreateNode(peakIndexes[i], hashes);
        }
        emit debug("> Calling root with", data.length);
        root = peakBagging(data.length, peaks);

        return root;
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
    function _getOrCreateNode(uint256 index, bytes32[] memory hashes)
        private
        returns (bytes32)
    {
        require(index <= getSize(index), "Out of range");

        if (hashes[index] == bytes32(0)) {
            (uint256 leftIndex, uint256 rightIndex) = getChildren(index);
            bytes32 leftHash = _getOrCreateNode(leftIndex, hashes);
            bytes32 rightHash = _getOrCreateNode(rightIndex, hashes);
            hashes[index] = hashBranch(index, leftHash, rightHash);
        }
        return hashes[index];
    }
}
