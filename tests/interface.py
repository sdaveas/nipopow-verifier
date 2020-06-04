from tqdm import tqdm
import sys

sys.path.append("../../tools/interface")
from contract_interface import ContractInterface

results = []

size = 500

for i in tqdm(range(0, size + 1, size)):
    data = [b"\xff"] * i

    iface = ContractInterface(
        {"path": "./hash_and_resubmit.sol", "ctor": []}, backend="geth"
    )
    submitStorage_gas = iface.call("submitStorage", function_args=[data])[
        "gas"
    ]
    contestStorage_gas = iface.call("contestStorage", function_args=[data])[
        "gas"
    ]
    iface.end()

    iface = ContractInterface(
        {"path": "./hash_and_resubmit.sol", "ctor": []}, backend="geth"
    )
    submitMemory_gas = iface.call("submitMemory", function_args=[data])["gas"]
    contestMemory_gas = iface.call(
        "contestMemory", function_args=[data, data]
    )["gas"]
    iface.end()

    results.append(
        str(
            str(i)
            + ","
            + str(submitStorage_gas)
            + ","
            + str(contestStorage_gas)
            + ","
            + str(submitMemory_gas)
            + ","
            + str(contestMemory_gas)
        )
    )
for r in results:
    print(r)
