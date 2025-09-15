# app/services/file_service.py
import aiofiles
import os
import secrets
from fastapi import UploadFile, HTTPException, status
from typing import Tuple

# Define o diretório de uploads na raiz do projeto
UPLOAD_DIRECTORY = "uploads"
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'odt', 'ods'}

class FileService:
    def __init__(self, upload_dir: str = UPLOAD_DIRECTORY):
        self.upload_dir = upload_dir
        # Garante que o diretório de uploads exista
        os.makedirs(self.upload_dir, exist_ok=True)

    def _is_allowed(self, filename: str) -> bool:
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    async def save_upload_file(self, contrato_id: int, file: UploadFile) -> Tuple[str, str, int]:
        """
        Valida e guarda um ficheiro de upload.
        Retorna (nome_original, caminho_completo, tamanho_em_bytes).
        """
        if not self._is_allowed(file.filename):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tipo de ficheiro não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Cria um subdiretório para cada contrato para manter os ficheiros organizados
        contrato_upload_folder = os.path.join(self.upload_dir, str(contrato_id))
        os.makedirs(contrato_upload_folder, exist_ok=True)

        # Cria um nome de ficheiro único para evitar conflitos
        original_filename = file.filename
        name, ext = os.path.splitext(original_filename)
        file_hash = secrets.token_hex(4)
        unique_filename = f"{name}_{file_hash}{ext}"
        
        file_path = os.path.join(contrato_upload_folder, unique_filename)

        try:
            # Escreve o ficheiro no disco de forma assíncrona
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            
            file_size = os.path.getsize(file_path)
            return original_filename, file_path, file_size
        except Exception as e:
            # Em caso de erro, remove o ficheiro parcialmente escrito se existir
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao guardar o ficheiro: {e}"
            )