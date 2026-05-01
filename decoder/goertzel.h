#ifndef GOERTZEL_H
#define GOERTZEL_H

// Fonction principale : traite un buffer d'échantillons et remplit le tableau des 8 magnitudes
// buffer : pointeur vers les échantillons (float)
// size : nombre d'échantillons dans le bloc
// fs : fréquence d'échantillonnage (ex: 8000.0)
// magnitudes : tableau de sortie de taille 8
void goertzel_run(float* buffer, int size, float fs, float* magnitudes);

#endif  