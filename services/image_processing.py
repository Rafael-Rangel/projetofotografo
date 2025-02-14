import cv2
import imghdr
import logging

# Configuração de logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def validate_image(image_path):
    """
    Valida se a imagem carregada é válida, possui conteúdo e está em um formato suportado.
    
    Parâmetros:
        image_path (str): Caminho do arquivo da imagem.
    
    Retorno:
        bool: True se a imagem for válida, False caso contrário.
    """
    try:
        # Verificar se o formato é suportado
        valid_formats = {"jpeg", "png", "jpg"}
        file_format = imghdr.what(image_path)

        if file_format not in valid_formats:
            logging.warning(f"Formato de imagem inválido: {file_format}")
            return False

        # Carregar a imagem com OpenCV
        image = cv2.imread(image_path)

        # Verificar se a imagem foi carregada corretamente
        if image is None or image.shape[0] == 0 or image.shape[1] == 0:
            logging.warning("Imagem inválida ou corrompida.")
            return False

        # Verificar número de canais (RGB ou Grayscale)
        if len(image.shape) == 3 and image.shape[2] in [1, 3]:
            return True
        elif len(image.shape) == 2:  # Imagem grayscale válida
            return True
        else:
            logging.warning("Imagem possui formato desconhecido.")
            return False

    except Exception as e:
        logging.error(f"Erro ao validar imagem: {e}")
        return False
