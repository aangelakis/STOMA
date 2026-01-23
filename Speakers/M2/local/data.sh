#!/usr/bin/env bash

set -e
set -u
set -o pipefail

log() {
    local fname=${BASH_SOURCE[1]##*/} || fname="script"
    echo -e "$(date '+%Y-%m-%dT%H:%M:%S') (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $*"
}

SECONDS=0

# ----------------------
# Default config options
# ----------------------
stage=0
stop_stage=2
text_format=phn
g2p=espeak_ng_greek
nj=4

log "$0 $*"
. utils/parse_options.sh || exit 1
. ./path.sh || exit 1
. ./cmd.sh || exit 1
. ./db.sh || exit 1

if [ -z "${GSD}" ]; then
    log "ERROR: GSD is not set in db.sh"
    exit 1
fi

db_root=${GSD}
train_set=tr_no_dev
dev_set=dev
eval_set=eval1

log ${GSD}
# ----------------------
# Stage 0: Data prep (MODIFIED)
# ----------------------
if [ ${stage} -le 0 ] && [ ${stop_stage} -ge 0 ]; then
    log "Stage 0: Preparing data/train"

    # --- New: Define Exclusion List ---
    EXCLUDED_UTTS="excluded_utts.txt"
    cat > "${EXCLUDED_UTTS}" << EOF
M2_B2_Greek-M2-B2-03-14
M2_B2_Greek-M2-B2-30-01
M2_B2_Greek-M2-B2-36-14
M2_C1_Greek-M2-C1-01-10
M2_C1_Greek-M2-C1-15-22
M2_C1_Greek-M2-C1-27-23
M2_C2_Greek-M2-C2-01-04
M2_C2_Greek-M2-C2-24-01
M2_C2_Greek-M2-C2-51-12
M2_Harvard_Greek-M2-Harvard-05-19
M2_Harvard_Greek-M2-Harvard-18-12
M2_Harvard_Greek-M2-Harvard-29-12
EOF
    # ----------------------------------

    mkdir -p data/train
    scp=data/train/wav.scp
    utt2spk=data/train/utt2spk
    spk2utt=data/train/spk2utt
    text=data/train/text

    rm -f ${scp} ${utt2spk} ${spk2utt} ${text}

    subsets=("Harvard" "B2" "C1" "C2")
    speakers=("M2")

    for subset in "${subsets[@]}"; do
        for spk in "${speakers[@]}"; do
            audio_root="${db_root}/Speakers/${spk}/${subset}"
            text_root="${db_root}/Text/${subset}"

            [ ! -d "${audio_root}" ] && continue
            [ ! -d "${text_root}" ] && continue

            find "${audio_root}" -name "*.wav" | sort | while read -r wav_path; do
                filename=$(basename "${wav_path}" .wav)  # Greek-M-Harvard-01-01
                session_dir=$(basename "$(dirname "${wav_path}")")  # e.g., 01
                base_text_id=$(echo "${filename}" | sed -E 's/-(M2|F1|F2|M|F)//')
                text_file="${text_root}/${session_dir}/${base_text_id}.txt"

                utt_id="${spk}_${subset}_${filename}"

                # --- New: Exclusion Check ---
                if grep -q "^${utt_id}$" "${EXCLUDED_UTTS}"; then
                    log "Skipping excluded utterance: ${utt_id}"
                    continue
                fi
                # ----------------------------

                if [ -f "${text_file}" ]; then
                    echo "${utt_id} ${wav_path}" >> ${scp}
                    echo "${utt_id} ${spk}" >> ${utt2spk}
                    transcription=$(cat "${text_file}" | tr -d '\r')
                    echo "${utt_id} ${transcription}" >> ${text}
                else
                    echo "Warning: Missing text for ${wav_path}"
                fi
            done
        done
    done

    # --- New: Clean up the temporary file ---
    rm -f "${EXCLUDED_UTTS}"
    # ----------------------------------------
    
    utils/utt2spk_to_spk2utt.pl ${utt2spk} > ${spk2utt}
    utils/fix_data_dir.sh data/train
    utils/validate_data_dir.sh --no-feats data/train

    log "Shuffling data/train for unbiased split using python script"
    python shuffle_data.py data/train || exit 1

    # --- Log total hours of speech ---
    if command -v soxi >/dev/null; then
        total_sec=$(awk '{print $2}' "${scp}" | xargs -n1 soxi -D | paste -sd+ - | bc)
        total_hr=$(echo "scale=2; ${total_sec}/3600" | bc)
        echo "Total duration: ${total_hr} hours (${total_sec} seconds)"
    else
        echo "Warning: soxi not found; cannot compute duration"
    fi

fi

# ----------------------
# Stage 1: Split into dev/eval/train
# ----------------------
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
    log "Stage 1: Splitting data/train into ${train_set}, ${dev_set}, ${eval_set}"

    utils/subset_data_dir.sh --last data/train 60 data/deveval
    utils/subset_data_dir.sh --last data/deveval 30 data/${eval_set}
    utils/subset_data_dir.sh --first data/deveval 30 data/${dev_set}

    n=$(( $(wc -l < data/train/wav.scp) - 60 ))
    utils/subset_data_dir.sh --first data/train ${n} data/${train_set}
fi

# ----------------------
# Stage 2: Convert to phonemes
# ----------------------
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ] && [ "${text_format}" = phn ]; then
    log "Stage 2: Converting transcriptions to phonemes (G2P: ${g2p})"

    for dset in "${train_set}" "${dev_set}" "${eval_set}"; do
        utils/copy_data_dir.sh data/${dset} data/${dset}_phn || true
        pyscripts/utils/convert_text_to_phn.py \
            --g2p "${g2p}" --nj "${nj}" \
            data/${dset}/text data/${dset}_phn/text
        utils/fix_data_dir.sh data/${dset}_phn
    done
fi

log "Successfully finished. [elapsed=${SECONDS}s]"