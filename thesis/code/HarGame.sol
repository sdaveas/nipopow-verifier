// Storage implementation             | // Memory implementation
                                      |
pragma solidity ^0.6.0;               | pragma solidity ^0.6.0;
                                      |
contract StorageGame {                | contract MemoryGame {
                                      |
uint[] public a1;                     + bytes32 public commit;
address public holder;                | address public holder;
                                      |
function submit(uint[] memory a)      | function submit(uint[] memory a)
public                                | public
{                                     | {
  // Save array in storage            +   // Same only the hash of array
  a1 = a;                             +   commit = sha256(a);
  holder = msg.sender;                |   holder = msg.sender;
}                                     | }
                                      |
// Pass contesting array              + // Also pass original array
function contest(uint[] memory a)     + function contest(uint[] memory a1,
                                      +                  uint[] memory a2)
public                                | public
{                                     | {
                                      +   // Check commit of original array
                                      +   require(sha256(a1) == commit);
                                      +
  require(compare(a));                +   require(compare(a1, a2));
  holder = msg.sender;                |   holder = msg.sender;
}                                     | }
                                      |
// Compare with storage array         | // Compare with memory array
function compare(uint[] memory a2)    + function compare(uint[] memory a1,
                                      +                  uint[] memory a2)
internal view returns(bool)           + internal pure returns(bool)
{                                     | {
  if (a2.length < a1.length) {        |   if (a2.length < a1.length) {
    return false;                     |     return false;
  }                                   |   }
  for (uint i=0; i<a1.length; i++) {  |   for (uint i=0; i<a1.length; i++) {
    if (a2[i] < a1[i]) {              |     if (a2[i] < a1[i]) {
      return false;                   |       return false;
    }                                 |     }
  }                                   |   }
  return true;                        |   return true;
}                                     | }
                                      |
}                                     | }

