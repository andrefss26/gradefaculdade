import os

SECRET_KEY = "gradefaculdade-secret-2026"
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")

CSVS = {
    "usuarios":    ["id", "nome", "email", "senha", "perfil", "id_vinculo"],
    "professores": ["id", "nome", "email", "dias_disponiveis", "max_aulas_dia"],
    "disciplinas": ["id", "nome", "carga_horaria", "duracao_blocos", "id_professor", "id_curso"],
    "turmas":      ["id", "nome", "id_curso", "quantidade_alunos"],
    "cursos":      ["id", "nome"],
    "salas":       ["id", "nome", "capacidade", "tipo"],
    "horarios":    ["id", "turno", "dia_semana", "horario_inicio", "horario_fim"],
    "aulas":       ["id_aula", "id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"],
}

MAPA_CURSO_DISCS = {
    "1": [str(i) for i in range(1,  6)],
    "2": [str(i) for i in range(6,  11)],
    "3": [str(i) for i in range(11, 16)],
    "4": [str(i) for i in range(16, 21)],
}
