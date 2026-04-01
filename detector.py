import numpy as np
import ctypes
import os
from dtmf_utils import DTMF_number, f_h, f_b
from generator import sequence_final

# configuration du pont C (ctypes)
dll_path = os.path.abspath("goertzel.dll")
lib = ctypes.CDLL(dll_path)

# On définit bien ici que la fonction C 
lib.goertzel_run.argtypes = [ctypes.POINTER(ctypes.c_float), ctypes.c_int, ctypes.c_float, ctypes.POINTER(ctypes.c_float)]

# fonction python (Celle que app.py va importer) 
def goertzel_run_python(samples, fs):
    """
    Cette fonction fait le pont entre Python et le C.
    """
    # Préparation du tableau de sortie pour les 8 fréquences
    magnitudes = np.zeros(8, dtype=np.float32)
    
    # Conversion du bloc audio en format compatible C
    samples_c = samples.astype(np.float32)
    
    # Appel de la fonction C (lib.goertzel_run)
    lib.goertzel_run(
        samples_c.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        len(samples_c),
        float(fs),
        magnitudes.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    )
    
    return magnitudes

# On définit la signature de la fonction C
lib.goertzel_run.argtypes = [
    ctypes.POINTER(ctypes.c_float), # buffer
    ctypes.c_int,                   # size
    ctypes.c_float,                 # fs
    ctypes.POINTER(ctypes.c_float)  # magnitudes (sortie)
]
lib.goertzel_run.restype = None

Fs = 8000

# logique de recherche du caractère 
def find_char(best_low_freq, best_high_freq):
    for char, (fb, fh) in DTMF_number.items():
        if abs(best_low_freq - fb) < 20 and abs(best_high_freq - fh) < 20:
            return char
    return "?"

# boucle principale d'analyse
detector_keys = []
last_state = "silence"

# On prépare un tableau pour les 8 fréquences cibles définies dans le C
# Ordre : 697, 770, 852, 941 (Basses) puis 1209, 1336, 1477, 1633 (Hautes)
all_target_freqs = f_b + f_h + [1633.0] if len(f_h) < 4 else f_b + f_h

for i in np.arange(0, len(sequence_final), 205):
    samples = sequence_final[i:i+205].astype(np.float32)
    if len(samples) < 205: break # Éviter le dernier petit bloc
    
    total_energy = np.mean(samples**2)

    # Appel de la DLL C : Calcule les 8 magnitudes d'un coup !
    magnitudes = np.zeros(8, dtype=np.float32)
    lib.goertzel_run(
        samples.ctypes.data_as(ctypes.POINTER(ctypes.c_float)),
        len(samples),
        float(Fs),
        magnitudes.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
    )

    # On sépare les résultats (4 basses, 4 hautes)
    low_mags = magnitudes[:4]
    high_mags = magnitudes[4:8]

    # Trouver l'indice de la plus forte énergie
    idx_low = np.argmax(low_mags)
    idx_high = np.argmax(high_mags)
    
    best_low_freq = f_b[idx_low]
    best_high_freq = f_h[idx_high]
    
    best_low_energy = low_mags[idx_low]
    best_high_energy = high_mags[idx_high]

    # Le Grand Filtre
    is_tone = best_low_energy > (total_energy * 0.1) and best_high_energy > (total_energy * 0.1)
    
    if is_tone:
        if last_state == "silence":
            char = find_char(best_low_freq, best_high_freq)
            detector_keys.append(char)
            print(f"Appui détecté : {char} (L:{int(best_low_freq)}Hz, H:{int(best_high_freq)}Hz)")
        last_state = "touche"
    else:
        last_state = "silence"

print(f"\nSéquence complète détectée : {''.join(detector_keys)}")