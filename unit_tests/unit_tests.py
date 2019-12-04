# run with
# $ python -m unittest unit_tests.py
import sys
sys.path.append('../')
import contract_interface
import test_contracts
import eth_tester
from eth_tester import EthereumTester, PyEVMBackend
import unittest

contract_path = './test.sol'
gas_block_limit = 3141592000
chain = test_contracts.create_chain(gas_block_limit)
ci = contract_interface.ContractInterface(chain, contract_path)

class TestSolidityVersion(unittest.TestCase):

    def test_solc_version(self):
        self.assertEqual(ci.solc_version ,'v0.5.13')

class TestContractInterface(unittest.TestCase):

    def test_contracts_instances(self):
        # Assert that the contract was compiled and deployed
        self.assertEqual(len(ci.get_contracts()), 1)

class TestContract(unittest.TestCase):

    def test_function_gas(self):
        # test setimate gas
        contract = ci.get_contract();
        gas = contract.functions.test(True).estimateGas()
        self.assertTrue(gas < gas_block_limit)
        # test call
        in_value = False
        res = contract.functions.test(in_value).call()
        # test_contract.test(bool) reverts the input
        self.assertEqual(res, not in_value)
