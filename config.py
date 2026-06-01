import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

CSVS = {
    "professores": os.path.join(DATA_DIR, "professores.csv"),
    "disciplinas":  os.path.join(DATA_DIR, "disciplinas.csv"),
    "turmas":       os.path.join(DATA_DIR, "turmas.csv"),
    "salas":        os.path.join(DATA_DIR, "salas.csv"),
    "horarios":     os.path.join(DATA_DIR, "horarios.csv"),
    "aulas":        os.path.join(DATA_DIR, "aulas.csv"),
    "usuarios":     os.path.join(DATA_DIR, "usuarios.csv"),
}

HEADERS = {
    "professores": ["id","nome","email","dias_disponiveis","max_aulas_dia","disciplinas_ids"],
    "disciplinas":  ["id","nome","carga_horaria","curso","id_professor"],
    "turmas":       ["id","nome","curso","semestre","periodo","quantidade_alunos","disciplinas_exigidas"],
    "salas":        ["id","nome","capacidade","tipo"],
    "horarios":     ["id","turno","dia_semana","horario_inicio","horario_fim"],
    "aulas":        ["id_aula","id_professor","id_turma","id_sala","id_horario","id_disciplina"],
    "usuarios":     ["id","nome","email","senha","perfil"],
}

SECRET_KEY = "faculdade_tech_2025"

CURSOS = ["ADS", "SI", "Ciberseguranca", "Banco de Dados"]
