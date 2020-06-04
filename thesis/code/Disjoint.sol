function disjoint(
    Proof memory exist, uint256 lca
    Proof memory cont
) internal pure returns (bool) {
    for (uint256 i = lca+1; i < exist.length; i++) {
        for (uint256 j = 1; j < contest.length; j++) {
            if (exist[i] == contest[j]) { return false; }
        }
    }
    return true;
}
