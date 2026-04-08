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


def alterar_senha(email: str, senha_atual: str, senha_nova: str) -> tuple[bool, str]:
    """
    Altera a senha de um usuário.
    Retorna (sucesso, mensagem).
    """
    df = read("usuarios")
    idx = df[df["email"] == email].index
    if idx.empty:
        return False, "Usuário não encontrado."
    if df.at[idx[0], "senha"] != senha_atual:
        return False, "Senha atual incorreta."
    df.at[idx[0], "senha"] = senha_nova
    write("usuarios", df)
    return True, "Senha alterada com sucesso."
