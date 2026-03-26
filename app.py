from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import ctypes
import os
from scipy.io import wavfile

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
    """Appelle la DLL sur un bloc, renvoie (mags, display_mags, idx_l, idx_h)."""
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
    """
    Logique de detection partagee entre le mode fichier et le mode live.
    blocks_iter : iterable de tableaux numpy float32 de taille BLOCK_SIZE.
    Renvoie (frames, sequence).
    """
    frames   = []
    sequence = []

    # Reglages de precision
    min_energy    = 0.008   # plancher de bruit
    rel_threshold = 0.2     # un pic doit faire 20% de l'energie du bloc
    min_duration  = 3       # blocs consecutifs pour valider (~75ms)
    min_silence   = 2       # blocs de silence pour liberer le verrou

    # Variables d'etat
    candidate_key  = None
    stable_count   = 0
    silence_count  = 0
    last_added_key = None

    for block_index, (samples, time_s) in enumerate(blocks_iter):
        total_energy = float(np.mean(samples ** 2))

        is_tone       = False
        detected_char = None    # caractere valide sur CE bloc (pour l'affichage)
        display_mags  = [0.0] * 8
        best_low_f    = F_LOW[0]
        best_high_f   = F_HIGH[0]
        best_low_e    = 0.0
        best_high_e   = 0.0
        raw_detected  = '?'

        # 1. Detection brute
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

        # 2. Machine a etats (stabilite + silence)
        if is_tone:
            silence_count = 0
            if raw_detected == candidate_key:
                stable_count += 1
            else:
                candidate_key = raw_detected
                stable_count  = 1

            # Validation : stable ET differente de la derniere touche envoyee
            if stable_count >= min_duration and candidate_key != last_added_key:
                detected_char  = candidate_key
                last_added_key = candidate_key
                sequence.append(detected_char)
        else:
            silence_count += 1
            if silence_count >= min_silence:
                last_added_key = None   # libere le verrou
                candidate_key  = None
                stable_count   = 0

        frames.append({
            'block_index'  : block_index,
            'time_s'       : round(time_s, 4),
            'magnitudes'   : display_mags,
            'low_freqs'    : F_LOW,
            'high_freqs'   : F_HIGH,
            'best_low_f'   : best_low_f,
            'best_high_f'  : best_high_f,
            'best_low_e'   : round(best_low_e, 6),
            'best_high_e'  : round(best_high_e, 6),
            'total_energy' : round(total_energy, 6),
            'is_tone'      : is_tone,
            'stable_count' : stable_count,
            'silence_count': silence_count,
            'raw_detected' : raw_detected,
            'detected_char': detected_char,
        })

    return frames, sequence


def analyse_wav(data, fs):
    """Mode fichier : genere l'iterateur de blocs depuis le signal complet."""
    def blocks():
        for start in range(0, len(data) - BLOCK_SIZE + 1, BLOCK_SIZE):
            samples = data[start:start + BLOCK_SIZE].astype(np.float32)
            yield samples, start / fs

    return analyse_blocks(blocks(), fs)


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/analyze', methods=['POST'])
def analyze():
    """Mode fichier : upload WAV complet, retourne tous les frames."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier recu'}), 400

    f = request.files['file']
    if not f.filename.lower().endswith('.wav'):
        return jsonify({'error': 'Fichier WAV requis'}), 400

    try:
        import io
        raw = f.read()
        fs, data = wavfile.read(io.BytesIO(raw))

        if data.ndim > 1:
            data = data[:, 0]
        data = data.astype(np.float32)
        peak = np.abs(data).max()
        if peak > 0:
            data /= peak

        frames, sequence = analyse_wav(data, fs)
        duration = round(len(data) / fs, 3)

        return jsonify({
            'ok'         : True,
            'fs'         : int(fs),
            'duration_s' : duration,
            'n_blocks'   : len(frames),
            'sequence'   : ''.join(sequence),
            'frames'     : frames,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/analyze_live', methods=['POST'])
def analyze_live():
    """
    Mode micro live : recoit un chunk PCM float32 brut (body = bytes),
    avec fs et block_offset passes en query string.
    Retourne le frame unique analyse + l'etat courant de la sequence.

    Le frontend envoie les chunks un par un et maintient la sequence
    cote serveur via l'etat stocke en session Flask (ou simplement
    en renvoyant tout le contexte). Pour rester stateless on accepte
    tout le contexte dans le body JSON.
    """
    data = request.get_json(force=True)
    if not data:
        return jsonify({'error': 'JSON attendu'}), 400

    try:
        fs      = int(data.get('fs', 8000))
        samples = np.array(data['samples'], dtype=np.float32)
        # Contexte de la machine a etats transmis par le client
        state   = data.get('state', {})

        min_energy    = 0.008
        rel_threshold = 0.2
        min_duration  = 3
        min_silence   = 2

        candidate_key  = state.get('candidate_key',  None)
        stable_count   = int(state.get('stable_count',   0))
        silence_count  = int(state.get('silence_count',  0))
        last_added_key = state.get('last_added_key', None)
        sequence       = list(state.get('sequence',      []))

        # Assure la taille du bloc
        if len(samples) < BLOCK_SIZE:
            samples = np.pad(samples, (0, BLOCK_SIZE - len(samples)))
        samples = samples[:BLOCK_SIZE]

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

        new_state = {
            'candidate_key' : candidate_key,
            'stable_count'  : stable_count,
            'silence_count' : silence_count,
            'last_added_key': last_added_key,
            'sequence'      : sequence,
        }

        frame = {
            'magnitudes'   : display_mags,
            'best_low_f'   : best_low_f,
            'best_high_f'  : best_high_f,
            'best_low_e'   : round(best_low_e, 6),
            'best_high_e'  : round(best_high_e, 6),
            'total_energy' : round(total_energy, 6),
            'is_tone'      : is_tone,
            'stable_count' : stable_count,
            'raw_detected' : raw_detected,
            'detected_char': detected_char,
        }

        return jsonify({
            'ok'      : True,
            'frame'   : frame,
            'state'   : new_state,
            'sequence': ''.join(sequence),
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ping')
def ping():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, port=5000)