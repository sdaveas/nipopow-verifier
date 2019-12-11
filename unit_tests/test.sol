pragma solidity ^0.5.13;

contract Crosschain {

    uint constant size = 1<<15;

    mapping(string => uint256) gases;

    event GasUsed(uint size, uint gas_used, string tag);

    uint256 start_gas = 0;
    function measure_gas_start(string memory tag) private {
        gases[tag] = gasleft();
    }

    function measure_gas_stop(string memory tag) private {
        emit GasUsed(size, gases[tag] - gasleft(), tag);
    }

    struct Gas {
        uint test;
        uint test_payable;
        uint test_memory;
    }

    bool dummy;
    Gas public gas;

    function measure_gas(bool value) public payable returns(uint) {
        {
            measure_gas_start('lalalal');
            test_memory(true);
            measure_gas_stop("lalalal");
        }

        // {
        //     uint256 start_gas = gasleft();
        //     bool res = test(true);
        //     dummy = dummy && res;
        //     gas.test += start_gas - gasleft();
        // }

        // {
        //     uint256 start_gas = gasleft();
        //     bool res = test_payable(true);
        //     dummy = dummy && res;
        //     gas.test_payable += start_gas - gasleft();
        // }
    }

    function test(bool value) public pure returns(bool) {
        return !value;
    }

    function test_payable(bool value) public payable returns(bool) {
        return !value;
    }

    function test_memory(bool value) public returns(bool) {

        measure_gas_start("buffer");
        bytes32[size] memory b;
        measure_gas_stop("buffer");

        measure_gas_start("loop");
        for (uint i=0; i<=1; i++) {
            b[0]=sha256(abi.encodePacked(b[i]));
        }

        if (b[0] > 0) {
            value = false;
        }
        else {
            value = true;
        }
        measure_gas_stop("loop");
        return value;
    }

    function payable_test(uint required_value) public payable returns(bool) {
        if (msg.value > required_value) {
            return true;
        }
        return false;
    }
}
