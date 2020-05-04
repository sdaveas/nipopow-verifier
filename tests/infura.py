import sys

sys.path.append("../tools/interface/")
from contract_interface import ContractInterface
from timer import Timer

sys.path.append("../tools/proof/")
from proof import Proof
from create_proof import ProofTool

from contract_api import (
    submit_event_proof,
    submit_contesting_proof,
    make_interface,
)
from config import extract_message_from_error, genesis, k, m

from web3 import Web3, HTTPProvider

w3 = Web3(
    HTTPProvider(
        "https://mainnet.infura.io/v3/8f2b15b73f394809bf93b7b6552da3cf"
        # "https://ropsten.infura.io/v3/8f2b15b73f394809bf93b7b6552da3cf"
        # "https://kovan.infura.io/v3/8f2b15b73f394809bf93b7b6552da3cf"
    )
)
privateKey = "c9d1b917273a40c67e9dfd46f55808e980b751f0d3e32c7355eb22af7946773c"

abi = open("./Crosschain.abi").read()
bytecode = open("./Crosschain.bin").read()

contract_ = w3.eth.contract(
    abi=abi,
    # bytecode=bytecode
    address="0xE374199fB157f798582533488F075C27c4E1f7A1",  # Ropsten
    # address = "0xA8E9ef556eA23d440e2c40931D0aAf2fc1613a6a"      # Kovan
)

acct = w3.eth.account.privateKeyToAccount(privateKey)

pt = ProofTool()
proof = Proof()
proof.set(pt.fetch_proof(500000))  # m = 8 -> 37184
headers_size = len(proof.headers) * 4 * 32
siblings_size = len(proof.siblings) * 32
print(headers_size, siblings_size, headers_size + siblings_size)

# construct_txn = contract_.constructor(genesis, k, m).buildTransaction({
#     'from': acct.address,
#     'nonce': w3.eth.getTransactionCount(acct.address),
#     'gas': 3000000,
#     'gasPrice': w3.toWei('21', 'gwei')})

function = contract_.functions.submitEventProof(
    proof.headers, proof.siblings, 0
)

function_txn = function.buildTransaction(
    {
        "value": pow(10, 17),
        "gas": 8000000,
        "gasPrice": 11000000000,
        "nonce": w3.eth.getTransactionCount(acct.address),
    }
)

# signed = acct.signTransaction(construct_txn)
signed = acct.signTransaction(function_txn)
tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
print("waiting confirmation...")
tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
print("OK")
print(tx_receipt)
contract_address = tx_receipt["contractAddress"]
print(contract_address)
