# Inspired by https://github.com/pryce-turner/web3_python_tutorials
import sys

import solcx
from solcx import set_solc_version, get_solc_version, compile_source, compile_files

import web3
from web3 import Web3, EthereumTesterProvider, contract

import eth_tester
from eth_tester import EthereumTester, PyEVMBackend

# Provide an interface to facilitate smart contracts compilation and deployment
class ContractInterface:
    def __init__(
            self,
            contract_path_list=[],
            solc_version='v0.5.4',
            contract_instances=[],
            backend='ganache',
            genesis_overrides={'gas_limit':3141592000},
            precompiled_contract={},
            ):

        self.solc_version=solc_version
        self.precompiled_contract=precompiled_contract
        self.contract_path_list=contract_path_list
        self.backend=backend
        self.compiled_contracts = {}
        self.contract_instances = []

        # backend -> 'ganache'
        # backend -> 'Py-EVM', override_params -> {'gas_limit': block_gas_limit}
        if backend=='Py-EVM':
            custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
            py_backend = PyEVMBackend(genesis_parameters=custom_genesis_params)
            self.w3 = Web3(EthereumTesterProvider(EthereumTester(py_backend)))
        elif backend=='ganache':
            self.w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))
        elif backend=='geth':
            self.w3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:8543"))
            # self.w3 = Web3(Web3.IPCProvider('~/.ethereum/geth.ipc'))
        else:
            print("Error: unknown backend '"+backend+"'). Available backends:")
            print(" 1. ganache\n 2. Py-EVM")
            exit()

        self.compile_contracts()
        self.deploy_contracts()

    @staticmethod
    def xprint(message, fill='='):
        message_length = len(message)
        print(fill * message_length)
        print(message)
        print(fill * message_length)

    def compile_contracts(self):
        try:
            solcx.set_solc_version(self.solc_version)
        except:
            print("Solidity version " + self.solc_version +
                  " does not exist in your system")
            print("Installing now ...")
            solcx.install_solc(self.solc_version)
            print("... OK")
        set_solc_version(self.solc_version)

        if not isinstance(self.contract_path_list, list):
            self.contract_path_list = [self.contract_path_list]
        # self.xprint("Compiling with solidity " +
        #                  str(solcx.get_solc_version()))

        if len(self.precompiled_contract) == 0:
            self.compiled_contracts = compile_files(self.contract_path_list)
        else:
            self.compiled_contracts = {
                    self.contract_path_list[0] :
                    {
                      'abi' : open(self.precompiled_contract['abi']).read(),
                      'bin' : open(self.precompiled_contract['bin']).read()
                    }}

        # print("Compiled contract(s): ", len(self.compiled_contracts))

    def deploy_contracts(self):
        deployed_contracts = []

        for compiled_contract in self.compiled_contracts.items():
            self.deployed_contract = self.w3.eth.contract(
                                    abi=compiled_contract[1]['abi'],
                                    bytecode=compiled_contract[1]['bin'],
                                    # Provide compiled contract abi and bytecode
                                    # abi=open('./Crosschain.abi').read(),
                                    # bytecode=open('./Crosschain.bin').read()
                                )
            my_contract = self.deployed_contract.constructor()

            gas_estimate = my_contract.estimateGas()
            tx_hash = my_contract.transact({'from': self.w3.eth.accounts[0]})

            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            contract_address = tx_receipt['contractAddress']
            print("Deployed {0} at: {1} using {2} gas.".format(
                compiled_contract[0],
                contract_address,
                tx_receipt['cumulativeGasUsed']
                ))

            deployed_contracts.append(self.deployed_contract)

            contract_instance = self.w3.eth.contract(
                                    abi = compiled_contract[1]['abi'],
                                    address = contract_address
                                )
            self.contract_instances.append(contract_instance)

    def get_contracts(self):
        return self.contract_instances

    def get_contract(self, index=0):
        return self.contract_instances[index]
