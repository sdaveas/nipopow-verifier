function disjoint(
    Proof memory exist, uint256 lca
    Proof memory cont
) internal pure returns (bool) {
    for (uint256 i = 0; i < lca; i++) {
        for (uint256 j = 0; j < contest.length - 1; j++) {
            if (exist[i] == contest[j]) { return false; }
        }
    }
    return true;
}
