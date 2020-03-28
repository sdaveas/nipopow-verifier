pragma solidity ^0.6.0;

contract MMR {

    event debug(string tag, uint256 value);

    struct Tree {
        bytes32 root;
        uint256 size;
        mapping(uint256 => bytes32) hashes;
        mapping(bytes32 => bytes) data;
    }

    Tree tree;

    function testMMR(bytes32[] memory data)
        public
        returns (bytes32)
    {
        emit debug("Inside with", data.length);

        for (uint256 i = 0; i < data.length; i++) {
             append(data[i], i);
        }
        return tree.root;
    }

    /**
     * @dev This only stores the hashed value of the leaf.
     *      If you need to retrieve the detail data later, use a map to store them.
     */
    function append(bytes32 data, uint256 index) public {
        // Hash the leaf node first
        bytes32 dataHash = sha256(abi.encodePacked(data));
        bytes32 leaf = hashLeaf(tree.size + 1, dataHash);
        // Put the hashed leaf to the map
        tree.hashes[tree.size + 1] = leaf;
        // Find peaks for the enlarged tree
        uint256[] memory peakIndexes = getPeakIndexes(index+1);
        // The right most peak's value is the new size of the updated tree
        tree.size = getSize(index+1);
        // Starting from the left-most peak, get all peak hashes using _getOrCreateNode() function.
//        bytes32[] memory peaks = new bytes32[](peakIndexes.length);
//        for (uint256 i = 0; i < peakIndexes.length; i++) {
//            peaks[i] = _getOrCreateNode(peakIndexes[i]);
//        }
    }

    function getPeaks() public view returns (bytes32[] memory peaks) {
        // Find peaks for the enlarged tree
        uint256[] memory peakNodeIndexes = getPeakIndexes(tree.width);
        // Starting from the left-most peak, get all peak hashes using _getOrCreateNode() function.
        peaks = new bytes32[](peakNodeIndexes.length);
        for (uint256 i = 0; i < peakNodeIndexes.length; i++) {
            peaks[i] = tree.hashes[peakNodeIndexes[i]];
        }
        return peaks;
        // Create the root hash and update the tree
        tree.root = peakBagging(index+1, peaks);
    }

    function getLeafIndex(uint256 width) public pure returns (uint256) {
        if (width % 2 == 1) {
            return getSize(width);
        } else {
            return getSize(width - 1) + 1;
        }
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
            if (bits % 2 == 1) num++;
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
    function _getOrCreateNode(uint256 index) private returns (bytes32) {
        require(index <= tree.size, "Out of range");
        if (tree.hashes[index] == bytes32(0)) {
            (uint256 leftIndex, uint256 rightIndex) = getChildren(index);
            bytes32 leftHash = _getOrCreateNode(leftIndex);
            bytes32 rightHash = _getOrCreateNode(rightIndex);
            tree.hashes[index] = hashBranch(index, leftHash, rightHash);
        }
        return tree.hashes[index];
    }
}
