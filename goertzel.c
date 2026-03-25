#include "goertzel.h"
#define _USE_MATH_DEFINES
#include <math.h>


void goertzel_run(float* buffer,int size, float fs, float* magnitudes){
    float target_freq[7]={697, 770, 852, 941, 1209, 1336, 1477,};
    for(int i = 0; i<7; i++){
        float f = target_freq[i];
        //precalcul du coefficient
        float omega = (2.0f * M_PI * f)/fs;
        float coeff = 2.0f * cosf(omega);

        //initialisation des états
        float s_0 = 0.0f,s_1 = 0.0f,s_2 = 0.0f;

        //boucle sur les echantillons
        for (int n = 0;n < size;n++){
            s_0 = buffer[n] + (coeff * s_1) - s_2;
            s_2 = s_1;
            s_1 = s_0;
            
        }

        magnitudes[i] = (s_1 * s_1) + (s_2 * s_2) - (coeff * s_1 * s_2);
    }

}