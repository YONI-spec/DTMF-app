# Nom de la bibliothèque de sortie
TARGET = goertzel.so

# Compilateur et options
CC = gcc
CFLAGS = -Wall -Wextra -O2 -fPIC
LDFLAGS = -shared
LDLIBS = -lm

# Fichiers sources
SRC = goertzel.c

# Règle par défaut
all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(LDFLAGS) -o $@ $^ $(LDLIBS)

# Nettoyage des fichiers générés
clean:
	rm -f $(TARGET)