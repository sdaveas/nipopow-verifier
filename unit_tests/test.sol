pragma solidity ^0.5.13;

contract Crosschain {
  function test(bool value) public view returns(bool) {
    return !value;
  }
}
