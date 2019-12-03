# Inspired by https://github.com/pryce-turner/web3_python_tutorials

import solcx
from solcx import set_solc_version, get_solc_version, compile_source, compile_files

import web3
from web3 import Web3, EthereumTesterProvider, contract

# Provide an interface to facilitate smart contracts compilation and deployment
class ContractInterface:
    def __init__(
            self,
            chain,
            contract_path_list,
            solc_version = 'v0.5.13',
            contract_instances = []
            ):

        self.solc_version = solc_version
        self.contract_path_list = contract_path_list
        self.w3 = Web3(EthereumTesterProvider(chain))
        self.contract_instances = []
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
        self.xprint("Compiling with solidity " +
                         str(solcx.get_solc_version()))
        self.compiled_contracts = compile_files(self.contract_path_list)
        print("Compiled contract(s): ", len(self.compiled_contracts))

    def deploy_contracts(self):
        deployed_contracts = []
        for compiled_contract in self.compiled_contracts.items():
            self.deployed_contract = self.w3.eth.contract(
                                    abi=compiled_contract[1]['abi'],
                                    bytecode = compiled_contract[1]['bin']
                                )
            my_contract = self.deployed_contract.constructor()

            gas_estimate = my_contract.estimateGas()
            tx_hash = my_contract.transact()

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
