// Storage implementation                  | // Memory implementation
                                           |
pragma solidity ^0.6.0;                    | pragma solidity ^0.6.0;
                                           |
contract StorageGame {                     | contract MemoryGame {
  uint256[] public a1;                     +   bytes32 public commit;
  address public holder;                   |   address public holder;
                                           |
  function submit(uint256[] memory a)      |   function submit(uint256[] memory a)
  public                                   |   public
  {                                        |   {
    // Save array in storage               +     // Same hash of array
    a1 = a;                                +     commit = sha256(abi.encodePacked(a));
    holder = msg.sender;                   |     holder = msg.sender;
  }                                        |   }
                                           |
  // Pass contesting array                 +   // Pass original and contesting array
  function contest(uint256[] memory a)     +   function contest(uint256[] memory a1,
                                           +                    uint256[] memory a2)
  public                                   |   public
  {                                        |   {
                                           +     // Check commitment of original array
                                           +     require(sha256(abi.encodePacked(a1)) ==
                                           +             commit);
    require(compare(a));                   +     require(compare(a1, a2));
    holder = msg.sender;                   |     holder = msg.sender;
  }                                        |   }
                                           |
  // Compare with storage array            |   // Compare with memory array
  function compare(uint256[] memory a2)    +   function compare(uint256[] memory a1,
                                           +                    uint256[] memory a2)
  internal view returns(bool)              +   internal pure returns(bool)
  {                                        |   {
    if (a2.length < a1.length) {           |     if (a2.length < a1.length) {
      return false;                        |       return false;
    }                                      |     }
    for (uint i = 0; i < a1.length; i++) { |     for (uint i = 0; i < a1.length; i++) {
      if (a2[i] < a1[i]) {                 |       if (a2[i] < a1[i]) {
        return false;                      |         return false;
      }                                    |       }
    }                                      |     }
    return true;                           |     return true;
  }                                        |   }
}                                          | }

