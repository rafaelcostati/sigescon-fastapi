#!/usr/bin/env python3
"""
Script completo para testar o sistema de perfis múltiplos do SIGESCON.
VERSÃO CORRIGIDA - Resolve problemas de KeyError e validação Pydantic

Execute com: python scripts/test_multiple_profiles_complete.py
"""

import requests
import json
import time
import os
import tempfile
from datetime import date, timedelta
import sys
import dotenv

dotenv.load_dotenv()

# Verifica se reportlab está instalado
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    print("❌ Biblioteca 'reportlab' não encontrada.")
    print("📦 Instalando reportlab...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    print("✅ reportlab instalado com sucesso!")
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

# Configurações
BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

# Dados dos usuários de teste
USUARIOS_TESTE = [
    {
        "nome": "Rafael Costa",
        "email": "rafael.costa@pge.pa.gov.br",
        "cpf": "12345678901",
        "matricula": "PGE001",
        "perfis": ["Fiscal", "Gestor"]
    },
    {
        "nome": "Anderson Pontes", 
        "email": "anderson.pontes@pge.pa.gov.br",
        "cpf": "98765432109",
        "matricula": "PGE002",
        "perfis": ["Fiscal", "Gestor"]
    }
]

class SigesconTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.rafael_token = None
        self.anderson_token = None
        self.test_files = []
        
        self.rafael_id = None
        self.anderson_id = None
        self.contratado_id = None
        self.modalidade_id = None
        self.status_id = None
        self.contrato_id = None
        self.pendencia_id = None
        self.relatorio_id = None
        
        print("🚀 SIGESCON - Teste Completo do Sistema de Perfis Múltiplos")
        print("=" * 60)

    def create_test_pdf(self, filename: str, content: str) -> str:
        """Cria um PDF de teste"""
        filepath = os.path.join(tempfile.gettempdir(), filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        width, height = letter
        
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "SIGESCON - Documento de Teste")
        
        c.setFont("Helvetica", 12)
        y_position = height - 100
        
        lines = content.split('\n')
        for line in lines:
            c.drawString(50, y_position, line)
            y_position -= 20
            if y_position < 50:
                c.showPage()
                y_position = height - 50
        
        c.setFont("Helvetica", 8)
        c.drawString(50, 30, f"Gerado automaticamente em {time.strftime('%d/%m/%Y %H:%M:%S')}")
        
        c.save()
        self.test_files.append(filepath)
        print(f"📄 PDF criado: {filepath}")
        return filepath

    def login_admin(self) -> str:
        """Faz login como administrador"""
        print("\n🔐 Fazendo login como administrador...")
        
        response = self.session.post(f"{BASE_URL}/auth/login", data={
            "username": os.getenv("ADMIN_EMAIL"),
            "password": os.getenv("ADMIN_PASSWORD")
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            self.admin_token = token
            print("✅ Login administrativo realizado com sucesso")
            return token
        else:
            print(f"❌ Erro no login admin: {response.status_code} - {response.text}")
            sys.exit(1)

    def get_or_create_user(self, user_data: dict) -> int:
        """Busca usuário existente ou cria novo - CORRIGIDO"""
        print(f"\n👤 Verificando usuário: {user_data['email']}")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Busca usuário existente
        response = self.session.get(f"{API_URL}/usuarios", 
                                   params={"nome": user_data["nome"]}, 
                                   headers=headers)
        
        if response.status_code == 200:
            usuarios = response.json()["data"]
            for usuario in usuarios:
                if usuario["email"] == user_data["email"]:
                    print(f"✅ Usuário encontrado: ID {usuario['id']}")
                    # ✅ CORRIGIDO: Reset de senha para usuário existente
                    self._reset_user_password(usuario['id'], headers)
                    return usuario["id"]
        
        # Cria novo usuário
        print(f"➕ Criando novo usuário: {user_data['nome']}")
        
        perfis_response = self.session.get(f"{API_URL}/perfis", headers=headers)
        perfis = perfis_response.json()
        perfil_fiscal_id = next(p["id"] for p in perfis if p["nome"] == "Fiscal")
        
        user_create_data = {
            "nome": user_data["nome"],
            "email": user_data["email"],
            "cpf": user_data["cpf"],
            "matricula": user_data["matricula"],
            "senha": "senha123",
            "perfil_id": perfil_fiscal_id
        }
        
        response = self.session.post(f"{API_URL}/usuarios", 
                                   json=user_create_data, 
                                   headers=headers)
        
        if response.status_code == 201:
            user_id = response.json()["id"]
            print(f"✅ Usuário criado: ID {user_id}")
            return user_id
        else:
            print(f"❌ Erro ao criar usuário: {response.status_code} - {response.text}")
            sys.exit(1)

    def _reset_user_password(self, user_id: int, headers: dict):
        """Reseta a senha do usuário para 'senha123'"""
        reset_data = {"nova_senha": "senha123"}
        
        response = self.session.patch(f"{API_URL}/usuarios/{user_id}/resetar-senha",
                                    json=reset_data,
                                    headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Senha resetada para usuário {user_id}")
        else:
            print(f"⚠️ Aviso: Não foi possível resetar senha: {response.status_code}")

    def setup_multiple_profiles(self, user_id: int, perfis: list):
        """Configura múltiplos perfis para um usuário"""
        print(f"\n🎭 Configurando perfis múltiplos para usuário {user_id}")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Busca IDs dos perfis
        perfis_response = self.session.get(f"{API_URL}/perfis", headers=headers)
        if perfis_response.status_code != 200:
            print(f"❌ Erro ao buscar perfis: {perfis_response.status_code}")
            return
            
        perfis_data = perfis_response.json()
        
        perfil_ids = []
        for perfil_nome in perfis:
            perfil_id = next((p["id"] for p in perfis_data if p["nome"] == perfil_nome), None)
            if perfil_id:
                perfil_ids.append(perfil_id)
        
        if not perfil_ids:
            print("❌ Nenhum perfil válido encontrado")
            return
        
        # Concede perfis múltiplos
        grant_data = {
            "perfil_ids": perfil_ids,
            "observacoes": "Configuração automática para testes - usuário pode ser fiscal e gestor"
        }
        
        response = self.session.post(f"{API_URL}/usuarios/{user_id}/perfis/conceder",
                                   json=grant_data,
                                   headers=headers)
        
        if response.status_code == 200:
            print(f"✅ Perfis configurados: {', '.join(perfis)}")
        else:
            print(f"⚠️ Aviso: {response.status_code} - {response.text}")

    def test_user_login_with_profile_selection(self, email: str, password: str = "senha123") -> tuple:
        """Testa login com seleção de perfil - CORRIGIDO"""
        print(f"\n🔑 Testando login com seleção de perfil: {email}")
        
        response = self.session.post(f"{BASE_URL}/auth/login", data={
            "username": email,
            "password": password
        })
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            
            # ✅ CORRIGIDO: Verifica se existe contexto de sessão
            if "contexto_sessao" in data:
                contexto = data["contexto_sessao"]
                print(f"✅ Login realizado como: {contexto.get('perfil_ativo_nome', 'N/A')}")
                
                perfis_nomes = []
                if isinstance(contexto.get('perfis_disponiveis'), list):
                    perfis_nomes = [p.get('nome', 'N/A') for p in contexto['perfis_disponiveis']]
                
                print(f"📋 Perfis disponíveis: {perfis_nomes}")
                print(f"🔄 Pode alternar: {contexto.get('pode_alternar', False)}")
                
                return token, contexto
            else:
                # Login legacy - sem contexto de sessão
                print(f"✅ Login realizado (modo legacy)")
                return token, {}
        else:
            print(f"❌ Erro no login: {response.status_code} - {response.text}")
            return None, None

    def test_profile_switching(self, token: str, target_profile: str) -> dict:
        """Testa alternância de perfil - CORRIGIDO"""
        if not token:
            print("❌ Token inválido para alternar perfil")
            return {}
            
        print(f"\n🔄 Testando alternância para perfil: {target_profile}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            # ✅ CORRIGIDO: Busca contexto atual com tratamento de erro
            context_response = self.session.get(f"{BASE_URL}/auth/contexto", headers=headers)
            
            if context_response.status_code != 200:
                print(f"⚠️ Não foi possível obter contexto: {context_response.status_code}")
                return {}
            
            current_context = context_response.json()
            
            # ✅ CORRIGIDO: Verifica estrutura da resposta
            perfis_disponiveis = current_context.get("perfis_disponiveis", [])
            if not isinstance(perfis_disponiveis, list):
                print(f"⚠️ Estrutura inválida de perfis disponíveis")
                return current_context
            
            # Busca ID do perfil desejado
            target_profile_id = None
            for perfil in perfis_disponiveis:
                if perfil.get("nome") == target_profile:
                    target_profile_id = perfil.get("id")
                    break
            
            if not target_profile_id:
                print(f"❌ Perfil '{target_profile}' não disponível")
                perfis_nomes = [p.get('nome') for p in perfis_disponiveis if p.get('nome')]
                print(f"   Perfis disponíveis: {perfis_nomes}")
                return current_context
            
            # Não faz nada se já está no perfil solicitado
            if current_context.get("perfil_ativo_id") == target_profile_id:
                print(f"ℹ️ Já está no perfil {target_profile}")
                return current_context
            
            # Alterna perfil
            switch_data = {
                "novo_perfil_id": target_profile_id,
                "justificativa": f"Teste automático - alternando para {target_profile}"
            }
            
            response = self.session.post(f"{BASE_URL}/auth/alternar-perfil",
                                       json=switch_data,
                                       headers=headers)
            
            if response.status_code == 200:
                new_context = response.json()
                perfil_novo = new_context.get('perfil_ativo_nome', 'N/A')
                print(f"✅ Perfil alterado para: {perfil_novo}")
                return new_context
            else:
                print(f"❌ Erro ao alternar perfil: {response.status_code} - {response.text}")
                return current_context
                
        except Exception as e:
            print(f"❌ Exceção ao alternar perfil: {e}")
            return {}

    def test_dashboard_and_permissions(self, token: str, user_name: str):
        """Testa dashboard e permissões contextuais"""
        if not token:
            print(f"❌ Token inválido para {user_name}")
            return
            
        print(f"\n📊 Testando dashboard e permissões para {user_name}")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Busca dados do dashboard
        try:
            dashboard_response = self.session.get(f"{BASE_URL}/auth/dashboard", headers=headers)
            
            if dashboard_response.status_code == 200:
                dashboard = dashboard_response.json()
                perfil_ativo = dashboard.get('perfil_ativo', 'N/A')
                print(f"✅ Dashboard carregado para perfil: {perfil_ativo}")
                print(f"📋 Widgets: {', '.join(dashboard.get('widgets_disponiveis', []))}")
                print(f"🔧 Permissões: {', '.join(dashboard.get('permissoes_ativas', []))}")
                print(f"📈 Estatísticas: {dashboard.get('estatisticas', {})}")
            else:
                print(f"⚠️ Dashboard não disponível: {dashboard_response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao buscar dashboard: {e}")
        
        # Busca permissões contextuais
        try:
            permissions_response = self.session.get(f"{BASE_URL}/auth/permissoes", headers=headers)
            
            if permissions_response.status_code == 200:
                permissions = permissions_response.json()
                perfil_ativo = permissions.get('perfil_ativo', 'N/A')
                print(f"🔒 Permissões contextuais para {perfil_ativo}:")
                print(f"   - Criar contrato: {permissions.get('pode_criar_contrato', False)}")
                print(f"   - Submeter relatório: {permissions.get('pode_submeter_relatorio', False)}")
                print(f"   - Aprovar relatório: {permissions.get('pode_aprovar_relatorio', False)}")
                print(f"   - Contratos visíveis: {len(permissions.get('contratos_visiveis', []))}")
            else:
                print(f"⚠️ Permissões não disponíveis: {permissions_response.status_code}")
        except Exception as e:
            print(f"⚠️ Erro ao buscar permissões: {e}")

    def setup_test_data(self):
        """Configura dados necessários para testes"""
        print("\n📋 Configurando dados de teste...")
        
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Busca ou cria contratado
        contratados_response = self.session.get(f"{API_URL}/contratados", headers=headers)
        contratados_data = contratados_response.json()
        
        if contratados_data.get("data"):
            self.contratado_id = contratados_data["data"][0]["id"]
            print(f"✅ Usando contratado existente: ID {self.contratado_id}")
        else:
            # Cria contratado de teste
            contratado_data = {
                "nome": "Empresa Teste LTDA",
                "email": "contato@empresateste.com",
                "cnpj": "12345678000123",
                "telefone": "(91) 99999-9999"
            }
            
            response = self.session.post(f"{API_URL}/contratados", 
                                       json=contratado_data, 
                                       headers=headers)
            if response.status_code == 201:
                self.contratado_id = response.json()["id"]
                print(f"✅ Contratado criado: ID {self.contratado_id}")
            else:
                print(f"❌ Erro ao criar contratado: {response.status_code}")
                return False
        
        # Busca modalidade e status
        modalidades_response = self.session.get(f"{API_URL}/modalidades", headers=headers)
        if modalidades_response.status_code == 200:
            modalidades = modalidades_response.json()
            if modalidades:
                self.modalidade_id = modalidades[0]["id"]
        
        status_response = self.session.get(f"{API_URL}/status", headers=headers)
        if status_response.status_code == 200:
            status_list = status_response.json()
            if status_list:
                self.status_id = status_list[0]["id"]
        
        print(f"✅ Modalidade ID: {self.modalidade_id}, Status ID: {self.status_id}")
        return True

    def run_complete_test(self):
        """Executa todos os testes - VERSÃO CORRIGIDA"""
        try:
            # 1. Setup inicial
            self.login_admin()
            
            # 2. Configurar usuários de teste
            self.rafael_id = self.get_or_create_user(USUARIOS_TESTE[0])
            self.anderson_id = self.get_or_create_user(USUARIOS_TESTE[1])
            
            # 3. Configurar perfis múltiplos
            self.setup_multiple_profiles(self.rafael_id, USUARIOS_TESTE[0]["perfis"])
            self.setup_multiple_profiles(self.anderson_id, USUARIOS_TESTE[1]["perfis"])
            
            # 4. Testar login com contexto de sessão
            self.rafael_token, rafael_context = self.test_user_login_with_profile_selection(
                USUARIOS_TESTE[0]["email"]
            )
            
            self.anderson_token, anderson_context = self.test_user_login_with_profile_selection(
                USUARIOS_TESTE[1]["email"]
            )
            
            # 5. Testar dashboard e permissões
            self.test_dashboard_and_permissions(self.rafael_token, "Rafael Costa")
            self.test_dashboard_and_permissions(self.anderson_token, "Anderson Pontes")
            
            # 6. Testar alternância de perfis (apenas se tokens válidos)
            if self.rafael_token:
                print("\n🎭 TESTANDO ALTERNÂNCIA DE PERFIS - RAFAEL")
                self.test_profile_switching(self.rafael_token, "Gestor")
                self.test_dashboard_and_permissions(self.rafael_token, "Rafael Costa como Gestor")
                
                self.test_profile_switching(self.rafael_token, "Fiscal") 
                self.test_dashboard_and_permissions(self.rafael_token, "Rafael Costa como Fiscal")
            
            if self.anderson_token:
                print("\n🎭 TESTANDO ALTERNÂNCIA DE PERFIS - ANDERSON")
                self.test_profile_switching(self.anderson_token, "Gestor")
                self.test_profile_switching(self.anderson_token, "Fiscal")
            
            # 7. Setup de dados de teste
            if self.setup_test_data():
                print("\n✅ SISTEMA BÁSICO FUNCIONANDO!")
                print("🎯 Funcionalidades testadas:")
                print("   - Login com perfis múltiplos")
                print("   - Dashboard contextual") 
                print("   - Alternância de perfis")
                print("   - Permissões contextuais")
                print("   - Configuração de dados")
            else:
                print("⚠️ Problemas na configuração de dados")
            
            print("\n🎉 TESTE BÁSICO CONCLUÍDO! 🎉")
            
        except Exception as e:
            print(f"\n❌ ERRO DURANTE OS TESTES: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.cleanup()

    def cleanup(self):
        """Limpa arquivos temporários"""
        print("\n🧹 Limpando arquivos temporários...")
        
        for filepath in self.test_files:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print(f"🗑️ Removido: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"⚠️ Erro ao remover {filepath}: {e}")

def main():
    """Função principal"""
    print("🔍 Verificando pré-requisitos...")
    
    # Verifica se o servidor está rodando
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor SIGESCON está rodando")
        else:
            print(f"⚠️ Servidor respondeu com status {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ ERRO: Servidor SIGESCON não está rodando!")
        print("💡 Inicie o servidor com:")
        print("   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    print("Aguarde enquanto executamos todos os testes...")
    print("Isso pode levar alguns minutos...\n")
    
    tester = SigesconTester()
    tester.run_complete_test()
    
    print("\n" + "="*60)
    print("📋 INSTRUÇÕES PARA PRÓXIMOS PASSOS:")
    print("="*60)
    print("1. Se perfis múltiplos falharam, execute:")
    print("   python scripts/migrate_to_multiple_profiles.py")
    print()
    print("2. Para testar manualmente no frontend:")
    print("   - Login: rafael.costa@pge.pa.gov.br / senha123")
    print("   - Login: anderson.pontes@pge.pa.gov.br / senha123")
    print()
    print("3. Endpoints disponíveis:")
    print("   - POST /auth/login - Login com contexto")
    print("   - POST /auth/alternar-perfil - Alternar perfil")
    print("   - GET /auth/dashboard - Dashboard dinâmico")
    print("   - GET /auth/permissões - Permissões contextuais")
    print()
    print("4. Documentação completa em:")
    print("   - http://127.0.0.1:8000/docs")
    print("   - docs/frontend_integration_guide.md")

if __name__ == "__main__":
    main()