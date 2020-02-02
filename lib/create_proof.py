import argparse

def prefix():
    return '../proofs/'

def import_proof(filename='proof.pkl'):
    import pickle
    pickle_in = open(filename,'rb')
    proof = pickle.load(pickle_in)
    return proof

def create_proof(blocks=450000, filename='proof.pkl'):
    import pickle
    import create_blockchain_new as blockchain_utils
    header, headerMap, mapInterlink = blockchain_utils.create_blockchain(blocks=blocks)
    proof = blockchain_utils.make_proof(header, headerMap, mapInterlink)
    pickle_out = open(filename, 'wb')
    pickle.dump(proof, pickle_out)
    pickle_out.close()
    print("Proof was written in " + filename)
    return proof

def make_proof_file_name(blocks):
    return prefix() + 'proof_'+str(blocks)+'.pkl'

def make_fork_proof_file_name(mainblocks, fork_index, forkblocks):
    return prefix() + str(mainblocks) + '_-' + str(fork_index) + '_+' + str(forkblocks) + '.pkl'

def get_proof(blocks):
    proof_file_name = make_proof_file_name(blocks)
    f = None
    try:
        f = open(proof_file_name)
        print('File', proof_file_name, 'already exists. Importing...')
        proof = import_proof(proof_file_name)
        f.close()
    except IOError:
        print('File', proof_file_name, 'does not exist. Creating...')
        proof = create_proof(blocks, proof_file_name)
    finally:
        print('...ok')

    return proof

def create_mainproof_and_forkproof(mainblocks, fork_index, forkblocks):
    import create_blockchain_new as blockchain_utils

    header = None
    headerMap = None
    mapInterlink = None

    proof_filename = make_proof_file_name(mainblocks)
    fork_proof_filename = make_fork_proof_file_name(mainblocks, fork_index, forkblocks)

    try:
        open(fork_proof_filename)
    except IOError:
        header, headerMap, mapInterlink = blockchain_utils.create_blockchain(blocks=mainblocks)

    proof = get_proof(mainblocks)

    f = None
    try:
        f = open(fork_proof_filename)
        print('File', fork_proof_filename, 'already exists. Importing...')
        f.close()
    except IOError:
        print('File', fork_proof_filename, 'does not exist. Creating...')
        header_f, headerMap_f, mapInterlink_f = blockchain_utils.create_fork(header,
                                                         headerMap,
                                                         mapInterlink,
                                                         fork=fork_index,
                                                         blocks=forkblocks)

        proof_f = blockchain_utils.make_proof(header_f, headerMap_f, mapInterlink_f)

        import pickle
        pickle_out = open(fork_proof_filename, 'wb')
        pickle.dump(proof_f, pickle_out)
        pickle_out.close()
    finally:
        print('...ok')

    print('Created fork at ' + fork_proof_filename)

    return (make_proof_file_name(mainblocks), fork_proof_filename)

def main():
    parser=argparse.ArgumentParser(description='Create and store proof from create_blockchain_new.py')
    parser.add_argument('--blocks', required=True, type=int, help='Number of blocks')
    args=parser.parse_args()
    blocks=args.blocks
    proof=get_proof(blocks)
    print('Proof size:', len(proof))

if __name__ == "__main__":
    main()
