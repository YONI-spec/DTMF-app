from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import numpy as np
import ctypes
import os
from scipy.io import wavfile
from scipy import signal  # Importation pour le rééchantillonnage
from dtmf_engine import run_goertzel_block,analyse_blocks,analyse_wav

app = Flask(__name__)
CORS(app)

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