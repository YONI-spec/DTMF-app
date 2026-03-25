import numpy as np
import scipy.io.wavfile as wav
from dtmf_utils import DTMF_number

def generate_dtmf(key,duration=0.5):
    Fs = 8000 #Frequence d'echantillonage
    #retourne un message d'erreur si l'utilisateur n'entre pas un nombre parmi ceux du dictionnaire
    if key not in DTMF_number:
        raise ValueError('Touche invalide')
    #reuperation des frequences basses(f_b) et hautes(f_h) du nombre entré
    f_b,f_h = DTMF_number[key]
    N = int(Fs*duration)
    n = np.arange(N)
    #pour transformer le signal en 16bits pour permettre l'enregistrement en wav
    facteur_de_conversion = 32767
    signal = 0.5*np.sin(2*np.pi*(f_b*n)/Fs) + np.sin(2*np.pi*(f_h*n)/Fs)
    return (signal*facteur_de_conversion).astype(np.int16)


sequence = np.concatenate([generate_dtmf(k) for k in "123"])
wav.write("sequence123.wav",8000,sequence)

#definition de la fonction de silence entre les touches

def generate_silence(duration=0.1,Fs=8000):
    #calcul du nombre d'echantillon
    N_silence = int(Fs*duration)
    #creation du tableau de silence

    silence = np.zeros(N_silence,dtype=np.int16)
    return silence

audio_segments = []

for k in "2831":
    #on genère le son de la touche et on l'ajoute 
   ton = generate_dtmf(k)
   audio_segments.append(ton)

   silence = generate_silence(duration=0.1)
   audio_segments.append(silence)

sequence_final = np.concatenate(audio_segments)

wav.write("test_sequence.wav",8000,sequence_final)
print("sequnece avec silence enregistrée")





