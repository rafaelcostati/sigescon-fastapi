# tests/test_contratados.py
import pytest
from httpx import AsyncClient
import random

@pytest.mark.asyncio
async def test_full_crud_workflow(async_client: AsyncClient):
    """
    Testa o fluxo completo de CRUD (Create, Read, Update, Delete)
    para o endpoint de contratados em uma única função para garantir a ordem.
    
    NOTA: Atualmente, estes endpoints são públicos. Em um próximo passo, 
    eles serão protegidos e estes testes precisarão ser atualizados para
    incluir um token de autenticação de administrador.
    """
    # Gera um identificador único para este teste
    import random
    unique_num = str(random.randint(10000000, 99999999))  # 8 dígitos
    
    # --- 1. CREATE (POST /contratados) ---
    print("\n--- Testando CREATE ---")
    create_data = {
        "nome": f"Contratado Teste {unique_num} LTDA",
        "email": f"teste_{unique_num}@example.com",
        "cnpj": f"{unique_num}000199",  # CNPJ de 14 dígitos
        "cpf": None,
        "telefone": "91988887777"
    }
    response = await async_client.post("/contratados/", json=create_data)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["email"] == create_data["email"]
    assert response_data["nome"] == create_data["nome"]
    assert "id" in response_data
    contratado_id = response_data["id"]
    print(f"--> Contratado ID {contratado_id} criado com sucesso.")

    # --- 2. READ ONE (GET /contratados/{id}) ---
    print("\n--- Testando READ ONE ---")
    response = await async_client.get(f"/contratados/{contratado_id}")

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == contratado_id
    assert response_data["nome"] == create_data["nome"]
    print(f"--> Contratado ID {contratado_id} lido com sucesso.")

    # --- 3. READ ALL (GET /contratados) ---
    print("\n--- Testando READ ALL ---")
    response = await async_client.get("/contratados/")

    assert response.status_code == 200
    response_data = response.json()
    assert isinstance(response_data, list)
    assert len(response_data) > 0
    # Verifica se o ID que acabamos de criar está na lista
    assert contratado_id in [c["id"] for c in response_data]
    print(f"--> Lista de contratados lida com sucesso.")

    # --- 4. UPDATE (PATCH /contratados/{id}) ---
    print("\n--- Testando UPDATE ---")
    update_data = {
        "nome": f"Nome Atualizado {unique_num} SA",
        "telefone": "91955554444"
    }
    response = await async_client.patch(f"/contratados/{contratado_id}", json=update_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["nome"] == update_data["nome"]
    assert response_data["telefone"] == update_data["telefone"]
    assert response_data["email"] == create_data["email"]  # Garante que o email não mudou
    print(f"--> Contratado ID {contratado_id} atualizado com sucesso.")

    # --- 5. DELETE (DELETE /contratados/{id}) ---
    print("\n--- Testando DELETE ---")
    response = await async_client.delete(f"/contratados/{contratado_id}")

    assert response.status_code == 204  # No Content

    # --- 6. VERIFY DELETE ---
    print("\n--- Verificando DELETE ---")
    response = await async_client.get(f"/contratados/{contratado_id}")

    assert response.status_code == 404  # Not Found
    print(f"--> Contratado ID {contratado_id} deletado e não é mais encontrado.")