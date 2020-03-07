pragma solidity ^0.6.2;

contract Benchmark {

    // -----------------------
    mapping(string => uint256) gases;
    event GasUsed(uint gas_used, string tag);
    uint256 start_gas = 0;
    function measure_gas_start(string memory tag) private {
        gases[tag] = gasleft();
    }
    function measure_gas_stop(string memory tag) private {
        emit GasUsed(gases[tag] - gasleft(), tag);
    }
    // -----------------------

    // Store
    function benchmark_0() public returns(bool) {
        uint[100000] memory buffer;
        buffer[0] = 1;
        return buffer[0] == 1;
    }

    // Iterate
    function benchmark() public returns(bool) {
        uint sum=0;
        for (uint i=0; i<10000; i++) {
            sum+=i;
        }
        return sum < 1<<15;
    }
}
