from fastapi import APIRouter, UploadFile, File, HTTPException
import cv2
import shutil
from pathlib import Path
from services.face_recognition import extract_embeddings
from services.faiss_search import search_similar
from services.google_drive import upload_image

# Criar o router
router = APIRouter()

# Diretório temporário
TEMP_DIR = Path("storage")
TEMP_DIR.mkdir(exist_ok=True)

@router.post("/albums/{album_id}/upload-and-match")
async def upload_and_match(album_id: str, file: UploadFile = File(...)):
    """
    Faz upload da selfie e retorna todas as imagens do álbum que contenham o rosto do usuário.
    """
    temp_path = TEMP_DIR / file.filename

    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extrair embeddings da selfie
    image = cv2.imread(str(temp_path))
    user_embedding = extract_embeddings(image)

    if user_embedding.size == 0:
        raise HTTPException(status_code=400, detail="Nenhum rosto detectado na selfie.")

    # Buscar imagens do álbum no cache FAISS
    matching_images = search_similar(user_embedding)

    return {"matching_images": matching_images}
