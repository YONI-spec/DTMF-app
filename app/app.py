from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import ctypes
import os
from scipy.io import wavfile
from scipy import signal  # Importation pour le rééchantillonnage

app = Flask(__name__)
CORS(app)

# Chargement de la DLL C
dll_path = os.path.abspath("goertzel.dll")
lib = ctypes.CDLL(dll_path)

lib.goertzel_run.argtypes = [
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int,
    ctypes.c_float,
    ctypes.POINTER(ctypes.c_float)
]
lib.goertzel_run.restype = None

# Constantes DTMF 
F_LOW  = [697.0, 770.0, 852.0, 941.0]
F_HIGH = [1209.0, 1336.0, 1477.0, 1633.0]

DTMF_MAP = {
    '1': (697, 1209), '2': (697, 1336), '3': (697, 1477), 'A': (697, 1633),
    '4': (770, 1209), '5': (770, 1336), '6': (770, 1477), 'B': (770, 1633),
    '7': (852, 1209), '8': (852, 1336), '9': (852, 1477), 'C': (852, 1633),
    '*': (941, 1209), '0': (941, 1336), '#': (941, 1477), 'D': (941, 1633),
}

BLOCK_SIZE = 205

def find_char(fl, fh):
    for char, (fb, fhb) in DTMF_MAP.items():
        if abs(fl - fb) < 20 and abs(fh - fhb) < 20:
            return char
    return '?'

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
        best_low_f    = F_LOW[0]
        best_high_f   = F_HIGH[0]
        best_low_e    = 0.0
        best_high_e   = 0.0
        raw_detected  = '?'

        if total_energy > min_energy:
            mags, display_mags, idx_l, idx_h = run_goertzel_block(samples, fs)
            best_low_f  = F_LOW[idx_l]
            best_high_f = F_HIGH[idx_h - 4]
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

#Routes

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier reçu'}), 400

    f = request.files['file']
    try:
        import io
        raw = f.read()
        fs, data = wavfile.read(io.BytesIO(raw))

        # 1. Conversion Mono
        if data.ndim > 1:
            data = data[:, 0]
        data = data.astype(np.float32)

        # 2. RÉÉCHANTILLONNAGE FORCÉ À 8000 HZ (Crucial pour la précision)
        target_fs = 8000
        if fs != target_fs:
            num_samples = int(len(data) * target_fs / fs)
            data = signal.resample(data, num_samples)
            fs = target_fs

        # 3. BOOST VOLUME (Normalisation de crête)
        peak = np.abs(data).max()
        if peak > 0:
            data /= peak

        frames, sequence = analyse_wav(data, fs)
        duration = round(len(data) / fs, 3)

        return jsonify({
            'ok'         : True,
            'fs'         : int(fs),
            'duration_s' : duration,
            'sequence'   : ''.join(sequence),
            'frames'     : frames,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)