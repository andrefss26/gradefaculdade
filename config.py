import os

# ── Diretórios ─────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ── Caminhos dos CSVs ──────────────────────────────────────────────────────────
CSVS = {
    "cursos":       os.path.join(DATA_DIR, "cursos.csv"),
    "professores": os.path.join(DATA_DIR, "professores.csv"),
    "disciplinas":  os.path.join(DATA_DIR, "disciplinas.csv"),
    "turmas":       os.path.join(DATA_DIR, "turmas.csv"),
    "salas":        os.path.join(DATA_DIR, "salas.csv"),
    "horarios":     os.path.join(DATA_DIR, "horarios.csv"),
    "aulas":        os.path.join(DATA_DIR, "aulas.csv"),
    "usuarios":     os.path.join(DATA_DIR, "usuarios.csv"),
}

# ── Colunas esperadas em cada CSV ──────────────────────────────────────────────
HEADERS = {
    "cursos":       ["id", "nome"],
    "professores": ["id", "nome", "email", "dias_disponiveis", "max_aulas_dia", "id_turma"],
    "disciplinas":  ["id", "nome", "carga_horaria", "id_professor", "duracao_blocos"],
    "turmas":       ["id", "nome", "quantidade_alunos", "id_curso"],
    "salas":        ["id", "nome", "capacidade", "tipo"],
    "horarios":     ["id", "turno", "dia_semana", "horario_inicio", "horario_fim"],
    "aulas":        ["id_aula", "id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"],
    "usuarios":     ["id", "nome", "email", "senha", "perfil"],
}

# ── Chave secreta da sessão ────────────────────────────────────────────────────
SECRET_KEY = "escola_secret_2025"
