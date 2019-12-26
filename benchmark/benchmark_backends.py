import argparse
import sys
sys.path.append('../')
import contract_interface

def benchmark(backend):

    interface = contract_interface.ContractInterface(contract_path_list='./benchmark.sol',
                                                     backend=backend)

    callback = interface.get_contract().functions.benchmark()

    estimated_gas = callback().estimateGas()
    from_address = interface.w3.eth.accounts[0]
    result = callback().call({'from':from_address})

    return result

def main():

    parser = argparse.ArgumentParser(description='Benchmark Py-EVM and Ganache')
    parser.add_argument('--backend', choices=['Py-EVM', 'ganache'], required=True, type=str, help='The name of the EVM')
    args = parser.parse_args()
    backend = args.backend

    res = benchmark(backend=backend)
    print(res)

if __name__ == "__main__":
    main()
