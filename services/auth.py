from services.db import read, write


def login(email, senha):
    df = read("usuarios")
    u = df[(df["email"] == email) & (df["senha"] == senha)]
    return u.iloc[0].to_dict() if not u.empty else None


def trocar_senha(email, atual, nova):
    df = read("usuarios")
    idx = df[df["email"] == email].index
    if idx.empty:
        return False, "Usuário não encontrado."
    if df.at[idx[0], "senha"] != atual:
        return False, "Senha atual incorreta."
    df.at[idx[0], "senha"] = nova
    write("usuarios", df)
    return True, "Senha alterada."
