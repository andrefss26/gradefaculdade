"""
Serviço de seed.
Popula os CSVs com dados de demonstração na primeira execução.
"""
import pandas as pd
from services.csv_service import read, write, CSVS


def seed_demo():
    """Insere dados de demonstração se os CSVs estiverem vazios."""

    # Usuários
    if read("usuarios").empty:
        pd.DataFrame([
            {"id": 1, "nome": "Administrador",  "email": "admin@escola.com",  "senha": "admin123",  "perfil": "adm"},
            {"id": 2, "nome": "Carlos Souza",   "email": "carlos@escola.com", "senha": "carlos123", "perfil": "professor"},
            {"id": 3, "nome": "Coord. Maria",   "email": "coord@escola.com",  "senha": "coord123",  "perfil": "coordenador"},
        ]).to_csv(CSVS["usuarios"], index=False)

    # Professores
    if read("professores").empty:
        pd.DataFrame([
            {"id": 1, "nome": "Carlos Souza",   "email": "carlos@escola.com",  "dias_disponiveis": "Segunda,Terca,Quarta,Quinta,Sexta", "max_aulas_dia": 4},
            {"id": 2, "nome": "Ana Lima",        "email": "ana@escola.com",     "dias_disponiveis": "Segunda,Terca,Quinta,Sexta",        "max_aulas_dia": 3},
            {"id": 3, "nome": "Roberto Nunes",   "email": "roberto@escola.com", "dias_disponiveis": "Segunda,Quarta,Sexta",              "max_aulas_dia": 4},
        ]).to_csv(CSVS["professores"], index=False)

    # Disciplinas
    if read("disciplinas").empty:
        pd.DataFrame([
            {"id": 1, "nome": "Matematica",  "carga_horaria": 4, "id_professor": 1},
            {"id": 2, "nome": "Portugues",   "carga_horaria": 4, "id_professor": 2},
            {"id": 3, "nome": "Fisica",      "carga_horaria": 3, "id_professor": 3},
            {"id": 4, "nome": "Historia",    "carga_horaria": 2, "id_professor": 2},
        ]).to_csv(CSVS["disciplinas"], index=False)

    # Turmas
    if read("turmas").empty:
        pd.DataFrame([
            {"id": 1, "nome": "1 EM A", "quantidade_alunos": 35},
            {"id": 2, "nome": "2 EM B", "quantidade_alunos": 32},
            {"id": 3, "nome": "3 EM C", "quantidade_alunos": 28},
        ]).to_csv(CSVS["turmas"], index=False)

    # Salas
    if read("salas").empty:
        pd.DataFrame([
            {"id": 1, "nome": "Sala 01",          "capacidade": 40, "tipo": "Sala de Aula"},
            {"id": 2, "nome": "Sala 02",          "capacidade": 40, "tipo": "Sala de Aula"},
            {"id": 3, "nome": "Lab. Informatica", "capacidade": 30, "tipo": "Laboratorio"},
        ]).to_csv(CSVS["salas"], index=False)

    # Horários institucionais (manhã e noite, Segunda a Sexta)
    if read("horarios").empty:
        horarios = []
        dias  = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta"]
        manha = [("07:00","07:50"), ("07:50","08:40"), ("08:40","09:30"), ("09:40","10:30")]
        noite = [("19:00","19:50"), ("19:50","20:40"), ("20:40","21:30"), ("21:40","22:30")]
        hid = 1
        for dia in dias:
            for ini, fim in manha:
                horarios.append({"id": hid, "turno": "Manha", "dia_semana": dia,
                                 "horario_inicio": ini, "horario_fim": fim})
                hid += 1
            for ini, fim in noite:
                horarios.append({"id": hid, "turno": "Noite", "dia_semana": dia,
                                 "horario_inicio": ini, "horario_fim": fim})
                hid += 1
        pd.DataFrame(horarios).to_csv(CSVS["horarios"], index=False)

    # Aulas (começa vazio)
    if read("aulas").empty:
        pd.DataFrame(columns=[
            "id_aula", "id_professor", "id_turma", "id_sala", "id_horario", "id_disciplina"
        ]).to_csv(CSVS["aulas"], index=False)
