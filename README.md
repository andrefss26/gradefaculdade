# Grade Faculdade 

Aplicação web em Flask para gerenciamento de grade horária escolar usando arquivos CSV como persistência.

## Visão geral

Este projeto oferece:

- Autenticação de usuários (login, logout e alteração de senha)
- Dashboard com resumo de entidades
- Cadastro e CRUD de professores, disciplinas, turmas, salas e horários
- Gestão da grade de aulas com verificação de conflitos
- Exportação de grade em CSV filtrada por turma ou professor
- Persistência simples em arquivos CSV localizados em `data/`

## Tecnologias

- Python
- Flask
- pandas
- HTML/CSS/JavaScript simples (templates em `templates/`)

## Estrutura do projeto

- `app.py` - ponto de entrada da aplicação
- `config.py` - configuração de caminhos e cabeçalhos dos CSVs
- `routes/` - rotas de autenticação, dashboard, cadastros e grade
- `services/` - lógica de negócio e acesso a arquivos CSV
- `templates/` - páginas HTML do login e dashboard
- `static/` - arquivos estáticos CSS e JavaScript
- `data/` - arquivos CSV usados como banco de dados

## Dependências

Instale as dependências com pip:

```bash
pip install flask pandas
```

> Se estiver usando um ambiente virtual, ative-o antes de instalar as dependências.

## Como rodar

1. Abra o terminal na pasta do projeto.
2. Execute:

```bash
python app.py
```

3. Acesse em `http://127.0.0.1:5050`.

Ao iniciar, o projeto cria os arquivos CSV em `data/` se eles não existirem e popula dados de demonstração.

## Usuários de demonstração

- `admin@escola.com` / `admin123`
- `carlos@escola.com` / `carlos123`
- `coord@escola.com` / `coord123`

## Endpoints principais

### Autenticação

- `GET /login` - página de login
- `POST /api/login` - autentica usuário
- `POST /api/logout` - encerra sessão
- `PUT /api/senha` - altera a senha do usuário logado

### Dashboard

- `GET /dashboard` - página principal do sistema
- `GET /api/resumo` - resumo de totais (professores, turmas, disciplinas, salas, aulas, alunos)

### Cadastro de entidades

- `GET /api/<entidade>` - lista todos os registros de `professores`, `disciplinas`, `turmas`, `salas` ou `horarios`
- `POST /api/<entidade>` - cria um novo registro
- `PUT /api/<entidade>/<id>` - atualiza um registro existente
- `DELETE /api/<entidade>/<id>` - remove um registro

### Grade horária

- `GET /api/grade` - retorna a grade de aulas para exibição
- `POST /api/verificar_conflito` - valida conflito de horário antes de salvar
- `POST /api/aulas` - cria uma nova aula
- `PUT /api/aulas/<id>` - edita uma aula existente
- `DELETE /api/aulas/<id>` - exclui uma aula
- `GET /api/exportar/<tipo>` - exporta a grade em CSV (`tipo` = `turma` ou `professor`)

## Observações

- Os dados são armazenados em CSVs e não há banco de dados relacional.
- A aplicação roda em modo de desenvolvimento com `debug=True`.
- Para uso em produção, ajuste a configuração do Flask e a chave secreta em `config.py`.
