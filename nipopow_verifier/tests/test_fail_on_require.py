#########################
# run with
# $ pytest -v -s test_fail_on_require
#########################

import sys
sys.path.append('../tools/interface/')
import contract_interface

import pytest
import web3
import errors
from eth_tester.exceptions import TransactionNotFound

@pytest.fixture(scope='session', autouse=True)
def finish_session(request):
    yield
    # you can access the session from the injected 'request':
    session = request.session

def test_fail_pyevm():

    contract_path = './contracts/fail_on_require.sol'
    interface = contract_interface.ContractInterface(contract_path, backend='Py-EVM')
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as e:
        res = my_contract.functions.fail().call({'from':from_address})
        tx_hash = my_contract.functions.fail().transact({'from':from_address})
        receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
        print('---------', res)
    interface.end()
    print(e)

def test_fail_geth():

    contract_path = './contracts/fail_on_require.sol'
    interface = contract_interface.ContractInterface(contract_path, backend='geth')
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as e:
        res = my_contract.functions.fail().call({'from':from_address})
        tx_hash = my_contract.functions.fail().transact({'from':from_address})
        receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    print(e)

def test_fail_ganache():

    contract_path = './contracts/fail_on_require.sol'
    interface = contract_interface.ContractInterface(contract_path, backend='ganache')
    my_contract = interface.get_contract()
    from_address = interface.w3.eth.accounts[0]

    with pytest.raises(Exception) as e:
        res = my_contract.functions.fail().call({'from':from_address})
        tx_hash = my_contract.functions.fail().transact({'from':from_address})
        receipt = interface.w3.eth.waitForTransactionReceipt(tx_hash)
    interface.end()
    assert errors.extract_message_from_error(e) == 'test failed successfully'
