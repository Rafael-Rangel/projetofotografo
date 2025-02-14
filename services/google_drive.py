import os
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carregar variáveis do .env
load_dotenv()

# Configuração do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_CREDENTIALS_PATH")
MAIN_FOLDER_ID = os.getenv("MAIN_FOLDER_ID")

# Conectar ao Google Drive
try:
    if not SERVICE_ACCOUNT_FILE:
        raise ValueError("Variável de ambiente 'GOOGLE_CREDENTIALS_PATH' não definida.")

    creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    logging.info("Conexão com Google Drive estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Erro ao conectar com Google Drive: {e}")
    raise RuntimeError("Falha na autenticação do Google Drive. Verifique as credenciais.")

# Cache para reduzir chamadas repetidas à API do Google Drive
folder_cache = {}
image_cache = {}

def get_folder_id(name, parent_id):
    """ Retorna o ID de uma pasta pelo nome dentro do Google Drive """
    try:
        if (name, parent_id) in folder_cache:
            return folder_cache[(name, parent_id)]

        query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_id}' in parents"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            folder_id = folders[0]['id']
            folder_cache[(name, parent_id)] = folder_id  # Armazena no cache
            logging.info(f"Pasta encontrada: {name} (ID: {folder_id})")
            return folder_id
        else:
            logging.warning(f"Pasta '{name}' não encontrada no Google Drive.")
            return None
    except Exception as e:
        logging.error(f"Erro ao buscar pasta '{name}': {e}")
        return None

def list_images_in_folder(folder_id):
    """ Lista todas as imagens dentro de uma pasta no Google Drive """
    try:
        if folder_id in image_cache:
            return image_cache[folder_id]

        query = f"mimeType contains 'image/' and trashed=false and '{folder_id}' in parents"
        results = service.files().list(q=query, fields="files(id, name, webContentLink)").execute()
        images = results.get('files', [])

        image_cache[folder_id] = images  # Armazena no cache
        logging.info(f"{len(images)} imagens encontradas na pasta ID {folder_id}.")
        return images
    except Exception as e:
        logging.error(f"Erro ao listar imagens na pasta {folder_id}: {e}")
        return []

def list_folders():
    """ Retorna todas as pastas dentro do Google Drive """
    try:
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields="files(id, name)"
        ).execute()
        folders = results.get("files", [])
        logging.info(f"{len(folders)} pastas encontradas no Google Drive.")
        return folders
    except Exception as e:
        logging.error(f"Erro ao listar pastas do Google Drive: {e}")
        return []
