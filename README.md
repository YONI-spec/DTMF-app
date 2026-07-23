#  Décodage DTMF robuste -- Goertzel optimisé en C/Python

**Auteur** : Jonathan AGBODRE\
**Date** : Mai 2026\
**Technologies** : C (DLL), Python (ctypes, NumPy, SciPy), Flask,
HTML/JS

------------------------------------------------------------------------

## Présentation

Ce projet implémente un décodeur de signaux DTMF (Dual-Tone
Multi-Frequency), les tonalités utilisées par les téléphones à clavier.

L'application convertit un fichier audio `.wav` contenant des tonalités
DTMF en une séquence de caractères (`0–9`, `*`, `#`, etc.). Le
traitement est basé sur l'algorithme de Goertzel implémenté en C et
exploité depuis Python via `ctypes`.

### Points principaux

-   Algorithme de Goertzel implémenté en C puis compilé en DLL.
-   Détection des faux positifs grâce à un contrôle d'équilibre
    énergétique (Twist Check).
-   Rééchantillonnage automatique à 8000 Hz et normalisation du signal.
-   API Flask avec interface Web pour l'analyse des fichiers audio et la
    visualisation des résultats.

------------------------------------------------------------------------

## Architecture

``` text
projet_dtmf/
├── detector.c
├── goertzel.dll
├── dtmf_utils.py
├── detector.py
├── dtmf_engine.py
├── app.py
├── index.html
├── requirements.txt
└── README.md
```

------------------------------------------------------------------------

## Fonctionnement

### Algorithme de Goertzel

L'algorithme calcule directement l'énergie des huit fréquences DTMF sans
effectuer une FFT complète.

Bloc de traitement :

-   Taille : 205 échantillons (\~25,6 ms à 8000 Hz)
-   Calcul des magnitudes pour les 8 fréquences normalisées DTMF

Interface C :

``` c
void goertzel_run(const float* samples, int size, float fs, float* magnitudes);
```

### Moteur Python

Le moteur :

-   appelle la DLL C ;
-   applique les seuils d'énergie ;
-   effectue le Twist Check ;
-   valide une touche après plusieurs blocs consécutifs.

Paramètres principaux :

``` python
BLOCK_SIZE = 205
min_energy = 0.005
rel_threshold = 0.15
min_duration = 3
min_silence = 2
```

### API Flask

Routes disponibles :

-   `GET /` : interface Web.
-   `POST /analyze` : analyse d'un fichier WAV et retour des résultats
    au format JSON.

------------------------------------------------------------------------

## Installation

``` bash
git clone https://github.com/YONI-spec/dtmf-decoder.git
cd dtmf-decoder
pip install -r requirements.txt
```

Compilation :

Windows

``` bash
gcc -shared -o goertzel.dll detector.c
```

Linux

``` bash
gcc -shared -fPIC -o goertzel.so detector.c
```

Exécution :

``` bash
python app.py
```

Puis ouvrir :

`http://localhost:5000`

------------------------------------------------------------------------

## Résultats

Le décodeur identifie correctement les séquences DTMF tout en limitant
les faux positifs liés au bruit, aux clics ou aux variations de niveau
grâce au Twist Check et aux seuils d'énergie.

------------------------------------------------------------------------

## Améliorations envisagées

-   Support d'autres formats audio (MP3, etc.).
-   Acquisition en temps réel depuis un microphone.
-   Optimisation SIMD de l'implémentation C.
-   Génération automatique de rapports en LaTeX.

------------------------------------------------------------------------

## Auteur

**Jonathan AGBODRE**\

