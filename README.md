# GradeEscolar

Sistema web em Flask para gestão de horários escolares, cadastro de entidades acadêmicas e alocação automática de aulas.  
O projeto utiliza arquivos CSV como persistência local, autenticação com sessão e controle de acesso por perfil.

## Visão geral

O GradeEscolar foi criado para centralizar a organização da grade horária de uma instituição, permitindo:

- login e controle de sessão
- cadastro de professores, disciplinas, turmas, cursos, salas e horários
- registro e edição de aulas alocadas
- disponibilidade de professores
- alocação automática de grade
- exportação da grade em CSV
- visualização de dashboard com resumo geral

## Funcionalidades

### Autenticação
- Login com e-mail e senha
- Logout
- Registro de usuários
- Controle de acesso por perfil

### Perfis suportados
- `admin`
- `coordenador`
- `professor`
- `aluno`

Cada perfil possui permissões diferentes sobre leitura, criação, edição, exclusão e exportação.

### Cadastros
- Professores
- Disciplinas
- Turmas
- Cursos
- Salas
- Horários institucionais

### Grade horária
- Listagem das aulas alocadas
- Criação manual de aula
- Edição de aula
- Remoção de aula
- Limpeza completa da grade
- Exportação da grade por turma ou por professor

### Disponibilidade
- Professores podem registrar seus dias disponíveis
- A alocação automática respeita a disponibilidade informada

### Alocação automática
- Distribui aulas considerando:
  - disponibilidade do professor
  - limite máximo de aulas por dia
  - conflitos de professor, turma e sala
  - capacidade da sala
  - duração em blocos da disciplina

### Dashboard
- Resumo geral com:
  - professores
  - turmas
  - disciplinas
  - salas
  - aulas alocadas
  - total de alunos

## Tecnologias utilizadas

- Python
- Flask
- Pandas
- HTML
- CSS
- JavaScript
- CSV como armazenamento local

## Estrutura do projeto

```text
gradefaculdade/
├── app.py
├── config.py
├── data/
│   ├── aulas.csv
│   ├── cursos.csv
│   ├── disciplinas.csv
│   ├── horarios.csv
│   ├── professores.csv
│   ├── salas.csv
│   ├── turmas.csv
│   └── usuarios.csv
├── routes/
│   ├── __init__.py
│   ├── alocar_routes.py
│   ├── auth_routes.py
│   ├── cadastro_routes.py
│   ├── dashboard_routes.py
│   └── grade_routes.py
├── services/
│   ├── __init__.py
│   ├── alocar_service.py
│   ├── auth_service.py
│   ├── csv_service.py
│   ├── grade_service.py
│   └── seed_service.py
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── templates/
    ├── index.html
    └── login.html
```

## Como funciona

### Persistência
O sistema não usa banco de dados relacional.  
Os dados ficam salvos em arquivos CSV dentro da pasta `data/`.

Na primeira execução, o sistema:
- cria os CSVs necessários
- popula dados iniciais de demonstração

### Controle de acesso
As permissões são definidas em `services/auth_service.py`.  
Cada perfil acessa apenas os recursos permitidos.

### Fluxo principal
1. O usuário faz login
2. O sistema carrega o dashboard
3. O usuário acessa os cadastros disponíveis para seu perfil
4. As aulas podem ser criadas manualmente ou geradas automaticamente
5. A grade pode ser exportada ou visualizada em tela

## Requisitos

- Python 3.10 ou superior
- Dependências Python:
  - Flask
  - pandas

## Instalação

### 1. Clonar o repositório
```bash
git clone https://github.com/andrefss26/gradefaculdade.git
cd gradefaculdade
```

### 2. Criar e ativar ambiente virtual

#### Windows
```bash
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/macOS
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install flask pandas
```

Se você preferir, também pode criar um `requirements.txt` com essas dependências.

## Execução

Para iniciar o sistema:

```bash
python app.py
```

O aplicativo será executado em:

```text
http://127.0.0.1:5050
```

Na primeira execução, os arquivos CSV serão inicializados automaticamente e os dados de demonstração serão carregados.

## Rotas principais

### Autenticação
- `GET /login`
- `POST /api/login`
- `POST /api/logout`
- `PUT /api/senha`

### Dashboard
- `GET /`
- `GET /dashboard`
- `GET /api/resumo`

### Cadastros
- `GET /api/<entidade>`
- `POST /api/<entidade>`
- `PUT /api/<entidade>/<id>`
- `DELETE /api/<entidade>/<id>`
- `PUT /api/professores/<id>/disponibilidade`

Entidades suportadas:
- `professores`
- `disciplinas`
- `turmas`
- `cursos`
- `salas`
- `horarios`

### Grade e aulas
- `GET /api/aulas`
- `POST /api/aulas`
- `PUT /api/aulas/<id>`
- `DELETE /api/aulas/<id>`
- `DELETE /api/aulas/limpar`
- `GET /api/grade/export/<tipo>`

### Alocação
- `POST /api/alocar-completo`
- `GET /api/relatorio-alocacao`

## Dados iniciais

Os arquivos CSV são criados automaticamente com as colunas corretas definidas em `config.py`.

Arquivos principais:
- `usuarios.csv`
- `professores.csv`
- `disciplinas.csv`
- `turmas.csv`
- `cursos.csv`
- `salas.csv`
- `horarios.csv`
- `aulas.csv`

## Regras de negócio

- professores precisam ter dias disponíveis cadastrados para que a alocação automática funcione bem
- disciplinas podem ter duração em blocos
- aulas não podem conflitar em:
  - professor
  - turma
  - sala
- salas precisam comportar a quantidade de alunos da turma
- usuários sem permissão recebem acesso negado

## Observações importantes

- O projeto usa armazenamento local em CSV, então alterações são persistidas diretamente nos arquivos da pasta `data/`
- A aplicação foi pensada para ambiente de desenvolvimento/local
- Em produção, seria recomendável substituir os CSVs por um banco de dados

## Desenvolvimento

### Iniciar em modo de desenvolvimento
O arquivo `app.py` inicia o Flask com:

- `debug=True`
- porta `5050`

### Arquivos centrais
- `app.py` — ponto de entrada
- `config.py` — configuração e definição dos CSVs
- `services/csv_service.py` — leitura e escrita dos dados
- `services/auth_service.py` — permissões
- `services/grade_service.py` — operações de grade
- `services/alocar_service.py` — alocação automática

## Licença

Projeto acadêmico/particular. Se desejar, adapte esta seção conforme a licença do repositório.

## Autor

Desenvolvido por André Filipi e Gabriel Ferraz
