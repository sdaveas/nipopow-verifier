"""
run with
$ pytest -v -s test_fail_on_require
"""

import sys

sys.path.append("../tools/interface/")
import contract_interface

import pytest
import web3
from config import errors, extract_message_from_error, genesis
from eth_tester.exceptions import TransactionNotFound


def test_fail_pyevm():
    """
    Test failure at require in smart contract for Py_EVM
    """

    contract_path = "./contracts/fail_on_require.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="Py-EVM", constructor_arguments=genesis
    )
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as ex:
        my_contract.functions.fail().call({"from": from_address})
        tx_hash = my_contract.functions.fail().transact({"from": from_address})
        interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    assert ex.match("test failed successfully")


def test_fail_geth():
    """
    Test failure at require in smart contract for geth
    """

    contract_path = "./contracts/fail_on_require.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="geth", constructor_arguments=genesis
    )
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as ex:
        my_contract.functions.fail().call({"from": from_address})
        tx_hash = my_contract.functions.fail().transact({"from": from_address})
        interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    assert ex.match("test failed successfully")


def test_fail_ganache():
    """
    Test failure at require in smart contract for ganache
    """

    contract_path = "./contracts/fail_on_require.sol"
    interface = contract_interface.ContractInterface(
        contract_path, backend="ganache", constructor_arguments=genesis
    )

    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as ex:
        my_contract.functions.fail().call({"from": from_address})
        tx_hash = my_contract.functions.fail().transact({"from": from_address})
        interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    assert extract_message_from_error(ex) == "test failed successfully"
