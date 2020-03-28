import argparse
import sys
sys.path.append('../lib')
import contract_interface
from timer import Timer

def benchmark(backend):

    interface = contract_interface.ContractInterface(contract_path_list='./benchmark.sol',
                                                     backend=backend)

    callback = interface.get_contract().functions.benchmark()

    estimated_gas = callback().estimateGas()
    from_address = interface.w3.eth.accounts[0]
    result = callback().call({'from':from_address})

    interface.end()

    return result

def main():

    available_backends = contract_interface.ContractInterface.available_backends()
    parser = argparse.ArgumentParser(description='Benchmark Py-EVM, Geth and Ganache')
    parser.add_argument('--backend', choices=available_backends+['all'], required=True, type=str, help='The name of the EVM')
    parser.add_argument('--timer', action='store_true')
    args = parser.parse_args()
    backend = args.backend
    timer = args.timer

    if backend == 'all':
        for backend in available_backends:
            print('Running in ' + backend)
            if timer: t = Timer()
            res = benchmark(backend=backend)
            print(res)
    else:
        if timer: t = Timer()
        res = benchmark(backend=backend)
        print(res)

if __name__ == "__main__":
    main()
