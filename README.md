# STOMA: A Multi-Speaker Greek Speech Corpus

STOMA is a new multi-speaker Greek speech corpus designed to advance research in text-to-speech (TTS) synthesis and related speech technologies for under-resourced languages. The corpus comprises approximately 23 hours of professionally recorded read speech from six native speakers (three male and three female), captured under controlled studio conditions using a dual-booth setup to ensure acoustic consistency and high signal quality. The spoken material was selected from the Text Bank of the Center for the Greek Language, specifically from texts corresponding to the B2, C1, and C2 proficiency levels of the Certification of Attainment in Greek, ensuring linguistically rich and pedagogically balanced content. All recordings were standardized to 44.1 kHz, 16-bit mono PCM format and processed through a hybrid quality control pipeline combining automated normalization and manual verification. To assess dataset quality, we trained state-of-the-art neural TTS systems based on the FastSpeech2 acoustic model and the HiFi-GAN vocoder, achieving natural and intelligible synthesized speech. The resulting corpus provides a publicly accessible, high-quality resource that supports both linguistic research and the development of modern speech synthesis systems in Greek.

## Dataset
The dataset is available at the following location: [TBA]()

## Requirements

The training framework employs the **ESPnet** toolkit for acoustic modeling (FastSpeech2) and **ParallelWaveGAN** for the vocoder (HiFi-GAN).

To replicate the training pipeline, the following toolkits must be installed:

* **Acoustic Model:** To train the acoustic model, **ESPnet** is required. Please refer to the official [ESPnet installation guide](https://espnet.github.io/espnet/installation.html).
* **Vocoder:** To train the vocoder, **ParallelWaveGAN** is required. Installation instructions are available in the [ParallelWaveGAN repository](https://github.com/kan-bayashi/ParallelWaveGAN?tab=readme-ov-file#a-use-pip).
  
## Training Procedure
### Acoustic Model (FastSpeech2)
The training process involves a two-stage pipeline: first training a Teacher model (Tacotron2) to extract durations, and then training the Student model (FastSpeech2).

**Strategy:**
Training Strategy:
* **Main Speaker (Main_Speaker_M / Main_Speaker_F)**: FastSpeech2 models are trained from scratch to establish a robust baseline.
* **Secondary Speakers**: Models are fine-tuned from the corresponding gender-specific main speaker checkpoints (e.g., male speakers are fine-tuned from *Main_Speaker_M*).

**Step 1: Train Tacotron2**
By default, the run script is configured to train the Tacotron2 model.
1. Navigate to the `FastSpeech2` directory located under `Speakers`.
2. **Crucial Step:** Open the `db.sh` file and define the absolute path to your dataset.
3. Execute the training script:
```bash
./run.sh
```

**Step 2: Generate Alignments**
Once the Tacotron2 model is trained, you must generate the alignments (durations) and statistics required for FastSpeech2. Execute the following command to run teacher forcing inference:
```bash
./run.sh --stage 8 \
    --tts_exp exp/tts_train_raw_phn_tacotron_g2p_en_no_space \
    --inference_args "--use_teacher_forcing true" \
    --test_sets "tr_no_dev_phn dev_phn eval1_phn"
```

**Step 3: Train FastSpeech2**
After generating the alignments, proceed to train the FastSpeech2 model using Tacotron's dump directory:
```bash
./run.sh --stage 6 \
    --train_config conf/tuning/train_fastspeech2.yaml \
    --teacher_dumpdir exp/tts_train_raw_phn_tacotron_g2p_en_no_space/decode_use_teacher_forcingtrue_train.loss.ave \
    --tts_stats_dir exp/tts_train_raw_phn_tacotron_g2p_en_no_space/decode_use_teacher_forcingtrue_train.loss.ave/stats \
    --write_collected_feats true
```

***Configuration Note***: Prior to execution, you must define the absolute path to the dataset within the `db.sh` file.

### Vocoder (HiFI-GAN)
Vocoder training requires the **ParallelWaveGAN** library. In this implementation, HiFi-GAN models are trained exclusively on the main speakers. These gender-specific vocoders are subsequently utilized for all remaining speakers during synthesis.

To initiate vocoder training, please refer to the standard ESPnet2 recipe instructions provided here: [HiFi-GAN training instructions](https://github.com/kan-bayashi/ParallelWaveGAN/tree/master/egs#run-training-using-espnet2-tts-recipe-within-5-minutes).

***Permission Denied Errors***: If you encounter a "Permission Denied" error, please grant execution rights to the relevant files using the following command:
```bash
chmod u+x file
```

## Inference Procedure
To perform speech synthesis, navigate to the `Speakers/inference` directory.

### Configuration Prerequisites
Before executing the script, ensure the following:
1.  **Model Paths:** The paths to the model weights must be correctly defined.
2.  **Config Updates:** In the `config.yaml` for each model, ensure the `stats_file` paths under `normalize_conf`, `pitch_normalize_conf`, and `energy_normalize_conf` are valid and accessible.

    **Locating the Statistics Files:**
    For locally trained models, the required statistics files can be found in the following directory:
    
    ```text
    {Speaker}/FastSpeech2/exp/tts_train_tacotron2_raw_phn_none/inference_use_teacher_forcingtrue_train.loss.ave/stats/train/
    ```

    You will need to map the configuration entries to these specific files:
    * `normalize_conf` → `feats_stats.npz`
    * `pitch_normalize_conf` → `pitch_stats.npz`
    * `energy_normalize_conf` → `energy_stats`

    *Note: Locations for pretrained model statistics will be announced soon.*

### Execution
Run the inference script as follows:
```bash
python inference.py --text "Αυτή είναι μία καινούρια βάση" --speaker M --ckpt 500000
```

## Pretrained model weights
TBA 

## License
This project is licensed under the MIT License.
