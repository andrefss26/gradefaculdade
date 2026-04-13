"""
Serviço de autenticação.
Responsável por validar credenciais e gerenciar a senha do usuário.
"""
from services.csv_service import read, write


def verificar_login(email: str, senha: str) -> dict | None:
    """
    Verifica as credenciais no CSV de usuários.
    Retorna o dicionário do usuário se válido, None caso contrário.
    """
    df = read("usuarios")
    usuario = df[(df["email"] == email) & (df["senha"] == senha)]
    if usuario.empty:
        return None
    return usuario.iloc[0].to_dict()
