"""
Serviço de cadastro das entidades principais.
Cobre: professores, disciplinas, turmas, salas e horários institucionais.
"""
import pandas as pd
from services.csv_service import read, write, next_id

# Entidades que usam "id" como chave primária
ENTIDADES_VALIDAS = {"cursos", "professores", "disciplinas", "turmas", "salas", "horarios"}


def listar(entidade: str) -> list[dict]:
    """Retorna todos os registros de uma entidade como lista de dicionários."""
    if entidade not in ENTIDADES_VALIDAS:
        return []
    return read(entidade).to_dict(orient="records")


def criar(entidade: str, dados: dict) -> dict:
    """
    Insere um novo registro na entidade.
    Atribui o próximo ID automaticamente.
    Retorna os dados com o ID gerado.
    """
    if entidade not in ENTIDADES_VALIDAS:
        raise ValueError(f"Entidade inválida: {entidade}")
    df = read(entidade)
    dados["id"] = str(next_id(entidade))
    novo = pd.DataFrame([dados])
    df = pd.concat([df, novo], ignore_index=True)
    write(entidade, df)
    return dados


def atualizar(entidade: str, id_val: str, dados: dict) -> bool:
    """
    Atualiza um registro existente pelo ID.
    Retorna True se encontrado e atualizado, False caso contrário.
    """
    if entidade not in ENTIDADES_VALIDAS:
        return False
    df = read(entidade)
    idx = df[df["id"] == str(id_val)].index
    if idx.empty:
        return False
    for campo, valor in dados.items():
        if campo in df.columns:
            df.at[idx[0], campo] = str(valor)
    write(entidade, df)
    return True


def deletar(entidade: str, id_val: str) -> bool:
    """
    Remove um registro pelo ID.
    Retorna True se removido com sucesso.
    """
    if entidade not in ENTIDADES_VALIDAS:
        return False
    df = read(entidade)
    novo_df = df[df["id"] != str(id_val)]
    write(entidade, novo_df)
    return True
