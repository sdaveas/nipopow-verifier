import ethereum.config as config
from ethereum.tools import tester
from ethereum import utils
from ethereum.tools._solidity import (
    get_solidity,
    compile_file,
    solidity_get_contract_data
    )
SOLIDITY_AVAILABLE = get_solidity() is not None

from ethereum import slogging
#slogging.configure(':INFO,eth.vm:INFO')
#slogging.configure(':DEBUG')

# Create the simulated blockchain
tester.Chain().chain.config['BLOCK_GAS_LIMIT'] = 31415920000
tester.Chain().chain.config['START_GAS_LIMIT'] = 31415920000

s = tester.Chain()
s.mine()

benchmark_path = './benchmark.sol'
benchmark_name = 'Benchmark'
benchmark_compiled = compile_file(benchmark_path)

benchmark_data = solidity_get_contract_data(
        benchmark_compiled,
        benchmark_path,
        benchmark_name,)

benchmark_address = s.contract(benchmark_data['bin'], language='evm')

benchmark_abi = tester.ABIContract(
    s,
    benchmark_data['abi'],
    benchmark_address)

# Take a snapshot before trying out test cases
s.mine()
base = s.snapshot()

def initialize_test():
    try:
        s.revert(base)
    except AssertionError as e:
        if 'block boundaries' not in str(e):
            raise

def benchmark():

    # initialize_test()

    g = s.head_state.gas_used

    success = benchmark_abi.benchmark(sender = tester.k1, startgas=3141592000)
    print(success)

    print 'Gas used:', s.head_state.gas_used - g

benchmark()
