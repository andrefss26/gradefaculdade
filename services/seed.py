"""
Estrutura real da faculdade:
- 4 cursos: ADS, SI, Cibersegurança, Banco de Dados
- Cada curso tem 4 semestres × 2 turmas (A e B) = 8 turmas por curso
- Manhã: semestres 1 e 2 (turmas 1A, 1B, 2A, 2B) × 4 cursos = 16 turmas
- Noite:  semestres 3 e 4 (turmas 3A, 3B, 4A, 4B) × 4 cursos = 16 turmas
- Total: 32 turmas
- Noite espelha a manhã: mesmas disciplinas do curso, horários equivalentes
"""
import pandas as pd
from services.db import read, CSVS


def seed():
    if read("usuarios").empty:
        pd.DataFrame([
            {"id":1,"nome":"Administrador",     "email":"admin@faculdade.com", "senha":"admin123","perfil":"adm"},
            {"id":2,"nome":"Prof. Carlos Souza","email":"carlos@faculdade.com","senha":"prof123", "perfil":"professor"},
            {"id":3,"nome":"Coord. Ana Lima",   "email":"coord@faculdade.com", "senha":"coord123","perfil":"coordenador"},
        ]).to_csv(CSVS["usuarios"], index=False)

    if read("professores").empty:
        dias = "Segunda,Terca,Quarta,Quinta,Sexta"
        nomes = [
            ("Carlos Souza",   "carlos"),   ("Ana Lima",       "ana"),
            ("Roberto Nunes",  "roberto"),  ("Patricia Melo",  "patricia"),
            ("Fernando Costa", "fernando"), ("Juliana Ramos",  "juliana"),
            ("Diego Ferreira", "diego"),    ("Camila Pereira", "camila"),
            ("Rafael Alves",   "rafael"),   ("Larissa Monteiro","larissa"),
            ("Marcos Vinicius","marcos"),   ("Beatriz Santos", "beatriz"),
        ]
        pd.DataFrame([
            {"id":i,"nome":n,"email":f"{s}@faculdade.com",
             "dias_disponiveis":dias,"max_aulas_dia":6,"disciplinas_ids":""}
            for i,(n,s) in enumerate(nomes,1)
        ]).to_csv(CSVS["professores"], index=False)

    if read("disciplinas").empty:
        # Cada curso tem disciplinas por semestre (sem1+sem2 = manhã, sem3+sem4 = noite)
        # carga_horaria=2 garante alocação sem estouro de slots
        discs = [
            # ADS
            {"id":1, "curso":"ADS","semestre":1,"nome":"Algoritmos e Lógica",   "carga_horaria":2,"id_professor":1},
            {"id":2, "curso":"ADS","semestre":1,"nome":"Fundamentos de TI",     "carga_horaria":2,"id_professor":2},
            {"id":3, "curso":"ADS","semestre":2,"nome":"Estrutura de Dados",    "carga_horaria":2,"id_professor":3},
            {"id":4, "curso":"ADS","semestre":2,"nome":"Programação Web",       "carga_horaria":2,"id_professor":4},
            {"id":5, "curso":"ADS","semestre":3,"nome":"Engenharia de Software","carga_horaria":2,"id_professor":5},
            {"id":6, "curso":"ADS","semestre":3,"nome":"Banco de Dados I",      "carga_horaria":2,"id_professor":6},
            {"id":7, "curso":"ADS","semestre":4,"nome":"Arquitetura de Soft.",  "carga_horaria":2,"id_professor":7},
            {"id":8, "curso":"ADS","semestre":4,"nome":"Projeto Integrador",    "carga_horaria":2,"id_professor":8},
            # SI
            {"id":9, "curso":"SI","semestre":1,"nome":"Redes de Computadores",  "carga_horaria":2,"id_professor":2},
            {"id":10,"curso":"SI","semestre":1,"nome":"Sistemas Operacionais",  "carga_horaria":2,"id_professor":3},
            {"id":11,"curso":"SI","semestre":2,"nome":"Gestão de TI",           "carga_horaria":2,"id_professor":4},
            {"id":12,"curso":"SI","semestre":2,"nome":"Auditoria de Sistemas",  "carga_horaria":2,"id_professor":5},
            {"id":13,"curso":"SI","semestre":3,"nome":"Governança de TI",       "carga_horaria":2,"id_professor":6},
            {"id":14,"curso":"SI","semestre":3,"nome":"Análise de Riscos",      "carga_horaria":2,"id_professor":7},
            {"id":15,"curso":"SI","semestre":4,"nome":"Inteligência de Negócios","carga_horaria":2,"id_professor":8},
            {"id":16,"curso":"SI","semestre":4,"nome":"TCC Orientado",          "carga_horaria":2,"id_professor":9},
            # Cibersegurança
            {"id":17,"curso":"Ciberseguranca","semestre":1,"nome":"Fundamentos de Segurança","carga_horaria":2,"id_professor":3},
            {"id":18,"curso":"Ciberseguranca","semestre":1,"nome":"Redes e Protocolos",       "carga_horaria":2,"id_professor":4},
            {"id":19,"curso":"Ciberseguranca","semestre":2,"nome":"Criptografia",             "carga_horaria":2,"id_professor":5},
            {"id":20,"curso":"Ciberseguranca","semestre":2,"nome":"Segurança de Redes",       "carga_horaria":2,"id_professor":6},
            {"id":21,"curso":"Ciberseguranca","semestre":3,"nome":"Ethical Hacking",          "carga_horaria":2,"id_professor":7},
            {"id":22,"curso":"Ciberseguranca","semestre":3,"nome":"Forense Digital",          "carga_horaria":2,"id_professor":8},
            {"id":23,"curso":"Ciberseguranca","semestre":4,"nome":"Pentest Avançado",         "carga_horaria":2,"id_professor":9},
            {"id":24,"curso":"Ciberseguranca","semestre":4,"nome":"Gestão de Incidentes",     "carga_horaria":2,"id_professor":10},
            # Banco de Dados
            {"id":25,"curso":"Banco de Dados","semestre":1,"nome":"Modelagem de Dados",       "carga_horaria":2,"id_professor":4},
            {"id":26,"curso":"Banco de Dados","semestre":1,"nome":"SQL Fundamental",          "carga_horaria":2,"id_professor":5},
            {"id":27,"curso":"Banco de Dados","semestre":2,"nome":"BD Relacional",            "carga_horaria":2,"id_professor":6},
            {"id":28,"curso":"Banco de Dados","semestre":2,"nome":"BD NoSQL",                 "carga_horaria":2,"id_professor":7},
            {"id":29,"curso":"Banco de Dados","semestre":3,"nome":"Data Warehouse",           "carga_horaria":2,"id_professor":8},
            {"id":30,"curso":"Banco de Dados","semestre":3,"nome":"Business Intelligence",    "carga_horaria":2,"id_professor":9},
            {"id":31,"curso":"Banco de Dados","semestre":4,"nome":"Big Data",                 "carga_horaria":2,"id_professor":10},
            {"id":32,"curso":"Banco de Dados","semestre":4,"nome":"Machine Learning p/ BD",  "carga_horaria":2,"id_professor":11},
        ]
        pd.DataFrame(discs).to_csv(CSVS["disciplinas"], index=False)

    if read("professores").empty:
        pass
    else:
        profs = read("professores")
        discs_df = read("disciplinas")
        if "disciplinas_ids" not in profs.columns:
            profs["disciplinas_ids"] = ""
        mapa = {}
        if not discs_df.empty and "id_professor" in discs_df.columns:
            for _, row in discs_df.iterrows():
                pid = str(row.get("id_professor", "")).strip()
                did = str(row.get("id", "")).strip()
                if pid and did:
                    mapa.setdefault(pid, [])
                    if did not in mapa[pid]:
                        mapa[pid].append(did)
        for i, row in profs.iterrows():
            pid = str(row.get("id", "")).strip()
            if not str(row.get("disciplinas_ids", "")).strip():
                profs.at[i, "disciplinas_ids"] = ",".join(mapa.get(pid, []))
        profs.to_csv(CSVS["professores"], index=False)

    if read("turmas").empty:
        turmas = []
        tid = 1
        cursos = ["ADS","SI","Ciberseguranca","Banco de Dados"]
        # Manhã: semestres 1 e 2, turmas A e B
        for curso in cursos:
            for sem in [1, 2]:
                for letra in ["A","B"]:
                    turmas.append({"id":tid,"nome":f"{curso[:3].upper()}-{sem}{letra}",
                                   "curso":curso,"semestre":sem,"periodo":"Manha","quantidade_alunos":35,"disciplinas_exigidas":""})
                    tid += 1
        # Noite: semestres 3 e 4, turmas A e B
        for curso in cursos:
            for sem in [3, 4]:
                for letra in ["A","B"]:
                    turmas.append({"id":tid,"nome":f"{curso[:3].upper()}-{sem}{letra}",
                                   "curso":curso,"semestre":sem,"periodo":"Noite","quantidade_alunos":35,"disciplinas_exigidas":""})
                    tid += 1
        pd.DataFrame(turmas).to_csv(CSVS["turmas"], index=False)

    turmas_df = read("turmas")
    if not turmas_df.empty:
        cursos = ["ADS","SI","Ciberseguranca","Banco de Dados"]
        existentes = set()
        for _, row in turmas_df.iterrows():
            existentes.add((str(row.get("curso", "")).strip(), str(row.get("semestre", "")).strip(), str(row.get("periodo", "")).strip(), str(row.get("nome", "")).strip()))
        vals = pd.to_numeric(turmas_df["id"], errors="coerce").dropna()
        tid = int(vals.max()) + 1 if not vals.empty else 1
        novas = []
        for curso in cursos:
            for sem, periodo in [(1, "Manha"), (2, "Manha"), (3, "Noite"), (4, "Noite")]:
                for letra in ["A","B"]:
                    nome = f"{curso[:3].upper()}-{sem}{letra}"
                    chave = (curso, str(sem), periodo, nome)
                    if chave not in existentes:
                        novas.append({"id":tid,"nome":nome,"curso":curso,"semestre":sem,"periodo":periodo,"quantidade_alunos":35,"disciplinas_exigidas":""})
                        tid += 1
        if novas:
            turmas_df = pd.concat([turmas_df, pd.DataFrame(novas)], ignore_index=True)
            turmas_df.to_csv(CSVS["turmas"], index=False)

    turmas_df = read("turmas")
    discs_df = read("disciplinas")
    if not turmas_df.empty:
        if "disciplinas_exigidas" not in turmas_df.columns:
            turmas_df["disciplinas_exigidas"] = ""
        for i, row in turmas_df.iterrows():
            if str(row.get("disciplinas_exigidas", "")).strip():
                continue
            curso = str(row.get("curso", "")).strip()
            sem = str(row.get("semestre", "")).strip()
            if not curso:
                continue
            base = discs_df[discs_df["curso"] == curso]
            if "semestre" in discs_df.columns and sem:
                fil = base[base["semestre"] == sem]
                if not fil.empty:
                    base = fil
            turmas_df.at[i, "disciplinas_exigidas"] = ",".join([str(v).strip() for v in base["id"].tolist() if str(v).strip()])
        turmas_df.to_csv(CSVS["turmas"], index=False)

    if read("salas").empty:
        salas = []
        for i in range(1, 13):
            salas.append({"id":i,    "nome":f"Sala {i:02d}","capacidade":40,"tipo":"Sala de Aula"})
        for i in range(1, 5):
            salas.append({"id":12+i,"nome":f"Lab. Info {i}","capacidade":30,"tipo":"Laboratorio"})
        salas.append({"id":17,"nome":"Auditorio","capacidade":120,"tipo":"Auditorio"})
        pd.DataFrame(salas).to_csv(CSVS["salas"], index=False)

    if read("horarios").empty:
        horarios = []
        dias  = ["Segunda","Terca","Quarta","Quinta","Sexta"]
        manha = [("07:00","07:50"),("07:50","08:40"),("08:40","09:30"),
                 ("09:40","10:30"),("10:30","11:20"),("11:20","12:10")]
        noite = [("19:00","19:50"),("19:50","20:40"),("20:40","21:30"),
                 ("21:40","22:30"),("22:30","23:20"),("23:20","00:10")]
        hid = 1
        for dia in dias:
            for ini,fim in manha:
                horarios.append({"id":hid,"turno":"Manha","dia_semana":dia,
                                 "horario_inicio":ini,"horario_fim":fim}); hid+=1
            for ini,fim in noite:
                horarios.append({"id":hid,"turno":"Noite","dia_semana":dia,
                                 "horario_inicio":ini,"horario_fim":fim}); hid+=1
        pd.DataFrame(horarios).to_csv(CSVS["horarios"], index=False)

    if read("aulas").empty:
        pd.DataFrame(columns=["id_aula","id_professor","id_turma",
                               "id_sala","id_horario","id_disciplina"]
                     ).to_csv(CSVS["aulas"], index=False)
