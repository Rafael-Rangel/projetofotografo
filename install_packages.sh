#!/bin/bash

echo "Atualizando pacotes e instalando dependências do dlib..."

# Atualiza pacotes
apt-get update && apt-get upgrade -y

# Instala dependências do dlib
apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libboost-thread-dev

echo "Dependências instaladas com sucesso!"
