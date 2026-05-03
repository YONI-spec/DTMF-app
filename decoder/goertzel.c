#define _USE_MATH_DEFINES
#include <math.h>
#include "goertzel.h"


void goertzel_run(float* buffer,int size,float fs,float* magnitudes){
    float targets_freq[8] = {697, 770, 851, 941, 1209, 1336, 1447, 1633};

    for (int i=0 ; i <8;i++){

    
        float f = targets_freq[i];
        // 1. Pré-calcul du coefficient pour cette fréquence
        float omega = (2.0f* M_PI*f)/fs;
        float coeff = 2.0f * cosf(omega);
        // 2. Initialisation des états
        float s_0 = 0.0f, s_1 = 0.0f, s_2 = 0.0f;

        // 3. Boucle sur les échantillons
        for (int n = 0; n < size; n++){
            s_0 = buffer[n] + (coeff*s_1) - s_2;
            s_2 = s_1;
            s_1 = s_0;
           
        }
         // 4. Calcul de la magnitude finale (UNE SEULE FOIS après la boucle n)
        magnitudes[i] = (s_1 * s_1) + (s_2 * s_2) - (coeff * s_1 * s_2);
    }

}