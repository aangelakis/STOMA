#!/usr/bin/env bash
# Set bash to 'debug' mode
set -e
set -u
set -o pipefail

# -----------------------------
# Feature extraction parameters
# -----------------------------
fs=22050
n_fft=1024
n_shift=256
win_length=1024

# -----------------------------
# Text format and G2P settings
# -----------------------------
text_format=phn  # Use "raw" or "phn"
# g2p=espeak_ng_greek
token_type=phn   # Use phn for phoneme-level training

# -----------------------------
# Data prep related
# -----------------------------
local_data_opts="--text_format ${text_format}"
# if [ "${text_format}" = "phn" ]; then
#     local_data_opts+=" --g2p ${g2p}"
# fi

dset_suffix=""
if [ "${text_format}" = "phn" ]; then
    dset_suffix=_phn
fi

train_set=tr_no_dev${dset_suffix}
valid_set=dev${dset_suffix}
test_sets="dev${dset_suffix} eval1${dset_suffix}"

# -----------------------------
# Configs
# -----------------------------
train_config=conf/tuning/train_tacotron2.yaml
inference_config=conf/tuning/decode_tacotron2.yaml
g2p=none

# -----------------------------
# Run TTS
# -----------------------------

# vocoder_file="checkpoint-125000steps.pkl"

./tts.sh \
    --local_data_opts "${local_data_opts}" \
    --audio_format wav \
    --lang el \
    --feats_type raw \
    --fs "${fs}" \
    --n_fft "${n_fft}" \
    --n_shift "${n_shift}" \
    --win_length "${win_length}" \
    --token_type "${token_type}" \
    --cleaner none \
    --g2p "${g2p}" \
    --train_config "${train_config}" \
    --train_set "${train_set}" \
    --valid_set "${valid_set}" \
    --test_sets "${test_sets}" \
    --srctexts "data/${train_set}/text" \
    "$@"
