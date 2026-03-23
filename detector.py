import numpy as np
from scipy.io import wavfile
from dtmf_utils import DTMF_number,f_h,f_b

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