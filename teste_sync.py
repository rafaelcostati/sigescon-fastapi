# teste_api_unificado.py
import requests
import os
import uuid
import random
from datetime import date, timedelta
from dotenv import load_dotenv
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- 1. CONFIGURAÇÃO INICIAL ---

load_dotenv()
BASE_URL = "http://127.0.0.1:8000"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Dicionário global para rastrear todos os recursos criados para cleanup
ids_criados = {
    "usuarios": [],
    "contratados": [],
    "contratos": [],
    "modalidades": [],
    "status": []
}

# --- 2. FUNÇÕES AUXILIARES DE TESTE ---

def print_step(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def print_sub_step(title):
    print("\n" + "-"*60)
    print(f" {title} ".center(60, "-"))

def print_success(message): print(f"✅ Sucesso: {message}")
def print_failure(message): print(f"❌ Falha: {message}")
def print_info(message): print(f"ℹ️ Info: {message}")
def print_expected_error(message): print(f"🎯 Erro Esperado: {message}")

def handle_api_error(message, e):
    print_failure(message)
    if hasattr(e, 'response') and e.response is not None:
        try:
            print(f"Status Code: {e.response.status_code}")
            print(f"Resposta da API: {e.response.json()}")
        except requests.exceptions.JSONDecodeError:
            print(f"Resposta da API (não-JSON): {e.response.text}")
    else:
        print(f"Exceção: {e}")

def generate_dummy_pdf(file_path: str, contrato_nr: str):
    c = canvas.Canvas(file_path, pagesize=letter)
    c.drawString(100, 750, "Relatório de Fiscalização"); c.drawString(100, 730, f"Contrato Nº: {contrato_nr}")
    c.drawString(100, 700, "Este é um relatório gerado automaticamente para fins de teste."); c.save()

# --- 3. FUNÇÕES DE INTERAÇÃO COM A API ---

def get_token(email, password):
    try:
        response = requests.post(f"{BASE_URL}/auth/login", data={"username": email, "password": password})
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.RequestException as e:
        handle_api_error(f"Falha no login para {email}", e); raise

def get_headers(token): return {"Authorization": f"Bearer {token}"}

def get_seeded_data_id(admin_headers, endpoint, required_name):
    try:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=admin_headers)
        response.raise_for_status()
        response_data = response.json()
        items = response_data.get('data') if isinstance(response_data, dict) and 'data' in response_data else response_data
        item = next((i for i in items if i['nome'] == required_name), None)
        return item['id'] if item else None
    except requests.exceptions.RequestException as e:
        handle_api_error(f"Falha ao buscar dados de '{endpoint}'", e); raise

def create_temporary_user(admin_headers, perfil_id=3, return_full_data=False):
    cpf = ''.join([str(random.randint(0, 9)) for _ in range(11)])
    user_data = { "nome": f"Usuário Temp {uuid.uuid4().hex[:6]}", "email": f"temp.{uuid.uuid4().hex[:6]}@teste.com", "cpf": cpf, "senha": "password123", "perfil_id": perfil_id }
    response = requests.post(f"{BASE_URL}/api/v1/usuarios/", json=user_data, headers=admin_headers)
    response.raise_for_status()
    user = response.json()
    ids_criados["usuarios"].append(user['id'])
    # Removido print daqui para não poluir a saída de outros testes
    if return_full_data: user['senha'] = user_data['senha']; return user
    return user

# --- 4. SUÍTES DE TESTE MODULARES ---

