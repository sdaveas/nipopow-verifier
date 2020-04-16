"""
run with
$ pytest -v -s test_fail_on_require
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface

import pytest
from config import extract_message_from_error


def make_interface(backend):
    return contract_interface.ContractInterface(
        contract={"path": "./contracts/fail_on_require.sol", "ctor": []},
        backend=backend,
    )


def test_fail_geth():
    """
    Test failure at require in smart contract for geth
    """

    with pytest.raises(Exception) as ex:
        make_interface("geth").call("fail")
    assert ex.match("test failed successfully")


def test_fail_ganache():
    """
    Test failure at require in smart contract for ganache
    """

    with pytest.raises(Exception) as ex:
        make_interface("ganache").call("fail")
    assert extract_message_from_error(ex) == "test failed successfully"
