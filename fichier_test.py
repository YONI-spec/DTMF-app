import numpy as np
import scipy.io.wavfile as wav

# PARAMÈTRES
Fs = 8000          # Fréquence d'échantillonnage (8 kHz)
T = 0.5            # Durée (0.5 seconde)
N = int(Fs * T)    # Nombre d'échantillons (4000)
n = np.arange(N)   # Indices d'échantillons
A = 1              # Amplitude
f_low = 770        # Fréquence basse (pour le '5')
f_high = 1336      # Fréquence haute (pour le '5')
scale_factor = 32767 # Facteur de mise à l'échelle pour 16-bit

#  1. GÉNÉRATION DU SIGNAL DTMF
signal = A * np.sin(2 * np.pi * f_low * n / Fs) + A * np.sin(2 * np.pi * f_high * n / Fs)

#  2. PRÉPARATION DU WAV (Scaling et Conversion int16)
audio_data = (signal * scale_factor).astype(np.int16)

#  3. SAUVEGARDE
wav.write("tonalite_5.wav", Fs, audio_data)
print(" Fichier sauvegardé: tonalite_5.wav")