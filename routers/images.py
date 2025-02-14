from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import shutil
import numpy as np
from pathlib import Path
from services.face_recognition import extract_embeddings
from services.faiss_search import search_similar
from services.google_drive import upload_image, list_images_in_folder
import requests
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Criar o router
router = APIRouter()

# Diretório temporário
TEMP_DIR = Path("storage")
TEMP_DIR.mkdir(exist_ok=True)

@router.post("/albums/{album_id}/upload-and-match")
async def upload_and_match(album_id: str, file: UploadFile = File(...)):
    """
    Faz upload da selfie no Google Drive (opcional), realiza o reconhecimento facial
    e retorna todas as imagens do álbum que contenham o rosto do usuário.
    Após o processamento, a selfie é removida do servidor.
    """
    temp_path = TEMP_DIR / file.filename

    try:
        # Salvar temporariamente a selfie enviada
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extrair embeddings da selfie
        image = cv2.imread(str(temp_path))
        user_embedding = extract_embeddings(image)

        if user_embedding.size == 0:
            raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")

        # Fazer upload da selfie para o Google Drive (opcional)
        uploaded_file = upload_image(album_id, str(temp_path), file.filename)

        if not uploaded_file:
            logging.error("Erro ao fazer upload da selfie para o Google Drive.")
            raise HTTPException(status_code=500, detail="Erro ao salvar selfie no Google Drive.")

        logging.info(f"Selfie enviada para o Google Drive: {uploaded_file['webViewLink']}")

        # Buscar imagens do álbum para comparação
        images = list_images_in_folder(album_id)

        if not images:
            raise HTTPException(status_code=404, detail="Nenhuma imagem encontrada no álbum.")

        matching_images = []
        for img in images:
            img_url = img["webContentLink"]
            img_response = requests.get(img_url)

            if img_response.status_code == 200:
                img_array = np.asarray(bytearray(img_response.content), dtype=np.uint8)
                img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                img_embedding = extract_embeddings(img_cv)

                if img_embedding.size > 0:
                    if search_similar(user_embedding):
                        matching_images.append({"name": img["name"], "download_link": img_url})

        return {"matching_images": matching_images}

    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        logging.error(f"Erro ao processar a selfie: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar a imagem.")
    finally:
        # Remover o arquivo temporário após processamento
        try:
            if temp_path.exists():
                temp_path.unlink()
                logging.info(f"Arquivo temporário removido: {temp_path}")
        except Exception as e:
            logging.error(f"Erro ao remover arquivo temporário {temp_path}: {e}")
