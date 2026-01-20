import numpy as np
import scipy.io.wavfile as wav
#definition d'un dictionnaire des touches avec leurs frequences de groetzel respectifs associés
DTMF_number = {
    '1': (697, 1209), '2' :(697, 1336), '3' : (697, 1447),
    '4': (770, 1209), '5' :(770, 1336), '5' : (770, 1447),
    '7': (852, 1209), '8' :(852, 1336), '9' : (852, 1447),
    '*': (941, 1209), '0' :(941,1336),  '#' : (941, 1447)
 }

def generate_dmf(key,duration=0.5):
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


sequence = np.concatenate([generate_dmf(k) for k in "123"])
wav.write("sequence123.wav",8000,sequence)