import numpy as np 
import ctypes
from dtmf_utils import DTMF_number,f_b,f_h
from detector import find_char,dll_path,lib




lib.goertzel_run.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int,
    ctypes.c_float,
    ctypes.POINTER(ctypes.c_float)
]
lib.goertzel_run.restype = None

BLOCK_SIZE = 205

def run_goertzel_block(samples, fs):
    mags = np.zeros(8, dtype=np.float32)
    lib.goertzel_run(
        samples.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        BLOCK_SIZE,
        float(fs),
        mags.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    )
    norm = max(float(np.max(mags)), 1e-6)
    display_mags = [round(float(m) / norm, 4) for m in mags]
    idx_l = int(np.argmax(mags[:4]))
    idx_h = int(np.argmax(mags[4:])) + 4
    return mags, display_mags, idx_l, idx_h





def analyse_blocks(blocks_iter, fs):
    frames   = []
    sequence = []

    # Réglages de précision pour audio bruité/faible
    min_energy     = 0.005   # Plancher de bruit très bas pour capter les sons lointains
    rel_threshold  = 0.15    # Un pic doit représenter 15% de l'énergie du bloc
    min_duration   = 3       # Doit être stable sur 3 blocs (~75ms)
    min_silence    = 2       # 2 blocs de silence minimum entre deux touches

    candidate_key  = None
    stable_count   = 0
    silence_count  = 0
    last_added_key = None

    for block_index, (samples, time_s) in enumerate(blocks_iter):
        total_energy = float(np.mean(samples ** 2))

        is_tone       = False
        detected_char = None
        display_mags  = [0.0] * 8
        best_low_f    = f_b[0]
        best_high_f   = f_h[0]
        best_low_e    = 0.0
        best_high_e   = 0.0
        raw_detected  = '?'

        if total_energy > min_energy:
            mags, display_mags, idx_l, idx_h = run_goertzel_block(samples, fs)
            best_low_f  = f_b[idx_l]
            best_high_f = f_h[idx_h - 4]
            best_low_e  = float(mags[idx_l])
            best_high_e = float(mags[idx_h])
            ref = total_energy * rel_threshold

            if mags[idx_l] > ref and mags[idx_h] > ref:
                raw_detected = find_char(best_low_f, best_high_f)
                if raw_detected != '?':
                    is_tone = True

        if is_tone:
            silence_count = 0
            if raw_detected == candidate_key:
                stable_count += 1
            else:
                candidate_key = raw_detected
                stable_count  = 1

            if stable_count >= min_duration and candidate_key != last_added_key:
                detected_char  = candidate_key
                last_added_key = candidate_key
                sequence.append(detected_char)
        else:
            silence_count += 1
            if silence_count >= min_silence:
                last_added_key = None
                candidate_key  = None
                stable_count   = 0

        frames.append({
            'block_index'  : block_index,
            'time_s'       : round(time_s, 4),
            'magnitudes'   : display_mags,
            'best_low_f'   : best_low_f,
            'best_high_f'  : best_high_f,
            'best_low_e'   : round(best_low_e, 6),
            'best_high_e'  : round(best_high_e, 6),
            'total_energy' : round(total_energy, 6),
            'is_tone'      : is_tone,
            'detected_char': detected_char,
        })

    return frames, sequence



def analyse_wav(data, fs):
    def blocks():
        for start in range(0, len(data) - BLOCK_SIZE + 1, BLOCK_SIZE):
            samples = data[start:start + BLOCK_SIZE].astype(np.float32)
            yield samples, start / fs
    return analyse_blocks(blocks(), fs)
