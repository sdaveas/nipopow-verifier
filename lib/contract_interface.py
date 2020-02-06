# Inspired by https://github.com/pryce-turner/web3_python_tutorials
import solcx
from solcx import set_solc_version, get_solc_version, compile_source, compile_files

import web3
from web3 import Web3, EthereumTesterProvider, contract

import eth_tester
from eth_tester import EthereumTester, PyEVMBackend

class ContractInterface:

    backends_to_inits = {'Py-EVM': None, 'ganache': None, 'geth': None}

    def __init__(
            self,
            contract_path_list=[],
            solc_version='v0.5.13',
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

        self.genesis_overrides=genesis_overrides

        self.backends_to_inits['Py-EVM']  = self.init_backend_pyevm
        self.backends_to_inits['ganache'] = self.init_backend_ganache
        self.backends_to_inits['geth']    = self.init_backend_geth

        self.init_backend()

        self.compile_contracts()
        self.deploy_contracts()

    def end(self):
        # Stop mining geth
        if self.backend == 'geth':
            self.w3.geth.miner.stop()

    @staticmethod
    def available_backends():
        return list(ContractInterface.backends_to_inits.keys())

    def init_backend(self):
        # TODO: make backend specification more formal
        # backend -> 'Py-EVM', override_params -> {'gas_limit': block_gas_limit}
        # backend -> 'ganache'
        # backend -> 'geth'
        if self.backend in list(self.backends_to_inits.keys()):
            self.backends_to_inits[self.backend]()
        else:
            print("Error: unknown backend '"+self.backend+"'). Available backends:")
            print(available_backends)
            exit()

    def init_backend_pyevm(self):
        custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=self.genesis_overrides)
        py_backend = PyEVMBackend(genesis_parameters=custom_genesis_params)
        self.w3 = Web3(EthereumTesterProvider(EthereumTester(py_backend)))

    def init_backend_ganache(self):
        url = 'http://127.0.0.1'
        port = '7545'
        self.w3 = Web3(Web3.HTTPProvider(url+":"+port, request_kwargs = {'timeout':60}))
        if not self.w3.isConnected():
            print('Cannot connect to '+url+':'+port+'. Is '+self.backend+' up?')
            raise RuntimeError('Cannot connect to '+url+':'+port+'. Is '+self.backend+' up? If not, run:\n> $ node --max-old-space-size=4000 /bin/ganache-cli -p 7545 -g 1 -l 0x6691b700')

    def init_backend_geth(self):
        url = 'http://127.0.0.1'
        port = '8545'
        self.w3 = Web3(Web3.HTTPProvider(url+':'+port))
        if not self.w3.isConnected():
            raise RuntimeError('Cannot connect to '+url+':'+port+'. Is '+self.backend+' up?')
        self.w3.geth.miner.start(4)

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
            # print("Deployed {0} at: {1} using {2} gas.".format(
            #     compiled_contract[0],
            #     contract_address,
            #     tx_receipt['cumulativeGasUsed']
            #     ))

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
