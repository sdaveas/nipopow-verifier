# Inspired by https://github.com/pryce-turner/web3_python_tutorials
import solcx
from solcx import set_solc_version, get_solc_version, compile_source, compile_files, link_code

import web3
from web3 import Web3, EthereumTesterProvider, contract

import eth_tester
from eth_tester import EthereumTester, PyEVMBackend


class ContractInterface:

    backends_to_inits = {'Py-EVM': None, 'ganache': None, 'geth': None}

    def __init__(
            self,
            contract={},
            libraries=[],
            solc_version='v0.6.4',
            backend='ganache',
            genesis_overrides={'gas_limit':3141592000},
            precompiled_contract=None,
            profiler=None
            ):

        self.solc_version=solc_version
        self.contract=contract
        self.backend=backend
        self.contract_instances = []

        self.genesis_overrides=genesis_overrides

        self.backends_to_inits['Py-EVM'] = self.init_backend_pyevm
        self.backends_to_inits['ganache'] = self.init_backend_ganache
        self.backends_to_inits['geth'] = self.init_backend_geth

        self.w3 = Web3()
        self.init_backend()
        self.setup_compiler()

        self.libraries = {}

        compiled_libraries = self.compile(libraries)
        self.deploy(compiled_libraries)

        path = contract["path"]
        if precompiled_contract is not None:
            compiled_contract = self.create_from_compiled(path, precompiled_contract)
        else:
            compiled_contract = self.compile(path)
        self.contract_instances = self.deploy(compiled_contract, contract["ctor"])

        self.profiler = profiler

    def create_from_compiled(self, contract_path, precompiled_contract):
        return [[ contract_path,
                {
                  'abi' : open(precompiled_contract['abi']).read(),
                  'bin' : open(precompiled_contract['bin']).read()
                }]]


    def setup_compiler(self):
        try:
            solcx.set_solc_version(self.solc_version)
        except Exception as e:
            print("Solidity version " + self.solc_version +
                  " does not exist in your system")
            print("Installing now ...")
            solcx.install_solc(self.solc_version)
            print("... OK")
        set_solc_version(self.solc_version)

    def link(self, contract_bin, libraries):
        for library_name in libraries.keys():
            library_address = libraries[library_name]
            contract_bin = link_code( contract_bin, {library_name: library_address})
        return contract_bin

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
        # print(self.backend)
        if self.backend in list(self.backends_to_inits.keys()):
            self.backends_to_inits[self.backend]()
        else:
            print("Error: unknown backend '"+self.backend+"'). Available backends:")
            print(self.available_backends())
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

    def get_paths(self, contracts):
        paths = []
        for c in contracts:
            paths.append(c.keys())
        return paths

    def find_in_compiled(self, target, compiled):
        for i, c in enumerate(compiled.keys()):
            if target in c:
                return i

    def compile(self, contracts):

        compiled_contracts = []
        if not isinstance(contracts, list):
            contracts = [contracts]
        for c in contracts:
            compiled = compile_files([c], optimize=True)
            index = self.find_in_compiled(c, compiled)
            key = list(compiled.keys())[index]
            value = compiled[key]
            compiled_contracts.append([key, value])
        return compiled_contracts


    @staticmethod
    def create_sourcemap(contract_path, sourcemap_path):
        import subprocess
        subprocess.Popen([
            'solc',
            '--combined-json',
            'srcmap-runtime',
            '--overwrite',
            contract_path,
            '-o',
            '.'
        ])

    # Salute to https://github.com/yushih/solidity-gas-profiler
    def run_gas_profiler(self, profiler, tx_hash, filename="gas_profile.txt"):

        if self.backend != 'geth':
            return

        try:
            executable = 'node'
            rpc = 'http://127.0.0.1:8545'
            contract_path = self.contract["path"]
            sourcemap_path = 'combined.json'
            self.create_sourcemap(contract_path, sourcemap_path)
            output_file = filename

            import subprocess
            process = subprocess.Popen([
                executable,
                profiler,
                rpc,
                tx_hash.hex(),
                contract_path,
                sourcemap_path,
                ],
                stdout = subprocess.PIPE)
            (process_output,  error) = process.communicate()
            file = open(output_file, "+wb")
            file.write(process_output)
            file.close()

            print('Gas profing saved to', output_file)
        except Exception as e:
            print('Unable to run profiles', e)

    def deploy(self, compiled_contracts, constructor_arguments=[]):
        contract_instances = []
        for compiled_contract in compiled_contracts:
            linked_bytecode = self.link(compiled_contract[1]['bin'], self.libraries)
            deployed_contract = self.w3.eth.contract(
                                    abi=compiled_contract[1]['abi'],
                                    bytecode=linked_bytecode,
                                )
            my_contract = deployed_contract.constructor(*constructor_arguments)
            tx_hash = my_contract.transact({'from': self.w3.eth.accounts[0]})
            tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
            contract_address = tx_receipt['contractAddress']
            self.libraries[compiled_contract[0]] = contract_address

            contract_instance = self.w3.eth.contract(
                                    abi = compiled_contract[1]['abi'],
                                    address = contract_address
                                )
            contract_instances.append(contract_instance)
        return contract_instances

    def get_contracts(self):
        return self.contract_instances

    def get_contract(self, index=0):
        return self.contract_instances[index]

    @staticmethod
    def get_events(contract, receipt, event_name):
        """
        Prints events with name 'event_name'
        """

        try:
            my_event = getattr(contract.events, event_name)
        except Exception:
            return []

        events = my_event().processReceipt(receipt)

        extracted_events = []
        if len(events) > 0:
            for e in events:
                log = dict(e)["args"]
                if isinstance(log["value"], bytes):
                    value = log["value"].hex()
                else:
                    value = log["value"]
                extracted_events.append([log["tag"], value])
        return extracted_events

    @staticmethod
    def timestamp():
        """
        Returns the current date time skipping milliseconds
        2020-04-16T12:11:45
        """
        from datetime import datetime
        return datetime.today().isoformat().split('.')[0]

    def call(self, function_name, function_args=[], event_name='debug', value=0, from_address=None):
        """
        Runs the output, gas used and events emitted for a function
        """
        if from_address is None:
            from_address = self.w3.eth.accounts[0]

        contract = self.get_contract()
        function = contract.get_function_by_name(function_name)(*function_args)
        res = function.call({"from": from_address, "value": value})
        tx_hash = function.transact({"from": from_address, "value": value})
        receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        events = self.get_events(contract, receipt, event_name)

        if self.profiler is not None:
            self.run_gas_profiler(self.profiler, tx_hash, function_name + '_' + self.timestamp())

        return {"result": res, "gas": receipt["gasUsed"], 'events': events}
