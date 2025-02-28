import os
from pathlib import Path
import logging
import requests

MODEL_URL = "https://example.com/shape_predictor_68_face_landmarks.dat"  # Substitua pela URL real
MODEL_PATH = "services/shape_predictor_68_face_landmarks.dat"

if not os.path.exists(MODEL_PATH):
    print("Baixando modelo de reconhecimento facial...")
    response = requests.get(MODEL_URL, stream=True)
    with open(MODEL_PATH, "wb") as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print("Download concluído.")



# Definir caminho base do projeto (ajustável por variável de ambiente)
BASE_DIR = Path(os.getenv("BASE_DIR", Path(__file__).resolve().parent))

# Diretório para armazenar arquivos temporários (ajustável)
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", BASE_DIR / "storage"))
LOG_DIR = Path(os.getenv("LOG_DIR", BASE_DIR / "logs"))

# Criar diretórios se não existirem
try:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.info(f"Diretórios configurados: {STORAGE_DIR}, {LOG_DIR}")
except Exception as e:
    logging.error(f"Erro ao criar diretórios: {e}")

# Tamanho máximo para arquivos de imagem (ajustável por variável de ambiente)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 5))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024  # Convertendo para bytes

# Configuração avançada de logs
LOG_FILE = LOG_DIR / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),  # Salvar logs no arquivo app.log
        logging.StreamHandler()  # Exibir logs no terminal
    ]
)

logging.info("Configuração de diretórios e logs concluída.")
