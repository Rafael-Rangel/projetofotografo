import os
import cv2
import dlib
import numpy as np
import logging
from scipy.spatial import distance

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Definir caminhos para os modelos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
shape_predictor_path = os.path.join(BASE_DIR, "shape_predictor_68_face_landmarks.dat")
face_rec_model_path = os.path.join(BASE_DIR, "dlib_face_recognition_resnet_model_v1.dat")

# Carregar modelos do Dlib
try:
    detector = dlib.get_frontal_face_detector()
    shape_predictor = dlib.shape_predictor(shape_predictor_path)
    face_rec_model = dlib.face_recognition_model_v1(face_rec_model_path)
    logging.info("Modelos do Dlib carregados com sucesso!")
except Exception as e:
    logging.error(f"Erro ao carregar os modelos do Dlib: {e}")
    raise RuntimeError("Falha ao carregar os modelos de reconhecimento facial.")

def extract_embeddings(image):
    """ 
    Extrai embeddings faciais de uma imagem. 

    Retorna uma lista com os embeddings de todos os rostos detectados.
    """
    try:
        if image is None or image.shape[0] == 0 or image.shape[1] == 0:
            logging.warning("Imagem inválida ou corrompida.")
            return np.array([])

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)

        if len(faces) == 0:
            logging.info("Nenhum rosto detectado na imagem.")
            return np.array([])

        embeddings = []
        for face in faces:
            shape = shape_predictor(gray, face)
            embedding = face_rec_model.compute_face_descriptor(image, shape)
            normalized_embedding = np.array(embedding) / np.linalg.norm(embedding)
            embeddings.append(normalized_embedding)

        logging.info(f"Extraídos {len(embeddings)} embeddings da imagem.")
        return np.array(embeddings) if embeddings else np.array([])

    except Exception as e:
        logging.error(f"Erro ao extrair embeddings: {e}")
        return np.array([])

def cosine_similarity(embedding1, embedding2):
    """ Calcula similaridade cosseno entre dois embeddings """
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

def compare_embeddings(embedding1, embedding2, threshold=0.6):
    """ 
    Compara embeddings usando distância euclidiana e similaridade cosseno.

    Retorna True se os embeddings forem semelhantes.
    """
    try:
        if embedding1.size == 0 or embedding2.size == 0:
            logging.warning("Um dos embeddings está vazio!")
            return False

        euclidean_dist = distance.euclidean(embedding1, embedding2)
        cos_sim = cosine_similarity(embedding1, embedding2)

        logging.info(f"Distância Euclidiana: {euclidean_dist:.4f}, Similaridade Cosseno: {cos_sim:.4f}")

        return euclidean_dist < threshold or cos_sim > (1 - threshold)

    except Exception as e:
        logging.error(f"Erro na comparação de embeddings: {e}")
        return False
