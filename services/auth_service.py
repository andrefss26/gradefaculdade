"""Controle de acesso RBAC."""
from __future__ import annotations

_PERMISSOES: dict[str, dict[str, set[str]]] = {
    "admin": {
        "professores": {"ler","criar","editar","deletar"},
        "turmas":      {"ler","criar","editar","deletar"},
        "disciplinas": {"ler","criar","editar","deletar"},
        "cursos":      {"ler","criar","editar","deletar"},
        "salas":       {"ler","criar","editar","deletar"},
        "horarios":    {"ler","criar","editar","deletar"},
        "aulas":       {"ler","criar","editar","deletar"},
        "grade":       {"ler","exportar"},
        "dashboard":   {"ler"},
    },
    "coordenador": {
        "professores": {"ler"},
        "turmas":      {"ler"},
        "disciplinas": {"ler"},
        "cursos":      {"ler"},
        "salas":       {"ler"},
        "horarios":    {"ler"},
        "aulas":       {"ler"},
        "grade":       {"ler","exportar"},
        "dashboard":   {"ler"},
    },
    "professor": {
        "professores": {"ler_own","editar_own"},
        "disciplinas": {"ler"},
        "horarios":    {"ler"},
        "aulas":       {"ler_own"},
        "grade":       {"ler_own"},
        "turmas":      set(),
        "salas":       set(),
        "dashboard":   set(),
    },
    "aluno": {
        "turmas":      {"ler_own"},
        "disciplinas": {"ler"},
        "horarios":    {"ler"},
        "aulas":       {"ler_own"},
        "grade":       {"ler_own"},
        "professores": set(),
        "salas":       set(),
        "dashboard":   set(),
    },
}

def verificar_permissao(usuario: dict, recurso: str, acao: str, id_alvo: str = "") -> None:
    perfil = usuario.get("perfil", "")
    uid    = str(usuario.get("id", ""))
    perms  = _PERMISSOES.get(perfil, {}).get(recurso, set())
    if acao in perms:
        return
    acao_own = f"{acao}_own"
    if acao_own in perms:
        if not id_alvo:
            raise PermissionError(f"Perfil '{perfil}' precisa de ID alvo para '{acao}' em '{recurso}'.")
        if str(id_alvo) == uid:
            return
        raise PermissionError(f"Perfil '{perfil}' só pode '{acao}' o próprio registro.")
    raise PermissionError(f"Perfil '{perfil}' não tem permissão para '{acao}' em '{recurso}'.")

def pode(usuario: dict, recurso: str, acao: str, id_alvo: str = "") -> bool:
    try:
        verificar_permissao(usuario, recurso, acao, id_alvo)
        return True
    except PermissionError:
        return False

def perfis_disponiveis() -> list[str]:
    return list(_PERMISSOES.keys())
