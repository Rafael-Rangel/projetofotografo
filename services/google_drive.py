import os
import base64
import logging
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carregar variáveis do .env
load_dotenv()

# Configuração do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

# Variável de ambiente com a credencial base64
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

# Criar credenciais temporárias se necessário
if GOOGLE_CREDENTIALS_BASE64:
    try:
        credentials_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8")

        # Definir o caminho temporário para armazenar as credenciais
        temp_credentials_path = "/tmp/credentials.json"  # Para Linux/Render
        if os.name == "nt":  # Se for Windows
            temp_credentials_path = os.path.join(os.getenv("TEMP"), "credentials.json")

        # Salvar credenciais no arquivo temporário
        with open(temp_credentials_path, "w") as f:
            f.write(credentials_json)

        # Atualizar variável de ambiente para apontar para o novo arquivo
        os.environ["GOOGLE_CREDENTIALS_PATH"] = temp_credentials_path
        GOOGLE_CREDENTIALS_PATH = temp_credentials_path
        logging.info("Credenciais do Google Drive decodificadas e salvas com sucesso.")

    except Exception as e:
        logging.error(f"Erro ao decodificar credenciais Base64: {e}")
        raise RuntimeError("Falha ao carregar as credenciais do Google Drive. Verifique a variável GOOGLE_CREDENTIALS_BASE64.")

# Verificar se a variável `GOOGLE_CREDENTIALS_PATH` está definida corretamente
if not GOOGLE_CREDENTIALS_PATH:
    raise ValueError("Variável de ambiente 'GOOGLE_CREDENTIALS_PATH' não definida.")

# Conectar ao Google Drive
try:
    creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
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