def run_usuarios_tests(admin_headers):
    print_step("Iniciando suíte de testes: Usuários e Autenticação")
    
    # Teste 1: CRUD completo
    print_sub_step("Teste 1: CRUD de Usuário")
    user_to_test = create_temporary_user(admin_headers, return_full_data=True)
    print_success(f"Usuário temporário (ID: {user_to_test['id']}) criado para o teste.")
    user_id = user_to_test['id']

    response = requests.get(f"{BASE_URL}/api/v1/usuarios/{user_id}", headers=admin_headers)
    assert response.status_code == 200 and response.json()['email'] == user_to_test['email']
    print_success("Leitura de usuário por ID funciona.")

    update_data = {"nome": "Nome do Usuário Atualizado"}
    response = requests.patch(f"{BASE_URL}/api/v1/usuarios/{user_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200 and response.json()['nome'] == update_data['nome']
    print_success("Atualização de usuário funciona.")

    # Teste 2: Gestão de Senhas
    print_sub_step("Teste 2: Gestão de Senhas")
    user_token = get_token(user_to_test['email'], user_to_test['senha'])
    user_headers = get_headers(user_token)

    change_pw_data = {"senha_antiga": "password123", "nova_senha": "new_password_456"}
    response = requests.patch(f"{BASE_URL}/api/v1/usuarios/{user_id}/alterar-senha", json=change_pw_data, headers=user_headers)
    assert response.status_code == 200
    print_success("Usuário alterou a própria senha.")
    get_token(user_to_test['email'], "new_password_456")

    reset_pw_data = {"nova_senha": "reset_by_admin"}
    response = requests.patch(f"{BASE_URL}/api/v1/usuarios/{user_id}/resetar-senha", json=reset_pw_data, headers=admin_headers)
    assert response.status_code == 200
    print_success("Admin resetou a senha do usuário.")
    get_token(user_to_test['email'], "reset_by_admin")

    # Teste 3: Permissões
    print_sub_step("Teste 3: Permissões de Usuário")
    response = requests.post(f"{BASE_URL}/api/v1/usuarios/", json=user_to_test, headers=user_headers)
    assert response.status_code == 403
    print_expected_error("Usuário comum não pode criar outros usuários (403 Forbidden).")
    
    # Teste 4: Paginação
    print_sub_step("Teste 4: Paginação de Usuários")
    for i in range(3):
        create_temporary_user(admin_headers)
    
    response_p1 = requests.get(f"{BASE_URL}/api/v1/usuarios/?page=1&per_page=2", headers=admin_headers)
    response_p1.raise_for_status()
    data_p1 = response_p1.json()
    assert len(data_p1['data']) == 2
    assert data_p1['current_page'] == 1
    assert data_p1['per_page'] == 2
    assert data_p1['total_items'] >= 4
    print_success("Paginação (página 1 de 2) funciona corretamente.")

    response_p2 = requests.get(f"{BASE_URL}/api/v1/usuarios/?page=2&per_page=2", headers=admin_headers)
    response_p2.raise_for_status()
    data_p2 = response_p2.json()
    assert data_p2['current_page'] == 2
    assert len(data_p2['data']) > 0
    print_success("Paginação (página 2 de 2) funciona corretamente.")
    
    # Soft delete final do usuário de teste
    response = requests.delete(f"{BASE_URL}/api/v1/usuarios/{user_id}", headers=admin_headers)
    assert response.status_code == 204
    print_success("Soft delete de usuário funciona.")


def run_contratados_tests(admin_headers):
    print_step("Iniciando suíte de testes: Contratados")
    
    # Teste 1: CRUD
    print_sub_step("Teste 1: CRUD de Contratado")
    contratado_data = {"nome": f"Contratado CRUD {uuid.uuid4().hex[:6]}", "email": f"crud.{uuid.uuid4().hex[:4]}@teste.com", "cnpj": f"{random.randint(10**13, 10**14-1)}"}
    response = requests.post(f"{BASE_URL}/api/v1/contratados/", json=contratado_data, headers=admin_headers)
    response.raise_for_status()
    contratado = response.json()
    ids_criados["contratados"].append(contratado['id'])
    print_success(f"Contratado '{contratado['nome']}' criado.")

    response = requests.delete(f"{BASE_URL}/api/v1/contratados/{contratado['id']}", headers=admin_headers)
    assert response.status_code == 204
    print_success("Contratado deletado com sucesso.")

    # --- TESTE CORRIGIDO E APRIMORADO ---
    print_sub_step("Teste 2: Paginação e Filtros")
    nome_filtro = f"Filtro-{uuid.uuid4().hex[:4]}"
    # Cria 3 contratados com nomes e emails únicos para o filtro
    for i in range(3):
        payload = {
            "nome": f"{nome_filtro}_{i}", 
            "email": f"filtro.{uuid.uuid4().hex[:6]}@teste.com"
        }
        resp_create = requests.post(f"{BASE_URL}/api/v1/contratados/", json=payload, headers=admin_headers)
        resp_create.raise_for_status()
        # Adiciona o ID para a limpeza
        ids_criados["contratados"].append(resp_create.json()['id'])
    
    # Realiza a busca com o filtro
    response = requests.get(f"{BASE_URL}/api/v1/contratados/?nome={nome_filtro}", headers=admin_headers)
    response.raise_for_status()
    data = response.json()
    assert data['total_items'] == 3
    print_success("Filtro por nome em contratados funciona e retorna a contagem correta.")
    
def run_auxiliary_tables_tests(admin_headers):
    print_step("Iniciando suíte de testes: Tabelas Auxiliares (Status, Perfis, etc.)")
    
    # Teste 1: Status de Contrato
    print_sub_step("Teste 1: CRUD de Status de Contrato")
    status_nome = f"Status Teste {uuid.uuid4().hex[:6]}"
    response = requests.post(f"{BASE_URL}/api/v1/status/", json={"nome": status_nome}, headers=admin_headers)
    response.raise_for_status()
    status_criado = response.json()
    ids_criados["status"].append(status_criado['id'])
    print_success("Status de contrato criado.")

    response = requests.delete(f"{BASE_URL}/api/v1/status/{status_criado['id']}", headers=admin_headers)
    assert response.status_code == 204
    print_success("Status de contrato (não utilizado) deletado.")
    
    # Teste 2: Listagem de outras tabelas
    print_sub_step("Teste 2: Listagem de dados semeados")
    for endpoint in ["/api/v1/perfis/", "/api/v1/statusrelatorio/", "/api/v1/statuspendencia/"]:
        response = requests.get(f"{BASE_URL}{endpoint}", headers=admin_headers)
        assert response.status_code == 200 and len(response.json()) > 0
        print_success(f"Endpoint '{endpoint}' listado com sucesso.")

def run_modalidade_tests(admin_headers):
    print_step("Iniciando suíte de testes: Modalidades (Regras de Negócio)")
    modalidade_em_uso_nome = f"Modalidade Em Uso {uuid.uuid4().hex[:6]}"
    response = requests.post(f"{BASE_URL}/api/v1/modalidades/", json={"nome": modalidade_em_uso_nome}, headers=admin_headers)
    response.raise_for_status()
    modalidade_em_uso = response.json()
    ids_criados["modalidades"].append(modalidade_em_uso['id'])
    print_success(f"Criada modalidade '{modalidade_em_uso_nome}' para teste de conflito.")
    
    contrato_id_teste_modalidade = create_temporary_contract(admin_headers, modalidade_em_uso['id'])
    print_success(f"Contrato temporário (ID: {contrato_id_teste_modalidade}) criado e vinculado à modalidade.")

    print_info(f"Tentando deletar a modalidade em uso (ID: {modalidade_em_uso['id']})...")
    response = requests.delete(f"{BASE_URL}/api/v1/modalidades/{modalidade_em_uso['id']}", headers=admin_headers)
    assert response.status_code == 409
    print_expected_error("A API retornou 409 (Conflict) como esperado.")

def run_main_workflow(admin_headers):
    print_step("Iniciando fluxo de trabalho principal: Contrato e Relatório E2E")
    admin_user_id = requests.get(f"{BASE_URL}/api/v1/usuarios/me", headers=admin_headers).json()['id']
    contratado_data = {"nome": f"Empresa Principal {uuid.uuid4().hex[:6]}", "email": f"principal.{uuid.uuid4().hex[:6]}@teste.com", "cnpj": f"{random.randint(10**13, 10**14-1)}"}
    response = requests.post(f"{BASE_URL}/api/v1/contratados/", json=contratado_data, headers=admin_headers)
    response.raise_for_status(); contratado = response.json(); ids_criados["contratados"].append(contratado['id'])
    fiscal_user = create_temporary_user(admin_headers, return_full_data=True)
    fiscal_token = get_token(fiscal_user['email'], fiscal_user['senha'])
    modalidade_id = get_seeded_data_id(admin_headers, "/api/v1/modalidades/", "Pregão")
    status_id = get_seeded_data_id(admin_headers, "/api/v1/status/", "Vigente")
    contrato_data = { "nr_contrato": f"API-MAIN-{uuid.uuid4().hex[:8]}", "objeto": "Contrato E2E", "data_inicio": str(date.today()), "data_fim": str(date.today() + timedelta(days=365)), "contratado_id": contratado['id'], "modalidade_id": modalidade_id, "status_id": status_id, "gestor_id": fiscal_user['id'], "fiscal_id": fiscal_user['id'] }
    response = requests.post(f"{BASE_URL}/api/v1/contratos/", data=contrato_data, headers=admin_headers)
    response.raise_for_status(); contrato = response.json(); ids_criados["contratos"].append(contrato['id'])
    status_pendente_id = get_seeded_data_id(admin_headers, "/api/v1/statuspendencia/", "Pendente")
    pendencia_data = { "descricao": "Relatório mensal E2E", "data_prazo": str(date.today() + timedelta(days=30)), "status_pendencia_id": status_pendente_id, "criado_por_usuario_id": admin_user_id }
    response = requests.post(f"{BASE_URL}/api/v1/contratos/{contrato['id']}/pendencias/", json=pendencia_data, headers=admin_headers)
    response.raise_for_status(); pendencia = response.json()
    print_success("Ambiente para o fluxo E2E criado (Contratado, Fiscal, Contrato, Pendência).")
    
    print_sub_step("Fluxo E2E: Ações do Fiscal")
    fiscal_headers = get_headers(fiscal_token)
    pdf_path = "relatorio_e2e.pdf"
    generate_dummy_pdf(pdf_path, contrato['nr_contrato'])
    relatorio_form_data = {"mes_competencia": str(date.today()), "pendencia_id": pendencia['id'], "observacoes_fiscal": "Relatório E2E."}
    with open(pdf_path, 'rb') as f:
        files = {'arquivo': (os.path.basename(pdf_path), f, 'application/pdf')}
        response = requests.post(f"{BASE_URL}/api/v1/contratos/{contrato['id']}/relatorios/", data=relatorio_form_data, files=files, headers=fiscal_headers)
        response.raise_for_status()
        relatorio_submetido = response.json()
        print_success("Fiscal enviou o relatório com anexo PDF.")

    print_sub_step("Fluxo E2E: Ações do Admin")
    status_aprovado_id = get_seeded_data_id(admin_headers, "/api/v1/statusrelatorio/", "Aprovado")
    analise_data = {"aprovador_usuario_id": admin_user_id, "status_id": status_aprovado_id, "observacoes_aprovador": "Aprovado via script E2E."}
    response = requests.patch(f"{BASE_URL}/api/v1/contratos/{contrato['id']}/relatorios/{relatorio_submetido['id']}/analise", json=analise_data, headers=admin_headers)
    response.raise_for_status()
    assert response.json()['status_relatorio'] == 'Aprovado'
    print_success("Admin aprovou o relatório. Fluxo E2E concluído!")


# --- 5. FUNÇÕES DE APOIO E ORQUESTRADOR ---

def create_temporary_contract(admin_headers, modalidade_id):
    contratado_data = {"nome": f"Contratado Temp Dep {uuid.uuid4().hex[:4]}", "email": f"dep.{uuid.uuid4().hex[:4]}@teste.com"}
    response = requests.post(f"{BASE_URL}/api/v1/contratados/", json=contratado_data, headers=admin_headers)
    response.raise_for_status(); contratado = response.json(); ids_criados["contratados"].append(contratado['id'])
    admin_user_id = requests.get(f"{BASE_URL}/api/v1/usuarios/me", headers=admin_headers).json()['id']
    status_id = get_seeded_data_id(admin_headers, "/api/v1/status/", "Vigente")
    contrato_data = {"nr_contrato": f"API-TEMP-{uuid.uuid4().hex[:8]}", "objeto": "Contrato de dependência", "data_inicio": str(date.today()), "data_fim": str(date.today() + timedelta(days=1)), "contratado_id": contratado['id'], "modalidade_id": modalidade_id, "status_id": status_id, "gestor_id": admin_user_id, "fiscal_id": admin_user_id}
    response = requests.post(f"{BASE_URL}/api/v1/contratos/", data=contrato_data, headers=admin_headers)
    response.raise_for_status(); contrato = response.json(); ids_criados["contratos"].append(contrato['id'])
    return contrato['id']

def main():
    admin_token = None
    try:
        print_info(f"Iniciando testes contra a API em {BASE_URL}")
        admin_token = get_token(ADMIN_EMAIL, ADMIN_PASSWORD)
        admin_headers = get_headers(admin_token)

        # Executa todas as suítes de teste
        run_usuarios_tests(admin_headers)
        run_contratados_tests(admin_headers)
        run_auxiliary_tables_tests(admin_headers)
        run_modalidade_tests(admin_headers)
        run_main_workflow(admin_headers)

        print_step("TODOS OS TESTES FORAM CONCLUÍDOS COM SUCESSO")

    except (requests.exceptions.RequestException, ValueError, AssertionError) as e:
        handle_api_error("A execução principal do teste falhou.", e)
    finally:
        print_step("Cleanup: Removendo todos os dados de teste criados")
        if admin_token:
            admin_headers = get_headers(admin_token)
            for id in reversed(ids_criados["contratos"]): requests.delete(f"{BASE_URL}/api/v1/contratos/{id}", headers=admin_headers); print(f"-> Contrato {id} deletado.")
            for id in reversed(ids_criados["contratados"]): requests.delete(f"{BASE_URL}/api/v1/contratados/{id}", headers=admin_headers); print(f"-> Contratado {id} deletado.")
            for id in reversed(ids_criados["modalidades"]): requests.delete(f"{BASE_URL}/api/v1/modalidades/{id}", headers=admin_headers); print(f"-> Tentativa de delete da Modalidade {id}.")
            for id in reversed(ids_criados["status"]): requests.delete(f"{BASE_URL}/api/v1/status/{id}", headers=admin_headers); print(f"-> Tentativa de delete do Status {id}.")
            for id in reversed(ids_criados["usuarios"]): requests.delete(f"{BASE_URL}/api/v1/usuarios/{id}", headers=admin_headers); print(f"-> Usuário {id} deletado.")

        for pdf_file in ["relatorio_e2e.pdf"]:
            if os.path.exists(pdf_file): os.remove(pdf_file); print(f"-> Arquivo PDF '{pdf_file}' removido.")
        
        print("\nTeste finalizado.")

if __name__ == "__main__":
    main()