"""
Create and edit chains and proofs
"""


import argparse
from create_blockchain_new import (
    create_blockchain,
    list_flatten,
    make_proof,
    mine_block,
    verify_proof,
    create_fork,
    Hash,
    CBlockHeaderPopow,
)
from create_proof import ProofTool


def print_headers(headers_map, fork=False):
    """
    Prints a chain iterating its headers
    """

    print("\nHeaders")
    for header_hash in list(headers_map.keys()):
        header = headers_map[header_hash]
        if fork and header.hashMerkleRoot != b'\xcc'*32:
            continue

        print("header hash:\t\t", header.GetHash().hex())
        print()
        print("prev block hash:\t", header.hashPrevBlock.hex())
        print("merkle tree root hash:\t", header.hashMerkleRoot.hex())
        print("interlink hash:\t\t", header.hashInterlink.hex())
        print("level\t\t\t", header.compute_level())
        print(32 * "-")


def print_tuple(_tuple):
    """
    Prints a tuple
    """

    if _tuple == ():
        return
    for element in _tuple:
        if isinstance(element, tuple):
            print_tuple(element)
        else:
            print("Interlink:", element.hex()[:6])


def print_interlinks(headers_map, interlink_map):
    """
    Print the interlinks of the blocks of a chain
    """

    print("\nInterlinks")
    for i in interlink_map.keys():
        print("Key:", i.hex()[:6], "| Level:", int(headers_map[i].compute_level()))
        print_tuple(interlink_map[i])
        print("+" * 32)


# FIXME: Check indices again
def print_proof_element(element):
    """
    indices seem different than below because element is a hex string, not a byte array
    """

    print("Prev header:\t", element[0:64])
    # print('Version:\t',        element[ 64: 66])
    # print('Something:\t',      element[ 66: 72])
    print("Interlink hash:\t", element[72:136])
    print("Merkle root:\t", element[136:200])
    # print('Time:\t\t',         element[200:208])
    # print('Bits:\t\t',         element[208:216])
    # print('Nonce:\t\t',        element[216:224])


# FIXME: Check indices again
def print_proof(proof, headers_map):
    """
    Prints a proof
    """

    print("\nProof")
    for i, _ in enumerate(proof):
        if i == 0:
            print(i, "Header:\t\t\t", "We dont know yet")
        else:
            print(
                i, "Header:\t\t\t",
                CBlockHeaderPopow.deserialize(proof[i][0]).GetHash().hex(),
            )
        header_hash, _ = proof[i]
        element = header_hash.hex()
        print("Previous block hash:\t", element[72:136])
        print("Interlink hash:\t\t", element[0:64])
        print()
    print("Chain length:", len(headers_map))
    print("Proof length:", len(proof))


def remove_genesis(proof):
    """
    Removes the genesis block of the proof
    """

    old_size = len(proof)
    print("Removing genesis block from proof ...")
    proof.pop(-1)
    print("OK")
    print("old size:", old_size, "-> new size:", len(proof))


def swap_byte(byte_array, index):
    """
    Changes a specific byte in a byte array
    """

    if byte_array[index] == 0:
        changed_byte_array = byte_array[0:index] + b"\xff" + byte_array[index + 1 :]
    changed_byte_array = byte_array[0:index] + b"\x00" + byte_array[index + 1 :]
    return changed_byte_array


