from espnet2.bin.tts_inference import Text2Speech
import numpy as np
from pyscripts.utils import convert_text_to_phn
import os
import sys
import tempfile
import subprocess
import argparse


# Argument parser setup
parser = argparse.ArgumentParser(description="Greek TTS with ESPnet and HiFi-GAN")
parser.add_argument("--text", "-t", type=str, help="Input Greek text")
parser.add_argument("--speaker", "-s", type=str, choices=["M", "F", "M1", "M2", "F1", "F2"], help="Speaker ID", required=True)
parser.add_argument("--ckpt", "-c", type=str, help="Checkpoint steps", default="500000")
parser.add_argument("--model", "-m", type=str, help="Model type", default="fastspeech2")
args = parser.parse_args()

base_dir = "/home/alex/STOMA_22050/Text/"

mos_test = [
    "Greek-B2-03-14", "Greek-B2-30-01", "Greek-B2-36-12",
    "Greek-C1-01-10", "Greek-C1-15-22", "Greek-C1-27-23",
    "Greek-C2-01-04", "Greek-C2-24-01", "Greek-C2-51-12",
    "Greek-Harvard-05-19", "Greek-Harvard-18-12", "Greek-Harvard-29-12"
]

# The following code just finds the text inside the .txt files of the above list
# Initialize the array to store the contents
texts = []
missing_files_count = 0

print("Starting file content extraction...")
print("-" * 40)

for full_name in mos_test:
    try:
        # Split the name: ['Greek', 'B2', '03', '14']
        parts = full_name.split('-')
        
        # Extract the required components
        folder_name = parts[1]  # e.g., 'B2'
        text_id = parts[2]      # e.g., '03' - This is the assumed file name
        
        # 1. Construct the full path. We assume the file is named just by its ID + .txt
        # Example path: STOMA/Text/B2/03.txt
        full_path = os.path.join(base_dir, folder_name, f"{text_id}/{full_name}.txt")
        
        # 2. Read the file content
        with open(full_path, "r", encoding='utf-8') as file:
            content = file.read()
            texts.append(content)
            print(f"Loaded: {full_path}")
            
    except IndexError:
        # This handles cases where the file name is not structured as expected
        texts.append(f"FILE_ERROR: Invalid name format for {full_name}")
        print(f"ERROR: Invalid name format for {full_name}")
        missing_files_count += 1
    except FileNotFoundError:
        # File could not be found at the calculated path
        texts.append(f"FILE_MISSING: {full_name}")
        print(f"Missing: {full_path}")
        missing_files_count += 1
    except Exception as e:
        # Catch any other reading errors (e.g., permission issues)
        texts.append(f"FILE_ERROR: {full_name} ({e})")
        print(f"Error reading {full_path}: {e}")
        missing_files_count += 1

# --- Final Output ---
print("\n" + "=" * 50)
print(f"Array creation complete. Total items loaded: {len(texts)}")
print(f"Actual contents array size: {len(texts)}")
if missing_files_count > 0:
    print(f"WARNING: {missing_files_count} files were missing or had errors.")
print("=" * 50)

print(texts)
# End of file content extraction

texts = [args.text] if args.text else texts
speaker = args.speaker
checkpoint = args.ckpt
model = args.model

if speaker in ["M1", "M2", "M"]:
    path = "trained_models_M"
    vocoder_ckpt = f"{path}/vocoder/checkpoint"
    vocoder_config = f"{path}/vocoder/config.yml"
    SCALE = 1.0
else:
    path = "trained_models_F"
    vocoder_ckpt = f"{path}/vocoder/checkpoint-{checkpoint}steps.pkl"
    vocoder_config = f"{path}/vocoder/config.yml"
    vocoder_stats = "/home/alex/ParallelWaveGAN/egs/Main_Speaker_F_shuffled/voc1/exp/train_nodev_hifigan.v1/stats.h5"
    SCALE = 0.85


if speaker == "M":
    model_ckpt = f"{path}/Main_Speaker_M/valid.loss.ave_5best.pth"
    model_config = f"{path}/Main_Speaker_M/config.yaml"
elif speaker == "M1":
    model_ckpt = f"{path}/M1valid.loss.ave_5best.pth"
    model_config = f"{path}/M1/config.yaml"
elif speaker == "M2":
    model_ckpt = f"{path}/M2/valid.loss.ave_5best.pth"
    model_config = f"{path}/M2/config.yaml"
elif speaker == "F":
    model_ckpt = f"{path}/Main_Speaker_F/{model}/valid.loss.ave_5best.pth"
    model_config = f"{path}/Main_Speaker_F/{model}/config.yaml"
    feats_stats_path = "/home/alex/espnet/espnet/egs2/Main_Speaker_F_shuffled/tts1/exp/tts_train_tacotron2_raw_phn_none/inference_use_teacher_forcingtrue_train.loss.ave/stats/train/feats_stats.npz"
elif speaker == "F1":
    model_ckpt = f"{path}/F1/{model}/valid.loss.ave_5best.pth"
    model_config = f"{path}/F1/{model}/config.yaml"
elif speaker == "F2":
    model_ckpt = f"{path}/F2/{model}/valid.loss.ave_5best.pth"
    model_config = f"{path}/F2/{model}/config.yaml"

wav_out_dir = f"mos_{speaker}_{model}_{checkpoint}"

    
# Load the pretrained text2mel model (in our case fastspeech2)
tts = Text2Speech.from_pretrained(
    model_file=model_ckpt,
    train_config=model_config,
)

g2p = "espeak_ng_greek"
feats_scp_lines = []

with tempfile.TemporaryDirectory() as tmpdir:
    in_path = os.path.join(tmpdir, "input.txt")
    out_path = os.path.join(tmpdir, "output.txt")

    # Save input in Kaldi-style format
    with open(in_path, "w", encoding="utf-8") as f:
        for i, text in enumerate(texts):
            utt_id = mos_test[i]
            f.write(f"{utt_id} {text}\n")

    sys.argv = [
        "convert_text_to_phn.py",
        "--g2p", g2p,
        "--nj", "4",
        in_path,
        out_path
    ]

    convert_text_to_phn.main()

    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            utt_id, phonemes = line.strip().split(" ", 1)

            output = tts(phonemes)
            mel_normalized = output["feat_gen"].cpu().numpy()
            mel = mel_normalized * SCALE  # Simple global gain adjustment

            mel_path = f"dump_feats/{utt_id}.npy"
            os.makedirs("dump_feats", exist_ok=True)
            np.save(mel_path, mel)

            full_mel_path = os.path.abspath(mel_path)
            feats_scp_lines.append(f"{utt_id} {full_mel_path}")


with open("feats.scp", "w", encoding="utf-8") as f:
    f.write("\n".join(feats_scp_lines))

print("Generating wav files for speaker:", speaker, "and checkpoint:", checkpoint)

subprocess.run([
    "parallel-wavegan-decode",
    "--checkpoint", vocoder_ckpt,
    "--config", vocoder_config,
    "--scp", "feats.scp",
    "--outdir", wav_out_dir
], check=True)

print("Generated wavs are in:", wav_out_dir)
