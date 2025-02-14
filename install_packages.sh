#!/bin/bash

# Atualiza pacotes e instala dependências do dlib
apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libboost-all-dev \
    python3-pybind11 \
    python3-dev

echo "Dependências instaladas com sucesso."
