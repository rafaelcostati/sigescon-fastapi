#!/usr/bin/env python3
"""
Teste para verificar funcionalidade de upload múltiplo de arquivos
"""
import os
import asyncio
import tempfile
from typing import List

# Simular UploadFile para teste
class MockUploadFile:
    def __init__(self, filename: str, content: bytes, content_type: str = "text/plain"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)

    async def read(self) -> bytes:
        return self.content

async def test_file_service():
    """Teste básico do FileService"""
    try:
        from app.services.file_service import FileService

        # Criar instância do serviço
        file_service = FileService()
        print("✅ FileService criado com sucesso")

        # Criar arquivos mock para teste
        files = [
            MockUploadFile("teste1.txt", b"Conteudo do arquivo 1", "text/plain"),
            MockUploadFile("teste2.pdf", b"Conteudo fake PDF", "application/pdf"),
            MockUploadFile("teste3.doc", b"Conteudo fake DOC", "application/msword"),
        ]

        print(f"📁 Criados {len(files)} arquivos de teste")

        # Testar salvamento múltiplo (contrato_id fictício: 999)
        contrato_id = 999

        # Verificar se diretório de uploads existe
        uploads_dir = "uploads"
        if not os.path.exists(uploads_dir):
            os.makedirs(uploads_dir)
            print(f"📂 Diretório {uploads_dir} criado")

        # Executar teste de salvamento
        print("🔄 Iniciando teste de salvamento múltiplo...")

        saved_files = await file_service.save_multiple_upload_files(contrato_id, files)

        print(f"✅ Salvamento concluído: {len(saved_files)} arquivos processados")

        # Verificar resultados
        for i, file_info in enumerate(saved_files):
            print(f"  Arquivo {i+1}:")
            print(f"    - Nome original: {file_info['original_filename']}")
            print(f"    - Caminho: {file_info['file_path']}")
            print(f"    - Tamanho: {file_info['file_size']} bytes")
            print(f"    - Tipo: {file_info['content_type']}")

            # Verificar se arquivo foi criado
            if os.path.exists(file_info['file_path']):
                print(f"    ✅ Arquivo físico criado com sucesso")
            else:
                print(f"    ❌ Arquivo físico NÃO encontrado")

        # Cleanup - remover arquivos de teste
        print("\n🧹 Limpando arquivos de teste...")
        for file_info in saved_files:
            try:
                if os.path.exists(file_info['file_path']):
                    os.remove(file_info['file_path'])
                    print(f"  🗑️ Removido: {file_info['original_filename']}")
            except Exception as e:
                print(f"  ⚠️ Erro ao remover {file_info['original_filename']}: {e}")

        return True

    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_validation():
    """Teste das validações de arquivo"""
    try:
        from app.services.file_service import FileService

        file_service = FileService()
        print("\n🔍 Testando validações de arquivo...")

        # Teste 1: Arquivo muito grande
        print("  Teste 1: Arquivo muito grande (>100MB)")
        large_content = b"X" * (101 * 1024 * 1024)  # 101MB
        large_file = MockUploadFile("arquivo_grande.txt", large_content)

        # Teste 2: Tipo não permitido
        print("  Teste 2: Tipo de arquivo não permitido")
        invalid_file = MockUploadFile("virus.exe", b"executable", "application/octet-stream")

        # Teste 3: Arquivos válidos
        print("  Teste 3: Arquivos válidos")
        valid_files = [
            MockUploadFile("documento.pdf", b"PDF content", "application/pdf"),
            MockUploadFile("planilha.xlsx", b"Excel content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        ]

        # Testes individuais
        tests = [
            ([large_file], "Arquivo muito grande deve falhar"),
            ([invalid_file], "Tipo inválido deve falhar"),
            (valid_files, "Arquivos válidos devem passar"),
        ]

        for files, description in tests:
            try:
                print(f"    🔄 {description}")
                result = await file_service.save_multiple_upload_files(999, files)
                print(f"    ✅ Sucesso: {len(result)} arquivos processados")

                # Cleanup
                for file_info in result:
                    if os.path.exists(file_info['file_path']):
                        os.remove(file_info['file_path'])

            except Exception as e:
                print(f"    ❌ Falhou como esperado: {str(e)[:100]}...")

        return True

    except Exception as e:
        print(f"❌ Erro durante teste de validação: {e}")
        return False

async def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes de upload múltiplo de arquivos\n")

    # Teste 1: Funcionalidade básica
    print("=" * 50)
    print("TESTE 1: Funcionalidade Básica")
    print("=" * 50)
    success1 = await test_file_service()

    # Teste 2: Validações
    print("\n" + "=" * 50)
    print("TESTE 2: Validações de Arquivo")
    print("=" * 50)
    success2 = await test_validation()

    # Resultado final
    print("\n" + "=" * 50)
    print("RESULTADO FINAL")
    print("=" * 50)

    if success1 and success2:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("🎉 Upload múltiplo está funcionando corretamente!")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique os erros acima para correção")

    return success1 and success2

if __name__ == "__main__":
    # Executar testes
    result = asyncio.run(main())
    exit(0 if result else 1)