# FIXME: Check indices again
def change_interlink_hash(proof, block_index):
    """
    Changes the interlink hash in a block hash

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

    block_of_interest = proof[block_index][0]
    changed_block = swap_byte(block_of_interest, 0)
    changed_proof = (
        proof[0:block_index]
        + [(changed_block, proof[block_index][1])]
        + proof[block_index + 1 :]
    )
    return changed_proof


def skip_blocks(proof, block_index, skipped_blocks=1):
    """
    Deletes a number of blocks from the proof starting from block_index
    """

    if block_index >= len(proof):
        return proof

    for i in range(block_index, block_index + skipped_blocks):
        print("Deleting block", i)
        del proof[i]

    return proof


def replace_block(proof, headers_map, interlink_map, block_index):
    """
    Replaces a block in the proof.
    The new block has the same interlink but different header hash
    """

    prevous_block = proof[block_index - 1][0]
    block_hash = prevous_block[36:68]
    block = headers_map[block_hash]
    interlink = list_flatten(interlink_map[block.GetHash()])

    block_2 = mine_block(
        block.hashPrevBlock, block.nBits - 1, interlink, hashMerkleRoot=b"\x00" * 32
    )
    return (
        proof[0:block_index]
        + [[block_2.serialize(), proof[block_index][1]]]
        + proof[block_index + 1 :]
    )


def main():
    """
    Create, edit and print chains and proofs
    """

    parser = argparse.ArgumentParser(description="Prints the contents of a NiPoPoW")
    parser.add_argument("--blocks", required=True, type=int, help="Number of blocks")
    parser.add_argument(
        "--output", default="proof.pkl", type=str, help="Name of exported proof"
    )
    args = parser.parse_args()
    blocks = args.blocks
    output = args.output
    if output.find(".pkl") == -1:
        output += ".pkl"

    # Create blockchain
    header, headers_map, interlink_map = create_blockchain(blocks=blocks)
    print_headers(headers_map)
    print_interlinks(headers_map, interlink_map)

    # Create proof
    proof = make_proof(header, headers_map, interlink_map)
    print_proof(proof, headers_map)

    ### Start spoiling proof

    # remove_genesis(proof)
    # proof = change_interlink_hash(proof, 0)
    # proof = skip_blocks(proof, -2)
    # proof = replace_block(proof, headers_map, interlink_map, int(len(proof)/2))
    # print_proof(proof, headers_map)
    # verify_proof(Hash(proof[0][0]), proof)

    ### Stop spoiling proof

    n_header = header
    fork_headers, fork_headers_map, fork_interlink_map = create_fork(
        n_header, headers_map.copy(), interlink_map.copy(), fork=100, blocks=50
    )
    fork_proof = make_proof(fork_headers, fork_headers_map, fork_interlink_map)

    # print_headers(fork_headers_map, True)
    # print_proof(fork_proof, fork_headers_map)

    # print_interlinks(headers_map, interlink_map)
    # print_interlinks(fork_headers_map, fork_interlink_map)

    verify_proof(Hash(proof[0][0]), proof)
    print()
    verify_proof(Hash(fork_proof[0][0]), fork_proof)

    print("Existing proof lenght:", len(proof))
    print("Contesting proof lenght:", len(fork_proof))

    fork_proof_lca = 0
    proof_lca = 0
    contesting = []
    for i, fp in enumerate(fork_proof):
        if fp in proof:
            fork_proof_lca = i - 1
            break
        contesting.append(fp)

    for i, p in enumerate(proof):
        if p[0] == contesting[-1][0]:
            proof_lca = i
            break

    print(" 0:", proof[0][0].hex())
    print("-1:", proof[-1][0].hex())
    print(" 0:", fork_proof[0][0].hex())
    print("-1:", fork_proof[-1][0].hex())
    print(" 0", contesting[0][0].hex())
    print("-1", contesting[-1][0].hex())

    print("lca in proof is", proof_lca)
    print("lca in fork proof is", fork_proof_lca)
    print("Contesting length:", len(contesting))
    print(proof[proof_lca][0].hex())
    print(fork_proof[fork_proof_lca][0].hex())
    print(contesting[-1][0].hex())

    # print_proof(contesting, fork_interlink_map)

    verify_proof(Hash(contesting[0][0]), contesting)

    proof_tool = ProofTool("../../data/proofs/")
    proof_tool.export_proof(contesting, output)


if __name__ == "__main__":
    main()
