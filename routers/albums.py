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
    Retorna todas as subpastas (álbuns) disponíveis dentro da pasta principal no Google Drive.
    """
    try:
        albums = list_folders()

        if not albums:
            logging.warning("Nenhum álbum encontrado no Google Drive.")
            raise HTTPException(status_code=404, detail="Nenhum álbum encontrado.")

        logging.info(f"{len(albums)} álbuns encontrados no Google Drive.")

        # Estruturando a resposta no formato adequado
        return {"total_albums": len(albums), "albums": albums}

    except HTTPException:
        raise  # Permite que exceções HTTP personalizadas sejam propagadas corretamente
    except Exception as e:
        logging.error(f"Erro ao listar álbuns: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao buscar álbuns.")
