# run with
# $ python -m unittest unit_tests.py
import sys
sys.path.append('../')
import contract_interface
import test_contracts
import unittest

gas_block_limit = 3141592000
test_contract_path = './test.sol'
nipopow_contract_path = '../contractNipopow.sol'

print(gas_block_limit)

test_chain = test_contracts.create_chain(gas_block_limit)
test_ci = contract_interface.ContractInterface(test_chain, test_contract_path)

nipopow_chain = test_contracts.create_chain(gas_block_limit)
nipopow_ci = contract_interface.ContractInterface(nipopow_chain, nipopow_contract_path)

class TestSolidityVersion(unittest.TestCase):

    def test_solc_version(self):
        self.assertEqual(test_ci.solc_version ,'v0.5.13')

class TestContractInterface(unittest.TestCase):

    def test_contracts_instances(self):
        self.assertEqual(len(test_ci.get_contracts()), 1)

class TestContract(unittest.TestCase):

    def test_function_estemated_gas(self):
        contract = test_ci.get_contract();
        gas = contract.functions.test(True).estimateGas()
        self.assertTrue(gas < gas_block_limit)

    def test_function_used_gas(self):
        contract = test_ci.get_contract();
        tx = contract.functions.test(True).transact()
        receipt = test_ci.w3.eth.getTransactionReceipt(tx)
        gas_used = receipt['gasUsed']
        self.assertTrue(gas_used < gas_block_limit)

    def test_function_call(self):
        contract = test_ci.get_contract();
        in_value = False
        res = contract.functions.test(in_value).call()
        self.assertTrue(not in_value)

    def test_payable_function(self):
        contract = test_ci.get_contract();
        res = contract.functions.payable_test(4).call({'value':5})
        self.assertTrue(res)
        res = contract.functions.payable_test(6).call({'value':5})
        self.assertFalse(res)
        print(res)


class TestSubmitProof(unittest.TestCase):

    def test_submit_proof(self):
        contract = nipopow_ci.get_contract();
        proof = test_contracts.create_proof(blocks=45000)
        res = test_contracts.submit_event_proof(contract, proof)
        self.assertTrue(res)

