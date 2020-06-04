"""
run with
$ pytest -v -s test_storage_vs_memory.py
"""

"""
output:

"""

from pprint import pprint
from tqdm import tqdm
import sys

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface


def run(size):
    """
    Deploys the contract and runs with_storage and with_memory functions
    printing the gas usage
    """

    interface = ContractInterface(
        {"path": "./contracts/storage_vs_memory.sol", "ctor": [size]},
        backend="ganache",
    )
    storage_gas = interface.call("with_storage")["gas"]
    memory_gas = interface.call("with_memory")["gas"]
    interface.end()
    return storage_gas, memory_gas


def main():
    _from = 1
    _to = 100
    gases = []
    for i in tqdm(range(_from, _to + 1)):
        (storage, memory) = run(i)
        gases.append([i, storage, memory])

    for g in gases:
        print(g[0], "\t", g[1], "\t", g[2])


main()
