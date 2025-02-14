from fastapi import FastAPI, File, UploadFile, HTTPException
from routers import albums, images
import shutil
import cv2
import numpy as np
import os
import requests
import logging
from services.face_recognition import extract_embeddings
from services.google_drive import get_folder_id, list_images_in_folder, MAIN_FOLDER_ID

app = FastAPI()

# Registrar os módulos de rotas
app.include_router(albums.router, prefix="/api", tags=["Albums"])
app.include_router(images.router, prefix="/api", tags=["Images"])

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Pasta temporária para armazenar imagens
STORAGE_DIR = "storage"
os.makedirs(STORAGE_DIR, exist_ok=True)

# Cache para armazenar embeddings de imagens do Drive (evita reprocessamento)
embeddings_cache = {}

def cosine_similarity(embedding1, embedding2):
    """Calcula similaridade por cosseno entre dois embeddings."""
    return np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))

@app.post("/upload-selfie/")
async def upload_selfie(file: UploadFile = File(...), event: str = "Casamento", month_year: str = "02-2025"):
    """
    Recebe uma selfie, busca imagens correspondentes no Google Drive e retorna as correspondências.
    """
    try:
        # Salvar selfie temporariamente
        temp_path = os.path.join(STORAGE_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Verificar se a imagem foi carregada corretamente
        image = cv2.imread(temp_path)
        if image is None:
            raise HTTPException(status_code=400, detail="Erro ao carregar a selfie. Formato inválido ou corrompido.")

        # Extrair embeddings da selfie
        selfie_embeddings = extract_embeddings(image)
        if selfie_embeddings.size == 0:
            raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")

        # Buscar a pasta correspondente no Google Drive
        category_id = get_folder_id(event, MAIN_FOLDER_ID)
        if not category_id:
            logging.warning(f"Categoria '{event}' não encontrada no Google Drive.")
            return {"error": f"Categoria '{event}' não encontrada."}

        folder_id = get_folder_id(f"{event} {month_year}", category_id)
        if not folder_id:
            logging.warning(f"Nenhuma subpasta encontrada para '{event} {month_year}'.")
            return {"error": f"Nenhuma subpasta encontrada para '{event} {month_year}'."}

        # Listar imagens da pasta
        images = list_images_in_folder(folder_id)
        if not images:
            logging.warning(f"Nenhuma imagem encontrada na pasta '{event} {month_year}'.")
            return {"error": f"Nenhuma imagem encontrada na pasta '{event} {month_year}'."}

        # Comparar selfies com imagens do Drive
        matched_images = []
        for img in images:
            img_id = img["id"]
            img_url = img["webContentLink"]

            # Verificar se a imagem já tem embeddings armazenados no cache
            if img_id not in embeddings_cache:
                img_response = requests.get(img_url)
                if img_response.status_code != 200:
                    logging.error(f"Erro ao baixar imagem {img['name']}")
                    continue

                img_array = np.asarray(bytearray(img_response.content), dtype=np.uint8)
                img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                # Extraindo embeddings
                img_embeddings = extract_embeddings(img_cv)
                if img_embeddings.size == 0:
                    logging.warning(f"Sem rosto detectado na imagem {img['name']}.")
                    continue
                
                embeddings_cache[img_id] = img_embeddings  # Salvar no cache
            else:
                img_embeddings = embeddings_cache[img_id]

            # Comparar embeddings usando similaridade cosseno
            similarity = cosine_similarity(selfie_embeddings, img_embeddings)
            if similarity > 0.6:  # Limiar de similaridade
                matched_images.append({"name": img["name"], "download_link": img_url})

        logging.info(f"Processo finalizado. {len(matched_images)} imagens correspondentes encontradas.")
        return {"message": "Selfie processada com sucesso", "matched_images": matched_images}

    except Exception as e:
        logging.error(f"Erro no processamento da selfie: {e}")
        return {"error": str(e)}
