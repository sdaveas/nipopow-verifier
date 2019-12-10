pragma solidity ^0.5.13;

contract Crosschain {

    struct Gas {
        uint test;
        uint test_payable;
        uint test_memory;
    }

    uint constant size = 60000;
    bool dummy;
    Gas public gas;

    function measure_gas() public payable returns(uint) {
        uint256 start_gas = gasleft();
        bool res = test_memory(true);
        dummy = res;
        gas.test_memory += start_gas - gasleft();

        start_gas = gasleft();
        res = test(true);
        dummy = dummy && res;
        gas.test += start_gas - gasleft();

        start_gas = gasleft();
        res = test_payable(true);
        dummy = dummy && res;
        gas.test_payable += start_gas - gasleft();
    }

    function test(bool value) public view returns(bool) {
        return !value;
    }

    function test_payable(bool value) public payable returns(bool) {
        return !value;
    }

    function test_memory(bool value) public returns(bool) {

        bytes32[size] memory b;
        for (uint i=0; i<=1; i++) {
            b[0]=sha256(abi.encodePacked(b[i]));
        }

        if (b[0] > 0) {
            value = false;
        }
        else {
            value = true;
        }
        return value;
    }

    function payable_test(uint required_value) public payable returns(bool) {
        if (msg.value > required_value) {
            return true;
        }
        return false;
    }
}
