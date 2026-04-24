"""Popula dados de demonstração."""
import pandas as pd
from services.csv_service import read, write
from config import MAPA_CURSO_DISCS

def seed_demo():
    # Usuarios
    if read("usuarios").empty:
        write("usuarios", pd.DataFrame([
            {"id":"1","nome":"Administrador","email":"admin@escola.com","senha":"admin123","perfil":"admin","id_vinculo":""},
            {"id":"2","nome":"Carlos Souza","email":"carlos@escola.com","senha":"carlos123","perfil":"professor","id_vinculo":"1"},
            {"id":"3","nome":"Coordenador","email":"coord@escola.com","senha":"coord123","perfil":"coordenador","id_vinculo":""},
            {"id":"4","nome":"Ana Lima","email":"ana@escola.com","senha":"ana123","perfil":"professor","id_vinculo":"2"},
        ]))
    # Cursos
    if read("cursos").empty:
        write("cursos", pd.DataFrame([
            {"id":"1","nome":"Banco de Dados"},
            {"id":"2","nome":"Sistemas de Informação"},
            {"id":"3","nome":"Análise e Desenvolvimento"},
            {"id":"4","nome":"Segurança Cibernética"},
        ]))
    # Professores
    if read("professores").empty:
        write("professores", pd.DataFrame([
            {"id":"1","nome":"Carlos Souza","email":"carlos@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta","max_aulas_dia":"6"},
            {"id":"2","nome":"Ana Lima","email":"ana@escola.com","dias_disponiveis":"Segunda,Terca,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"3","nome":"Roberto Nunes","email":"roberto@escola.com","dias_disponiveis":"Segunda,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"4","nome":"Marina Costa","email":"marina@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Sexta","max_aulas_dia":"6"},
            {"id":"5","nome":"Felipe Santos","email":"felipe@escola.com","dias_disponiveis":"Terca,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"6","nome":"Juliana Oliveira","email":"juliana@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta","max_aulas_dia":"6"},
            {"id":"7","nome":"Pedro Alves","email":"pedro@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"8","nome":"Lucia Fernandes","email":"lucia@escola.com","dias_disponiveis":"Segunda,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"9","nome":"Rafael Moreira","email":"rafael@escola.com","dias_disponiveis":"Terca,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"10","nome":"Beatriz Santos","email":"beatriz@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta","max_aulas_dia":"6"},
            {"id":"11","nome":"Diego Lima","email":"diego@escola.com","dias_disponiveis":"Segunda,Terca,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"12","nome":"Carla Mendes","email":"carla@escola.com","dias_disponiveis":"Segunda,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"13","nome":"Marcos Ribeiro","email":"marcos@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Sexta","max_aulas_dia":"6"},
            {"id":"14","nome":"Sofia Castro","email":"sofia@escola.com","dias_disponiveis":"Terca,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"15","nome":"André Sousa","email":"andre@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta","max_aulas_dia":"6"},
            {"id":"16","nome":"Vanessa Cruz","email":"vanessa@escola.com","dias_disponiveis":"Segunda,Terca,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"17","nome":"Thiago Barbosa","email":"thiago@escola.com","dias_disponiveis":"Segunda,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"18","nome":"Fernanda Rocha","email":"fernanda@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Sexta","max_aulas_dia":"6"},
            {"id":"19","nome":"Gustavo Pinto","email":"gustavo@escola.com","dias_disponiveis":"Terca,Quarta,Quinta,Sexta","max_aulas_dia":"6"},
            {"id":"20","nome":"Isabela Gomes","email":"isabela@escola.com","dias_disponiveis":"Segunda,Terca,Quarta,Quinta","max_aulas_dia":"6"},
        ]))
    # Salas
    if read("salas").empty:
        write("salas", pd.DataFrame([
            {"id":"1","nome":"Sala 101","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"2","nome":"Sala 102","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"3","nome":"Sala 103","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"4","nome":"Sala 104","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"5","nome":"Sala 201","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"6","nome":"Sala 202","capacidade":"40","tipo":"Sala de Aula"},
            {"id":"7","nome":"Lab. Informática A","capacidade":"35","tipo":"Laboratorio"},
            {"id":"8","nome":"Lab. Informática B","capacidade":"35","tipo":"Laboratorio"},
            {"id":"9","nome":"Lab. Segurança","capacidade":"30","tipo":"Laboratorio"},
            {"id":"10","nome":"Auditório","capacidade":"80","tipo":"Auditorio"},
        ]))
    # Horários (manhã 07-12 + noite 19-23, Seg-Sex)
    if read("horarios").empty:
        slots = []
        sid = 1
        dias = ["Segunda","Terca","Quarta","Quinta","Sexta"]
        manha = [("07:00","07:50"),("07:50","08:40"),("08:40","09:30"),("09:40","10:30"),("10:30","11:20"),("11:20","12:10")]
        noite = [("19:00","19:50"),("19:50","20:40"),("20:40","21:30"),("21:40","22:30")]
        for dia in dias:
            for ini, fim in manha:
                slots.append({"id":str(sid),"turno":"Manha","dia_semana":dia,"horario_inicio":ini,"horario_fim":fim}); sid+=1
            for ini, fim in noite:
                slots.append({"id":str(sid),"turno":"Noite","dia_semana":dia,"horario_inicio":ini,"horario_fim":fim}); sid+=1
        write("horarios", pd.DataFrame(slots))
    # Disciplinas (20 disciplinas, 4 cursos × 5 disc)
    if read("disciplinas").empty:
        nomes = [
            # Curso 1 - Banco de Dados
            "Fundamentos de SQL","Banco de Dados NoSQL","Modelagem de Dados","Administração de BD","Data Warehouse",
            # Curso 2 - Sistemas de Informação
            "Análise de Sistemas","Engenharia de Software","Gestão de TI","Sistemas Distribuídos","Arquitetura de Software",
            # Curso 3 - Análise e Desenvolvimento
            "Desenvolvimento Web","Programação Mobile","Estrutura de Dados","Algoritmos Avançados","DevOps e Cloud",
            # Curso 4 - Segurança Cibernética
            "Criptografia","Segurança de Redes","Forense Digital","Ethical Hacking","Gestão de Riscos",
        ]
        discs = []
        for i, nome in enumerate(nomes, 1):
            curso = str((i-1)//5 + 1)
            prof  = str(i) if i <= 20 else "1"
            discs.append({"id":str(i),"nome":nome,"carga_horaria":"4","duracao_blocos":"1",
                          "id_professor":prof,"id_curso":curso})
        write("disciplinas", pd.DataFrame(discs))
    # Turmas
    if read("turmas").empty:
        nomes_t = []
        for curso in range(1,5):
            for sem in range(1,5):
                nomes_t.append((f"Turma {chr(64+curso)} {sem}º Sem", str(curso), str(30+sem)))
        turmas = [{"id":str(i+1),"nome":n,"id_curso":c,"quantidade_alunos":a}
                  for i,(n,c,a) in enumerate(nomes_t)]
        write("turmas", pd.DataFrame(turmas))
