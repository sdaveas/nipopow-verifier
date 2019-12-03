# TODO:
# 1. Test NipopwsContract.sol all functionalities
# 2.~Wrap the functionality around an object~
# 3. Add snapshots
# 4. Check if there is something better than just estimating the gas used
# 5. Gas usage per solidity code line
# 6. Provide thorough unit tests

import contract_interface
import eth_tester
from eth_tester import EthereumTester, PyEVMBackend

# import/export proof
def import_proof(filename='proof_new.pkl'):
    import pickle
    pickle_in = open(filename,'rb')
    proof = pickle.load(pickle_in)
    return proof

def create_proof(blocks=450000, filename='proof_new.pkl'):
    import pickle
    import create_blockchain_new as blockchain_utils
    header, headerMap, mapInterlink = blockchain_utils.create_blockchain(blocks=blocks)
    proof = blockchain_utils.make_proof(header, headerMap, mapInterlink)
    pickle_out = open(filename, 'wb')
    pickle.dump(proof, pickle_out)
    pickle_out.close()
    print("Proof was written in " + filename)
    return proof

# proof data manipulation
def str_to_bytes32(s):
    r = []
    for start in range(0,len(s),32):
        r.append(s[start:start+32])
    return r

def extract_headers_siblings(proof):
    headers = []
    hashed_headers = []
    siblings = []
    # mp stands for merkle proof
    # hs stands for headers.
    for p in proof:
        hs = p[0]
        mp = p[1]
        # Copy the header to an array of 4 bytes32
        header = str_to_bytes32(hs)
        # Encode the Merkle bits (mu) in the largest byte
        # Encode the mp size in the next largest byte
        assert 0 <= len(mp) < 256
        mu = sum(bit << i for (i,(bit,_)) in enumerate(mp[::-1]))
        assert 0 <= mu < 256
        #header[3] = chr(len(mp)) + chr(mu) + header[3][2:]
        header[3] = header[3] + ('\x00'*14).encode() + bytes([len(mp)]) + bytes([mu])
        headers.append(header)

        for (_,sibling) in mp:
            siblings.append(sibling)

    return headers, siblings

# tests
def submit_event_proof(my_contract, proof):
    headers, siblings = extract_headers_siblings(proof)

    gas = my_contract.functions.submit_event_proof(
                                          headers,
                                          siblings,
                                          headers[100]
                                      ).estimateGas()
    print("Estimated gas:", gas)
    res = my_contract.functions.submit_event_proof(
                                          headers,
                                          siblings,
                                          headers[100]
                                      ).call()
    print("Result was:", res)

def main():
    # Create a test chain
    genesis_overrides = {'gas_limit': 3141592000}
    custom_genesis_params = PyEVMBackend._generate_genesis_params(overrides=genesis_overrides)
    pyevm_backend = PyEVMBackend(genesis_parameters=custom_genesis_params)
    test_chain = EthereumTester(backend=pyevm_backend)

    # Create contract interface
    my_contract_interface = contract_interface.ContractInterface(test_chain, "./contractNipopow.sol")
    my_contract = my_contract_interface.get_contract();
    gas = my_contract.functions.test(True).estimateGas()
    print("Estemated gas:", gas)
    res = my_contract.functions.test(True).call()
    print("Result:", res)

    # submit_event_proof(my_contract, proof)

if __name__ == "__main__":
    main()
