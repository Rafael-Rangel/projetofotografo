import faiss
import numpy as np
import os
import pickle
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuração do índice FAISS
INDEX_FILE = "storage/faiss_index.bin"
MAP_FILE = "storage/image_map.pkl"
DIMENSIONS = 128  # Dimensão dos embeddings faciais

# Criar pasta de armazenamento se não existir
os.makedirs("storage", exist_ok=True)

# Inicializar índice FAISS
def initialize_faiss():
    global index, image_map
    if os.path.exists(INDEX_FILE) and os.path.exists(MAP_FILE):
        logging.info("Carregando índice FAISS do disco...")
        index = faiss.read_index(INDEX_FILE)
        with open(MAP_FILE, "rb") as f:
            image_map = pickle.load(f)
    else:
        logging.info("Criando novo índice FAISS...")
        index = faiss.IndexFlatL2(DIMENSIONS)
        image_map = {}

initialize_faiss()

def save_faiss():
    """ Salva o índice FAISS e o mapeamento em disco """
    faiss.write_index(index, INDEX_FILE)
    with open(MAP_FILE, "wb") as f:
        pickle.dump(image_map, f)
    logging.info("Índice FAISS salvo com sucesso.")

def add_embedding(image_id, embedding):
    """ Adiciona um embedding ao índice FAISS """
    try:
        embedding = np.array(embedding).astype("float32").reshape(1, -1)
        
        if embedding.shape[1] != DIMENSIONS:
            raise ValueError(f"Embedding inválido. Esperado {DIMENSIONS} dimensões, recebido {embedding.shape[1]}.")

        index.add(embedding)
        image_map[index.ntotal - 1] = image_id  # Mapeia o ID da imagem para a posição no FAISS
        
        save_faiss()  # Salva o estado atualizado
        logging.info(f"Embedding adicionado para {image_id}")

    except Exception as e:
        logging.error(f"Erro ao adicionar embedding: {e}")

def search_similar(embedding, top_k=5):
    """ Busca as K imagens mais semelhantes no índice FAISS """
    try:
        embedding = np.array(embedding).astype("float32").reshape(1, -1)
        
        if embedding.shape[1] != DIMENSIONS:
            raise ValueError(f"Embedding inválido. Esperado {DIMENSIONS} dimensões, recebido {embedding.shape[1]}.")

        if index.ntotal == 0:
            logging.warning("Nenhum embedding no índice FAISS ainda.")
            return []

        distances, indices = index.search(embedding, top_k)
        similar_images = [image_map[i] for i in indices[0] if i in image_map]

        logging.info(f"Busca FAISS concluída. {len(similar_images)} imagens correspondentes encontradas.")
        return similar_images

    except Exception as e:
        logging.error(f"Erro na busca FAISS: {e}")
        return []

