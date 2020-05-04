import sys

sys.path.append("../tools/interface")
from contract_interface import ContractInterface

iface = ContractInterface(
    {"path": "./contracts/storage_vs_memory.sol", "ctor": [1]}, backend="geth"
)

size = 2 ** 16
data = [b"\x00" * 32] * (size // 32)

try:
    res = iface.call("testCallSize", function_args=[data])
    print(size, "bytes cost", res["gas"], "gas")
except Exception as e:
    print("failed for size", size, "\n", e)
finally:
    iface.end()
