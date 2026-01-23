import sys
import random

random.seed(42)

def shuffle_data_dir(data_dir):
    """
    Shuffles the Kaldi data directory files based on utt_id.
    Reads all relevant files, shuffles the utterance IDs, and rewrites the files.
    """
    if len(sys.argv) != 2:
        print("Usage: python shuffle_data.py <data_dir>", file=sys.stderr)
        sys.exit(1)

    data_dir = sys.argv[1]

    try:
        # 1. Read wav.scp to get all utterance IDs
        with open(f'{data_dir}/wav.scp', 'r') as f:
            wav_lines = [line.strip() for line in f]
        
        utt_ids = [line.split()[0] for line in wav_lines]

        # 2. Shuffle the utterance IDs
        random.shuffle(utt_ids)
        
        # 3. Load all files into memory using a dictionary keyed by utt_id
        data_map = {
            'wav.scp': {line.split()[0]: line for line in wav_lines},
            'utt2spk': {},
            'text': {},
        }

        for filename in ['utt2spk', 'text']:
            try:
                with open(f'{data_dir}/{filename}', 'r') as f:
                    for line in f:
                        line = line.strip()
                        utt = line.split()[0]
                        data_map[filename][utt] = line
            except FileNotFoundError:
                print(f"Warning: {data_dir}/{filename} not found, skipping.", file=sys.stderr)
                
        # 4. Write the files back in the new shuffled order
        for filename in ['wav.scp', 'utt2spk', 'text']:
            if data_map[filename]:
                with open(f'{data_dir}/{filename}', 'w') as f:
                    for utt in utt_ids:
                        if utt in data_map[filename]:
                            f.write(data_map[filename][utt] + '\n')
                        
        print(f"Successfully shuffled data in {data_dir}")

    except Exception as e:
        print(f"Error during shuffling: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    shuffle_data_dir(sys.argv[1])