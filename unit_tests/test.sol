pragma solidity ^0.5.13;

contract Crosschain {
    function test(bool value) public view returns(bool) {
        return !value;
    }

    function payable_test(uint required_value) public payable returns(bool) {
        if (msg.value > required_value) {
            return true;
        }
        return false;
    }
}
