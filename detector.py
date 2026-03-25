import numpy as np
from scipy.io import wavfile
from dtmf_utils import DTMF_number,f_h,f_b
from generator import sequence_final


Fs = 8000
def goertzel_filter(samples,target_freq,Fs):
    coef = 2*np.cos((2*np.pi*target_freq)/Fs)

    s_1 = 0.0
    s_2 = 0.0

    for x in samples:
        s_current = x + coef*s_1-s_2

        s_2 = s_1
        s_1 = s_current

    Energy = s_1**2 + s_2**2 - (coef*s_1*s_2) 
    return Energy

def find_char(best_low_freq,best_high_freq):
    for char,(f_b,f_h) in DTMF_number.items():
        #on verifie si on est proche des frequences cibles(avec une marge de 20HZ)
        if abs(best_low_freq-f_b) < 20 and abs(best_high_freq-f_h) < 20:
            return char
    return "?"

detector_keys = []
last_state = "silence" # au demarrage on considère qu'il y a du silence 

for i in np.arange(0,len(sequence_final),205):
    samples = sequence_final[i:i+205]
    total_energy= np.mean(samples**2) # Énergie moyenne du bloc

     #Trouver la meilleure fréquence basse et son énergie
    low_energies = {}
    for f in f_b:
       
        low_energies[f] = goertzel_filter(samples,f,Fs)
    best_low_freq = max(low_energies,key=low_energies.get)
    best_low_energy = low_energies[best_low_freq]
#Trouver la meilleure fréquence haute et son énergie
    high_energies = {}
    for f in f_h:
        high_energies[f] = goertzel_filter(samples,f,Fs)
    best_high_freq = max(high_energies,key=high_energies.get)
    best_high_energy = high_energies[best_high_freq]

    #Le Grand Filtre: est-ce que c'est une vraie touche ?
         # Seuil de détection (ex: 10% de l'énergie totale)
    is_tone = best_low_energy > (total_energy * 0.1) and best_high_energy > (total_energy * 0.1)
    if is_tone:
        if last_state == "silence":
            print(f"DEBUG: Low={best_low_freq}Hz, High={best_high_freq}Hz")
            #debut du bip
            char = find_char(best_low_freq,best_high_freq) 
            detector_keys.append(char)
            print(f"appui detecté {char}")
        last_state = "touche"
    else:
        last_state = "silence"
print(f"\nSéquence complète détectée : {''.join(detector_keys)}")

