#!/bin/bash

echo "🔧 Atualizando pacotes do sistema..."
apt-get update && apt-get upgrade -y

echo "📦 Instalando dependências para dlib..."
apt-get install -y \
    cmake \
    build-essential \
    python3-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev

echo "✅ Dependências instaladas com sucesso!"
