import os, sys, wave, time
import numpy as np
import matplotlib.pyplot as plt

### Global Dataset Audio Parameters: ###
datatype = np.int16
maxrange = np.iinfo(datatype).max
gsd_params = wave._wave_params(
    # Single channel (mono)
    nchannels = 1,
    # Sample width = 2 bytes (16-bit signed int)
    sampwidth = 2,
    framerate = 44100,
    # Number of frames do not matter
    nframes = 'any',
    # Compression = None (PCM WAV)
    comptype = 'NONE',
    compname = 'not compressed'
)
gsd_params_dict = gsd_params._asdict()
### Preprocessing Hyperparameters: ###
EPSILON = 0.01
MIN_LEN_SEC = 0.3
MIN_PEAK = 10
ENERGY_THRESHOLD = 1e7
CHUNK_LEN_SEC = 0.1

# def rename_wav(wav_path, newname):
#     dirname, filename = os.path.split(wav_path)

#     rest_of_name = filename[len("Greek-"):]
#     new_name = f"{newname}-{rest_of_name}"
#     new_wav_path = os.path.join(dirname, new_name)
#     os.rename(wav_path, new_wav_path)
#     return

def params_match(params: wave._wave_params) -> bool:
    """True if input WAV parameters match the expected GSD parameters."""
    params = params._asdict()
    return all(
        gsd_params_dict[field] == params[field]
        for field in wave._wave_params._fields
        if field != 'nframes'
    )

def process_wav(wav_path):
    """Removes DC component, normalizes to near full dynamic range,
    and trims silence from beginning and end based on an energy threshold
    before overwriting the WAV file."""
    trimmed_sec = 0
    try:
        with wave.open(wav_path, 'rb') as wav:
            params = wav.getparams()
            # Checking that we get the expected audio parameters:
            if not params_match(params):
                print(
                    f"\nSkipping {wav_path} — parameter mismatch."
                    f"\nExpected: {gsd_params}"
                    f"\nGot:      {params}"
                )
                return trimmed_sec
            
            # Extract audio from WAV:
            frames = wav.readframes(params.nframes)
            audio = np.frombuffer(frames, dtype=datatype)
            if len(audio) < MIN_LEN_SEC * params.framerate:
                print(f"{wav_path}: Very short audio, skipping.")
                return trimmed_sec
            
            # Remove DC component:
            audio = audio - np.mean(audio)
            # Normalize to near full dynamic range:
            peak = np.max(np.abs(audio))
            if peak < MIN_PEAK:
                print(f"{wav_path}: Too quiet, skipping.")
                return trimmed_sec
            audio = (audio / (peak - EPSILON)) * maxrange

            # Trim beggining silence:
            step = int(CHUNK_LEN_SEC * gsd_params.framerate)
            iters = int(len(audio) // step)
            curr = 0
            for _ in range(iters):
                energy = np.sum(audio[curr:curr+step]**2)
                if energy > ENERGY_THRESHOLD:
                    break
                curr += step
            crop_start = max(0, curr - 2*step)

            # Trim trailing silence:
            curr = len(audio)
            for _ in range(iters):
                energy = np.sum(audio[curr-step:curr]**2)
                if energy > ENERGY_THRESHOLD:
                    break
                curr -= step
            crop_end = min(len(audio), curr + 2*step)

            # Visualize audio cropping:
            # timeaxis = np.arange(len(audio)) / gsd_params.framerate
            # plt.figure()
            # plt.title(wav_path)
            # plt.plot(timeaxis, audio)
            # plt.axvline(x=crop_start/gsd_params.framerate, color='red')
            # plt.axvline(x=crop_end/gsd_params.framerate, color='red')
            # plt.xlabel("Time (s)")
            # plt.ylabel("Amplitude")
            # plt.tight_layout()
            # plt.show()
            # plt.close()

            if crop_start < crop_end:
                trimmed_sec += (crop_start + len(audio) - crop_end) / gsd_params.framerate 
                audio = audio[crop_start:crop_end]
            else:
                print(f"{wav_path}: Crop range invalid, skipping silence trimming.")

        audio = audio.astype(datatype)
        processed_audio = audio.tobytes()
        
        with wave.open(wav_path, 'wb') as wav:
            wav.setnchannels(params.nchannels)
            wav.setsampwidth(params.sampwidth)
            wav.setframerate(params.framerate)
            wav.setcomptype(params.comptype, params.compname)
            wav.writeframes(processed_audio)

    except (wave.Error, EOFError) as e:
        print(f"Skipping {wav_path} — invalid WAV file or corrupted. Error: {e}")
    except Exception as e:
        print(f"Skipping {wav_path} — unexpected error: {e}")

    return trimmed_sec

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python preprocess.py /path/to/start/folder")
        sys.exit(1)

    start_folder = sys.argv[1]

    if not os.path.isdir(start_folder):
        print(f"Error: {start_folder} is not a directory.")
        sys.exit(1)

    print(f"Started .wav file processing from: {start_folder}")
    start = time.perf_counter()
    wavs_total = 0
    trimmed_sec = 0
    for root, dirs, files in os.walk(start_folder):
        for file in files:
            if file.lower().endswith('.wav'):
            # if file.lower().endswith('.wav') and file.startswith("Greek-"):
                # rename_wav(
                #     wav_path=os.path.join(root, file), 
                #     newname="GS-M"
                # )
                # continue
                full_wav_path = os.path.join(root, file)
                trimmed_sec += process_wav(full_wav_path)
                wavs_total += 1
    
    end = time.perf_counter()
    elapsed = end - start
    print(
        f"Processed {wavs_total} WAV files."
        f"\nTrimmed {trimmed_sec:.2f} seconds of silence."
        f"\nElapsed time: {elapsed:.2f} seconds."
    )