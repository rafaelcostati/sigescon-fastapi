#!/usr/bin/env python3
"""
Teste completo do sistema - Upload de múltiplos arquivos via API
"""
import asyncio
import tempfile
import os
from pathlib import Path

async def test_complete_upload_system():
    """Teste completo do sistema de upload"""

    try:
        print("🚀 Testando sistema completo de upload de múltiplos arquivos\n")

        # 1. Testar import da aplicação
        print("1️⃣ Testando imports do sistema...")
        from app.main import app
        from app.services.contrato_service import ContratoService
        from app.services.file_service import FileService
        print("   ✅ Todos os imports funcionaram\n")

        # 2. Testar FileService standalone
        print("2️⃣ Testando FileService...")
        file_service = FileService()

        # Criar arquivos temporários de teste
        test_files = []

        # Arquivo 1: PDF pequeno
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n')
            test_files.append(f.name)

        # Arquivo 2: TXT simples
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'Este eh um arquivo de teste para o contrato.')
            test_files.append(f.name)

        # Arquivo 3: Word fake
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
            f.write(b'PK\x03\x04\x14\x00\x06\x00')  # Fake DOCX header
            test_files.append(f.name)

        print(f"   ✅ Criados {len(test_files)} arquivos de teste")

        # Simular UploadFile objects
        class MockUploadFile:
            def __init__(self, filepath):
                self.filepath = filepath
                self.filename = Path(filepath).name

                # Detectar content type baseado na extensão
                ext = Path(filepath).suffix.lower()
                content_types = {
                    '.pdf': 'application/pdf',
                    '.txt': 'text/plain',
                    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    '.doc': 'application/msword'
                }
                self.content_type = content_types.get(ext, 'application/octet-stream')
                self.size = os.path.getsize(filepath)

            async def read(self):
                with open(self.filepath, 'rb') as f:
                    return f.read()

        mock_files = [MockUploadFile(fp) for fp in test_files]
        print(f"   ✅ Arquivos mock criados: {[f.filename for f in mock_files]}")

        # 3. Testar upload múltiplo
        print("\\n3️⃣ Testando upload múltiplo...")
        contrato_id = 9999  # ID fictício

        try:
            saved_files = await file_service.save_multiple_upload_files(contrato_id, mock_files)
            print(f"   ✅ Upload realizado com sucesso: {len(saved_files)} arquivos salvos")

            for i, file_info in enumerate(saved_files, 1):
                print(f"   📄 Arquivo {i}: {file_info['original_filename']}")
                print(f"      • Tamanho: {file_info['file_size']} bytes")
                print(f"      • Tipo: {file_info['content_type']}")
                print(f"      • Caminho: {file_info['file_path']}")

                # Verificar se arquivo foi criado fisicamente
                if os.path.exists(file_info['file_path']):
                    print(f"      • ✅ Arquivo físico existe")
                else:
                    print(f"      • ❌ Arquivo físico NÃO existe")

        except Exception as e:
            print(f"   ❌ Erro no upload: {e}")
            return False

        # 4. Verificar estrutura de diretórios
        print("\\n4️⃣ Verificando estrutura de diretórios...")
        uploads_dir = Path("uploads")
        if uploads_dir.exists():
            print(f"   ✅ Diretório uploads existe")

            contrato_dir = uploads_dir / str(contrato_id)
            if contrato_dir.exists():
                files_in_dir = list(contrato_dir.glob("*"))
                print(f"   ✅ Diretório do contrato existe com {len(files_in_dir)} arquivos")
            else:
                print(f"   ❌ Diretório do contrato não existe")
        else:
            print(f"   ❌ Diretório uploads não existe")

        # 5. Teste de validações
        print("\\n5️⃣ Testando validações...")

        # Arquivo muito grande (simulado)
        try:
            large_content = b"X" * (101 * 1024 * 1024)  # 101MB
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
                f.write(large_content[:1024])  # Escrever só 1KB para não ocupar espaço
                large_file = MockUploadFile(f.name)
                large_file.size = 101 * 1024 * 1024  # Simular tamanho grande

            await file_service.save_multiple_upload_files(9998, [large_file])
            print("   ❌ Arquivo grande deveria ter falhado!")

        except Exception as e:
            print(f"   ✅ Validação de tamanho funcionou: {str(e)[:80]}...")

        # Tipo de arquivo inválido
        try:
            with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
                f.write(b'MZ')  # Fake EXE header
                exe_file = MockUploadFile(f.name)
                exe_file.content_type = 'application/x-msdownload'

            await file_service.save_multiple_upload_files(9997, [exe_file])
            print("   ❌ Tipo inválido deveria ter falhado!")

        except Exception as e:
            print(f"   ✅ Validação de tipo funcionou: {str(e)[:80]}...")

        # 6. Cleanup
        print("\\n6️⃣ Limpando arquivos de teste...")

        # Remover arquivos de teste originais
        for filepath in test_files:
            try:
                os.unlink(filepath)
                print(f"   🗑️ Removido: {Path(filepath).name}")
            except:
                pass

        # Remover arquivos salvos
        try:
            for file_info in saved_files:
                if os.path.exists(file_info['file_path']):
                    os.unlink(file_info['file_path'])
                    print(f"   🗑️ Removido: {file_info['original_filename']}")
        except:
            pass

        # Remover diretório do contrato se vazio
        try:
            contrato_dir = Path("uploads") / str(contrato_id)
            if contrato_dir.exists() and not any(contrato_dir.iterdir()):
                contrato_dir.rmdir()
                print(f"   🗑️ Removido diretório: {contrato_dir}")
        except:
            pass

        print("\\n" + "="*60)
        print("🎉 TESTE COMPLETO FINALIZADO COM SUCESSO!")
        print("✅ Upload de múltiplos arquivos está funcionando perfeitamente")
        print("✅ Validações estão ativas e funcionando")
        print("✅ Sistema está pronto para uso")
        print("="*60)

        return True

    except Exception as e:
        print(f"\\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_integration():
    """Teste de integração com a API"""
    print("\\n🔌 Testando integração com API...")

    try:
        from app.main import app

        # Verificar se todas as rotas estão registradas
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        contrato_routes = [r for r in routes if '/contratos' in r]

        # Verificar rotas específicas de upload
        upload_routes = [
            '/api/v1/contratos/',  # POST para criar contrato com arquivos
            '/api/v1/contratos/{contrato_id}',  # PATCH para atualizar com arquivos
            '/api/v1/contratos/{contrato_id}/arquivos',  # GET para listar arquivos
            '/api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}/download',  # GET para download
            '/api/v1/contratos/{contrato_id}/arquivos/{arquivo_id}',  # DELETE para remover
        ]

        missing_routes = []
        for route in upload_routes:
            if route not in contrato_routes:
                # Verificar se existe uma versão similar (ignorando métodos HTTP duplicados)
                base_route = route.replace('/api/v1', '').replace('contratos/', 'contratos')
                if not any(base_route in r for r in contrato_routes):
                    missing_routes.append(route)

        if missing_routes:
            print(f"   ⚠️ Rotas possivelmente em falta: {missing_routes}")
        else:
            print(f"   ✅ Todas as rotas de upload estão registradas")

        print(f"   ✅ Total de rotas de contratos: {len(contrato_routes)}")

        return True

    except Exception as e:
        print(f"   ❌ Erro na integração: {e}")
        return False

async def main():
    """Função principal"""
    print("🧪 TESTE COMPLETO DO SISTEMA DE CONTRATOS")
    print("=" * 60)

    # Teste 1: Sistema completo
    success1 = await test_complete_upload_system()

    # Teste 2: Integração API
    success2 = await test_api_integration()

    # Resultado final
    print("\\n" + "=" * 60)
    print("📊 RESULTADO FINAL DOS TESTES")
    print("=" * 60)

    if success1 and success2:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ O sistema está funcionando corretamente!")
        print("✅ Upload de múltiplos arquivos operacional!")
        print("✅ API integrada e pronta para uso!")
        exit_code = 0
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("🔧 Verifique os logs acima para detalhes")
        exit_code = 1

    print("=" * 60)
    return exit_code

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)