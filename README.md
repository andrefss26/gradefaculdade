# GradeEscolar — Sistema de Gerenciamento de Horários Escolares

## Tecnologias
- **Back-end:** Python 3 + Flask
- **Front-end:** HTML5 + CSS3 (Flexbox/Grid) + JavaScript puro
- **Armazenamento:** Arquivos CSV via Pandas

## Instalação e Execução

### 1. Instalar dependências
```bash
pip install flask pandas --break-system-packages
```

### 2. Executar o servidor
```bash
python app.py
```

### 3. Acessar no navegador
```
http://localhost:5050
```

## Acessos de Demonstração

| Perfil       | E-mail                  | Senha      |
|-------------|-------------------------|------------|
| ADM         | admin@escola.com        | admin123   |
| Professor   | carlos@escola.com       | carlos123  |
| Coordenador | coord@escola.com        | coord123   |

## Estrutura do Projeto
```
escola/
├── app.py                  # Back-end Flask (todas as rotas e regras de negócio)
├── data/                   # Arquivos CSV (gerados automaticamente)
│   ├── professores.csv
│   ├── disciplinas.csv
│   ├── turmas.csv
│   ├── salas.csv
│   ├── horarios.csv
│   ├── aulas.csv
│   └── usuarios.csv
├── static/
│   ├── css/style.css       # Estilos globais
│   └── js/app.js           # Lógica front-end
└── templates/
    ├── login.html          # Tela de login
    └── index.html          # Aplicação principal (SPA)
```

## Funcionalidades Implementadas
- Login / logout com controle de sessão
- Dashboard com painel de resumo (professores, turmas, disciplinas, salas, aulas, alunos)
- CRUD completo: Professores, Disciplinas, Turmas, Salas, Horários
- Grade horária visual semanal (Segunda a Sexta)
- Alocação de aulas com clique direto na grade
- Validação de conflitos em tempo real (professor, turma, sala no mesmo horário)
- Edição e exclusão de aulas
- Exportação de grade em CSV (por turma ou por professor)
- Filtros de grade por turno, turma e professor
- Alteração de senha
