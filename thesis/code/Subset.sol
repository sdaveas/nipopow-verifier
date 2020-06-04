function subset(
    Proof memory exist, uint existLca,
    Proof memory cont, uint contLca
) internal pure returns(bool)
{
    uint256 j = contLca;
    for (uint256 i = existLca; i < exist.length; i++) {
        while (exist[i] != cont[j]) {
            if (++j >= contLca) { return false; }
        }
    }
    return true;
}
