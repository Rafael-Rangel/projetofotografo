from fastapi import APIRouter, HTTPException
from services.google_drive import list_folders
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Criando o router
router = APIRouter()

@router.get("/albums")
async def get_albums():
    """
    Retorna todas as pastas (álbuns) disponíveis no Google Drive.
    """
    try:
        albums = list_folders()

        if not albums:
            logging.warning("Nenhum álbum encontrado no Google Drive.")
            raise HTTPException(status_code=404, detail="Nenhum álbum encontrado.")

        logging.info(f"{len(albums)} álbuns encontrados no Google Drive.")
        return {"albums": albums}

    except Exception as e:
        logging.error(f"Erro ao listar álbuns: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar álbuns.")
