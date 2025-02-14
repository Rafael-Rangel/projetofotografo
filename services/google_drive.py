import os
import base64
import logging
import requests
from googleapiclient.discovery import build
from google.oauth2 import service_account
from dotenv import load_dotenv

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Carregar variáveis do ambiente
load_dotenv()

# Diretórios de armazenamento
STORAGE_DIR = "storage"
MODEL_DIR = "services"

# Criar diretórios se não existirem
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# Configuração do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']
GOOGLE_CREDENTIALS_BASE64 = os.getenv("GOOGLE_CREDENTIALS_BASE64")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH")

# Definir a pasta principal fixa dentro do Google Drive
FOLDER_NAME = "Fotografia_Eventos"

# Criar credenciais temporárias se necessário
if GOOGLE_CREDENTIALS_BASE64:
    try:
        credentials_json = base64.b64decode(GOOGLE_CREDENTIALS_BASE64).decode("utf-8")
        temp_credentials_path = "/tmp/credentials.json" if os.name != "nt" else os.path.join(os.getenv("TEMP"), "credentials.json")

        with open(temp_credentials_path, "w") as f:
            f.write(credentials_json)

        os.environ["GOOGLE_CREDENTIALS_PATH"] = temp_credentials_path
        GOOGLE_CREDENTIALS_PATH = temp_credentials_path
        logging.info("Credenciais do Google Drive carregadas com sucesso.")

    except Exception as e:
        logging.error(f"Erro ao decodificar credenciais Base64: {e}")
        raise RuntimeError("Falha ao carregar as credenciais do Google Drive.")

if not GOOGLE_CREDENTIALS_PATH:
    raise ValueError("A variável de ambiente 'GOOGLE_CREDENTIALS_PATH' não está definida.")

# Conectar ao Google Drive
try:
    creds = service_account.Credentials.from_service_account_file(GOOGLE_CREDENTIALS_PATH, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)
    logging.info("Conexão com Google Drive estabelecida com sucesso.")
except Exception as e:
    logging.error(f"Erro ao conectar com Google Drive: {e}")
    raise RuntimeError("Falha na autenticação do Google Drive. Verifique as credenciais.")

# Cache para evitar chamadas repetitivas ao Google Drive
folder_cache = {}
image_cache = {}

def get_folder_id(name, parent_id=None):
    """ Retorna o ID de uma pasta pelo nome dentro do Google Drive """
    try:
        if parent_id:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_id}' in parents"
        else:
            query = f"name='{name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            folder_id = folders[0]['id']
            logging.info(f"Pasta encontrada: {name} (ID: {folder_id})")
            return folder_id
        else:
            logging.warning(f"Pasta '{name}' não encontrada no Google Drive.")
            return None
    except Exception as e:
        logging.error(f"Erro ao buscar pasta '{name}': {e}")
        return None

def list_subfolders():
    """ Lista todas as subpastas dentro da pasta principal fixa """
    try:
        parent_id = get_folder_id(FOLDER_NAME)  # Pegamos o ID da pasta principal fixa
        if not parent_id:
            return {"error": f"Pasta principal '{FOLDER_NAME}' não encontrada no Google Drive."}

        query = f"mimeType='application/vnd.google-apps.folder' and trashed=false and '{parent_id}' in parents"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        subfolders = results.get("files", [])

        logging.info(f"{len(subfolders)} subpastas encontradas dentro de '{FOLDER_NAME}'.")
        return [{"id": folder["id"], "name": folder["name"]} for folder in subfolders]
    except Exception as e:
        logging.error(f"Erro ao listar subpastas: {e}")
        return []

def list_images_in_folder(folder_id):
    """ Lista todas as imagens dentro de uma subpasta no Google Drive """
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

def find_matching_images(folder_id, user_embedding, threshold=0.6):
    """ Compara os embeddings do usuário com as imagens na pasta e retorna as compatíveis """
    try:
        images = list_images_in_folder(folder_id)
        matched_images = []

        for img in images:
            img_url = img["webContentLink"]
            img_response = requests.get(img_url)
            if img_response.status_code == 200:
                img_array = bytearray(img_response.content)
                
                # Aqui você precisa chamar a função extract_embeddings para extrair os embeddings da imagem
                img_embedding = extract_embeddings(img_array)
                if img_embedding.size > 0:
                    similarity = np.dot(user_embedding, img_embedding)
                    if similarity > threshold:
                        matched_images.append({"name": img["name"], "download_link": img_url})

        logging.info(f"{len(matched_images)} imagens compatíveis encontradas.")
        return matched_images

    except Exception as e:
        logging.error(f"Erro ao comparar imagens na pasta {folder_id}: {e}")
        return []
