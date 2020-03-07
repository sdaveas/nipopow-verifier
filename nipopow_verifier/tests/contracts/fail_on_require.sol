pragma solidity ^0.6.2;

contract fail_of_require
{
    function fail() public pure returns (bool)
    {
        require(0==1, "test failed successfully");
    }
}

