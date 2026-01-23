# STOMA: A Multi-Speaker Greek Speech Corpus

STOMA is a new multi-speaker Greek speech corpus designed to advance research in text-to-speech (TTS) synthesis and related speech technologies for under-resourced languages. The corpus comprises approximately 23 hours of professionally recorded read speech from six native speakers (three male and three female), captured under controlled studio conditions using a dual-booth setup to ensure acoustic consistency and high signal quality. The spoken material was selected from the Text Bank of the Center for the Greek Language, specifically from texts corresponding to the B2, C1, and C2 proficiency levels of the Certification of Attainment in Greek, ensuring linguistically rich and pedagogically balanced content. All recordings were standardized to 44.1 kHz, 16-bit mono PCM format and processed through a hybrid quality control pipeline combining automated normalization and manual verification. To assess dataset quality, we trained state-of-the-art neural TTS systems based on the FastSpeech2 acoustic model and the HiFi-GAN vocoder, achieving natural and intelligible synthesized speech. The resulting corpus provides a publicly accessible, high-quality resource that supports both linguistic research and the development of modern speech synthesis systems in Greek.

## Dataset
The dataset is available at the following location: [Dataset]()

## Requirements

The training framework employs the **ESPnet** toolkit for acoustic modeling (FastSpeech2) and **ParallelWaveGAN** for the vocoder (HiFi-GAN).

To replicate the training pipeline, the following toolkits must be installed:

* **Acoustic Model:** To train the acoustic model, **ESPnet** is required. Please refer to the official [ESPnet installation guide](https://espnet.github.io/espnet/installation.html).
* **Vocoder:** To train the vocoder, **ParallelWaveGAN** is required. Installation instructions are available in the [ParallelWaveGAN repository](https://github.com/kan-bayashi/ParallelWaveGAN?tab=readme-ov-file#a-use-pip).
  
## Training Procedure
### Acoustic Model (FastSpeech2)
Upon successful installation of ESPnet, training can be initiated for individual speakers. Navigate to the `Speakers/<Speaker_Directory>/FastSpeech2` directory and execute the run script:
```bash
./run.sh
```

***Configuration Note***: Prior to execution, you must define the absolute path to the dataset within the `db.sh` file.

Training Strategy:
* **Main Speaker (Main_Speaker_M / Main_Speaker_F)**: FastSpeech2 models are trained from scratch to establish a robust baseline.
* **Secondary Speakers**: Models are fine-tuned from the corresponding gender-specific main speaker checkpoints (e.g., male speakers are fine-tuned from *Main_Speaker_M*).

### Vocoder (HiFI-GAN)
Vocoder training requires the **ParallelWaveGAN** library. In this implementation, HiFi-GAN models are trained exclusively on the main speakers. These gender-specific vocoders are subsequently utilized for all remaining speakers during synthesis.

To initiate vocoder training, please refer to the standard ESPnet2 recipe instructions provided here: [HiFi-GAN training instructions](https://github.com/kan-bayashi/ParallelWaveGAN/tree/master/egs#run-training-using-espnet2-tts-recipe-within-5-minutes).

***Permission Denied Errors***: If you encounter a "Permission Denied" error, please grant execution rights to the relevant files using the following command:
```bash
chmod u+x file
```

## Inference Procedure
add the inference procedure here.

## Pretrained model weights
add the model weights here

## License
This project is licensed under the MIT License.
