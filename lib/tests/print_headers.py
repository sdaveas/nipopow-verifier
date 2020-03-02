import sys
sys.path.append('../')

from create_blockchain_new import create_blockchain, bits_to_target, list_flatten, hash_interlink, make_proof, CBlockHeaderPopow
from create_proof import export_proof
from bitcoin.core import uint256_from_str

import argparse

def print_headers(headers_map):
    print('\nHeaders')
    for h in list(headers_map.keys()):
        k = h
        v = headers_map[k]
        print('header hash:\t\t', v.GetHash().hex())
        print()
        print('prev block hash:\t', v.hashPrevBlock.hex())
        print('merkle tree root hash:\t', v.hashMerkleRoot.hex())
        print('interlink hash:\t\t', v.hashInterlink.hex())
        print('level\t\t\t', v.compute_level())
        print(32*'-')

def print_tuple(t):
    if t == ():
        return
    for element in t:
        if type(element) == tuple:
            print_tuple(element)
        else:
            print('Interlink:', element.hex()[:6])

def print_interlinks(headers_map, interlink_map):
    print('\nInterlinks')
    for i in interlink_map.keys():
        print('Key:', i.hex()[:6], '| Level:', int(headers_map[i].compute_level()))
        print_tuple(interlink_map[i])
        print('+'*32)

def print_proof_element(element):
    print('Prev header:\t',    element[  0: 64])
    # print('Version:\t',        element[ 64: 66])
    # print('Something:\t',      element[ 66: 72])
    print('Interlink hash:\t', element[ 72:136])
    print('Merkle root:\t',    element[136:200])
    # print('Time:\t\t',         element[200:208])
    # print('Bits:\t\t',         element[208:216])
    # print('Nonce:\t\t',        element[216:224])

def print_proof(proof, headers_map):
    print('\nProof')
    for p in proof:
        header_hash, interlink_flatten = p
        print_proof_element(header_hash.hex())
        print()
    print('Chain length:', len(headers_map))
    print('Proof length:', len(proof))

def main():
    parser=argparse.ArgumentParser(description='Prints the contents of a NiPoPoW')
    parser.add_argument('--blocks', required=True, type=int, help='Number of blocks')
    args=parser.parse_args()
    blocks=args.blocks

    header, headers_map, interlink_map = create_blockchain(blocks=blocks)
    print_headers(headers_map)
    print_interlinks(headers_map, interlink_map)

    proof = make_proof(header, headers_map, interlink_map)
    proof.pop(-1)
    print_proof(proof, headers_map)
    export_proof(proof, 'messed_up_proof.pkl')

if __name__ == '__main__':
    main()
