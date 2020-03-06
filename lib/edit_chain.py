import sys
sys.path.append('../')

from create_blockchain_new import create_blockchain, bits_to_target, list_flatten, hash_interlink, make_proof, CBlockHeaderPopow, mine_block, list_flatten
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

"""
indices seem different than below because element is a hex string, not a byte array
"""
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

"""
Removes the genesis block of the proof
"""
def remove_genesis(proof):
    old_size = len(proof)
    print('Removing genesis block from proof ...')
    proof.pop(-1)
    print('OK')
    print('old size:', old_size, '-> new size:', len(proof))

"""
Changes a specific byte in a byte array
"""
def swap_byte(byte_array, index):
    mask = 1
    if byte_array[index] == 0:
        changed_byte_array = byte_array[0:index] + b'\xff' + byte_array[index+1:]
    changed_byte_array = byte_array[0:index] + b'\x00' + byte_array[index+1:]
    return changed_byte_array

"""
Changes the interlink hash in a blockhash

Each block is represented with a 112 bytes hash.
The hash is encoded as such:
Prev header:    [  0: 32]
Version:        [ 32: 33]
Something:      [ 33: 36]
Interlink hash: [ 36: 68]
Merkle root:    [ 68:100]
Time:           [100:104]
Bits:           [104:108]
Nonce:          [108:112]

By swapping byte 36, we effectively mess up the interlink hash of a the block
header indicated by the block_index parameter
"""
def change_interlink_hash(proof, block_index):
    block_of_interest = proof[block_index][0]
    changed_block = swap_byte(block_of_interest, 36)
    changed_proof = proof[0:block_index] + [(changed_block, proof[block_index][1])] + proof[block_index+1:]
    return changed_proof

"""
Deletes a number of blocks from the proof starting from block_index
"""
def skip_blocks(proof, block_index, skipped_blocks=1):

    if block_index >= len(proof):
        return proof

    for i in range(block_index, block_index+skipped_blocks):
        print('Deleting block', i)
        del proof[i]

    return proof

def replace_block(proof, headers_map, interlink_map, block_index):
    prevous_block = proof[block_index-1][0]
    block_hash = prevous_block[36:68]
    block = headers_map[block_hash]
    interlink = list_flatten(interlink_map[block.GetHash()])

    block_2 = mine_block(block.hashPrevBlock, block.nBits-1, interlink, hashMerkleRoot=b'\x00'*32)
    return proof[0:block_index] + [[block_2.serialize(), proof[block_index][1]]] + proof[block_index+1:]

def main():
    parser=argparse.ArgumentParser(description='Prints the contents of a NiPoPoW')
    parser.add_argument('--blocks', required=True, type=int, help='Number of blocks')
    parser.add_argument('--output', default='messed_up_proof.pkl', type=str, help='Name of exported proof')
    args=parser.parse_args()
    blocks=args.blocks
    output=args.output
    if output.find('.pkl') == -1:
        output += '.pkl'

    # Create blockchain
    header, headers_map, interlink_map = create_blockchain(blocks=blocks)
    print_headers(headers_map)
    print_interlinks(headers_map, interlink_map)

    # Create proof
    proof = make_proof(header, headers_map, interlink_map)
    # print_proof(proof, headers_map)

    """ Start spoiling proof """
    # remove_genesis(proof)
    # proof = change_interlink_hash(proof, 0)
    # proof = skip_blocks(proof, -2)
    # block_index = int(len(proof)/2)
    # proof = replace_block(proof, headers_map, interlink_map, int(len(proof)/2))
    """ Stop spoiling proof """

    export_proof(proof, output)

if __name__ == '__main__':
    main()
