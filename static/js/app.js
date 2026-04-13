// ── State ────────────────────────────────────────────────────────────────────
const S = {
  cursos: [], professores: [], disciplinas: [], turmas: [],
  salas: [], horarios: [], aulas: [],
  editId: null, editType: null,
};

// ── Utils ─────────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const byQ = q => document.querySelector(q);

function toast(msg, type = "success") {
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.classList.add("show"), 50);
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 400); }, 3000);
}

async function api(path, method = "GET", body = null) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch(path, opts);
  return r;
}

function fmt(val) { return val || "—"; }

function lookup(arr, id, field = "nome") {
  const item = arr.find(x => String(x.id) === String(id));
  return item ? item[field] : id;
}

// ── Navigation ────────────────────────────────────────────────────────────────
function navTo(page) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  const pg = $(page);
  if (pg) pg.classList.add("active");
  const nav = document.querySelector(`[data-page="${page}"]`);
  if (nav) nav.classList.add("active");
  if (page === "dashboard")    loadDashboard();
  if (page === "professores")  loadProfessores();
  if (page === "disciplinas")  loadDisciplinas();
  if (page === "turmas")       loadTurmas();
  if (page === "cursos")       loadCursos();
  if (page === "salas")        loadSalas();
  if (page === "horarios")     loadHorariosInst();
  if (page === "grade")        loadGrade();
  if (page === "aulas")        loadAulas();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
async function bootstrap() {
  await Promise.all([
    api("/api/cursos").then(r=>r.json()).then(d=>S.cursos=d),
    api("/api/professores").then(r=>r.json()).then(d=>S.professores=d),
    api("/api/disciplinas").then(r=>r.json()).then(d=>S.disciplinas=d),
    api("/api/turmas").then(r=>r.json()).then(d=>S.turmas=d),
    api("/api/salas").then(r=>r.json()).then(d=>S.salas=d),
    api("/api/horarios").then(r=>r.json()).then(d=>S.horarios=d),
  ]);
  navTo(window.START_PAGE || "dashboard");
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  const r = await api("/api/resumo");
  const d = await r.json();
  $("stat-profs").textContent  = d.professores;
  $("stat-turmas").textContent = d.turmas;
  $("stat-discs").textContent  = d.disciplinas;
  $("stat-salas").textContent  = d.salas;
  $("stat-aulas").textContent  = d.aulas;
  $("stat-alunos").textContent = d.alunos;
}

// ── Professores ───────────────────────────────────────────────────────────────
async function loadProfessores() {
  const r = await api("/api/professores");
  S.professores = await r.json();
  const tb = $("tb-professores");
  if (S.professores.length === 0) {
    tb.innerHTML = `<tr><td colspan="7"><div class="empty-state"><div class="es-icon">👨‍🏫</div><p>Nenhum professor cadastrado.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.professores.map(p => `
    <tr>
      <td>${p.id}</td>
      <td><strong>${p.nome}</strong></td>
      <td>${p.email}</td>
      <td>${lookup(S.turmas, p.id_turma, 'nome') || '—'}</td>
      <td><span style="font-size:12px">${(p.dias_disponiveis||"").replace(/,/g,", ")}</span></td>
      <td>${p.max_aulas_dia || "—"}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditProf(${p.id})">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="delItem('professores',${p.id})">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewProf() {
  S.editId = null; S.editType = "professor";
  $("modal-prof-title").textContent = "Novo Professor";
  $("prof-nome").value = ""; $("prof-email").value = "";
  $("prof-max").value = "4";
  $("prof-turma").innerHTML = `<option value="">Nenhuma turma</option>` + S.turmas.map(t => `<option value="${t.id}">${t.nome}</option>`).join("");
  $("prof-turma").value = "";
  document.querySelectorAll(".dia-check").forEach(c => c.checked = false);
  openModal("modal-prof");
}

function openEditProf(id) {
  const p = S.professores.find(x => String(x.id) === String(id));
  if (!p) return;
  S.editId = id; S.editType = "professor";
  $("modal-prof-title").textContent = "Editar Professor";
  $("prof-nome").value  = p.nome;
  $("prof-email").value = p.email;
  $("prof-max").value   = p.max_aulas_dia || 4;
  $("prof-turma").innerHTML = `<option value="">Nenhuma turma</option>` + S.turmas.map(t => `<option value="${t.id}" ${String(t.id)===String(p.id_turma)?'selected':''}>${t.nome}</option>`).join("");
  $("prof-turma").value = p.id_turma || "";
  const dias = (p.dias_disponiveis || "").split(",");
  document.querySelectorAll(".dia-check").forEach(c => {
    c.checked = dias.includes(c.value);
  });
  openModal("modal-prof");
}

async function saveProf() {
  const dias = [...document.querySelectorAll(".dia-check:checked")].map(c => c.value).join(",");
  const body = {
    nome: $("prof-nome").value.trim(),
    email: $("prof-email").value.trim(),
    dias_disponiveis: dias,
    max_aulas_dia: $("prof-max").value,
    id_turma: $("prof-turma").value,
  };
  if (!body.nome || !body.email) { toast("Preencha todos os campos obrigatórios.", "error"); return; }
  let r;
  if (S.editId) {
    r = await api(`/api/professores/${S.editId}`, "PUT", body);
  } else {
    r = await api("/api/professores", "POST", body);
  }
  if (r.ok) { closeModal("modal-prof"); toast("Professor salvo!"); loadProfessores(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Disciplinas ───────────────────────────────────────────────────────────────
async function loadDisciplinas() {
  const r = await api("/api/disciplinas");
  S.disciplinas = await r.json();
  const tb = $("tb-disciplinas");
  if (S.disciplinas.length === 0) {
    tb.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="es-icon">📚</div><p>Nenhuma disciplina cadastrada.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.disciplinas.map(d => `
    <tr>
      <td>${d.id}</td>
      <td><strong>${d.nome}</strong></td>
      <td><span class="badge badge-blue">${d.carga_horaria}h/sem</span></td>
      <td>${lookup(S.professores, d.id_professor)}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditDisc('${d.id}')">✏️ Editar</button>
        <button class="btn btn-success btn-sm" onclick="alocarAutomatico('${d.id}')">⚡ Alocar</button>
        <button class="btn btn-danger btn-sm" onclick="delItem('disciplinas','${d.id}')">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewDisc() {
  S.editId = null;
  $("modal-disc-title").textContent = "Nova Disciplina";
  $("disc-nome").value = ""; $("disc-carga").value = "2";
  populateSelect("disc-prof", S.professores);
  openModal("modal-disc");
}

function openEditDisc(id) {
  const d = S.disciplinas.find(x => String(x.id) === String(id));
  if (!d) return;
  S.editId = id;
  $("modal-disc-title").textContent = "Editar Disciplina";
  $("disc-nome").value  = d.nome;
  $("disc-carga").value = d.carga_horaria;
  populateSelect("disc-prof", S.professores, d.id_professor);
  openModal("modal-disc");
}

async function saveDisc() {
  const body = {
    nome: $("disc-nome").value.trim(),
    carga_horaria: $("disc-carga").value,
    id_professor: $("disc-prof").value,
  };
  if (!body.nome) { toast("Informe o nome.", "error"); return; }
  const r = S.editId
    ? await api(`/api/disciplinas/${S.editId}`, "PUT", body)
    : await api("/api/disciplinas", "POST", body);
  if (r.ok) { closeModal("modal-disc"); toast("Disciplina salva!"); loadDisciplinas(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Turmas ────────────────────────────────────────────────────────────────────
async function loadTurmas() {
  const r = await api("/api/turmas");
  S.turmas = await r.json();
  const tb = $("tb-turmas");
  if (S.turmas.length === 0) {
    tb.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="es-icon">🏫</div><p>Nenhuma turma cadastrada.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.turmas.map(t => `
    <tr>
      <td>${t.id}</td>
      <td><strong>${t.nome}</strong></td>
      <td>${lookup(S.cursos, t.id_curso, 'nome') || '—'}</td>
      <td>${t.quantidade_alunos || "—"}</td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditTurma('${t.id}')">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="delItem('turmas','${t.id}')">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewTurma() {
  S.editId = null;
  $("modal-turma-title").textContent = "Nova Turma";
  $("turma-nome").value = ""; $("turma-alunos").value = "";
  $("turma-curso").innerHTML = `<option value="">Selecione um curso</option>` + S.cursos.map(c => `<option value="${c.id}">${c.nome}</option>`).join("");
  $("turma-curso").value = "";
  openModal("modal-turma");
}

function openEditTurma(id) {
  const t = S.turmas.find(x => String(x.id) === String(id));
  if (!t) return;
  S.editId = id;
  $("modal-turma-title").textContent = "Editar Turma";
  $("turma-nome").value   = t.nome;
  $("turma-alunos").value = t.quantidade_alunos;
  $("turma-curso").innerHTML = `<option value="">Selecione um curso</option>` + S.cursos.map(c => `<option value="${c.id}" ${String(c.id)===String(t.id_curso)?'selected':''}>${c.nome}</option>`).join("");
  $("turma-curso").value = t.id_curso || "";
  openModal("modal-turma");
}

async function saveTurma() {
  const body = { nome: $("turma-nome").value.trim(), quantidade_alunos: $("turma-alunos").value, id_curso: $("turma-curso").value };
  if (!body.nome || !body.id_curso) { toast("Preencha todos os campos obrigatórios.", "error"); return; }
  const r = S.editId
    ? await api(`/api/turmas/${S.editId}`, "PUT", body)
    : await api("/api/turmas", "POST", body);
  if (r.ok) { closeModal("modal-turma"); toast("Turma salva!"); loadTurmas(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Cursos ────────────────────────────────────────────────────────────────────
async function loadCursos() {
  const r = await api("/api/cursos");
  S.cursos = await r.json();
  const tb = $("tb-cursos");
  if (S.cursos.length === 0) {
    tb.innerHTML = `<tr><td colspan="3"><div class="empty-state"><div class="es-icon">📖</div><p>Nenhum curso cadastrado.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.cursos.map(c => `
    <tr>
      <td>${c.id}</td>
      <td><strong>${c.nome}</strong></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditCurso('${c.id}')">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="delItem('cursos','${c.id}')">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewCurso() {
  S.editId = null;
  $("modal-curso-title").textContent = "Novo Curso";
  $("curso-nome").value = "";
  openModal("modal-curso");
}

function openEditCurso(id) {
  const c = S.cursos.find(x => String(x.id) === String(id));
  if (!c) return;
  S.editId = id;
  $("modal-curso-title").textContent = "Editar Curso";
  $("curso-nome").value = c.nome;
  openModal("modal-curso");
}

async function saveCurso() {
  const body = { nome: $("curso-nome").value.trim() };
  if (!body.nome) { toast("Informe o nome.", "error"); return; }
  const r = S.editId
    ? await api(`/api/cursos/${S.editId}`, "PUT", body)
    : await api("/api/cursos", "POST", body);
  if (r.ok) { closeModal("modal-curso"); toast("Curso salvo!"); loadCursos(); loadTurmas(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Salas ─────────────────────────────────────────────────────────────────────
async function loadSalas() {
  const r = await api("/api/salas");
  S.salas = await r.json();
  const tb = $("tb-salas");
  if (S.salas.length === 0) {
    tb.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="es-icon">🚪</div><p>Nenhuma sala cadastrada.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.salas.map(s => `
    <tr>
      <td>${s.id}</td>
      <td><strong>${s.nome}</strong></td>
      <td>${s.capacidade}</td>
      <td><span class="badge ${s.tipo==='Laboratorio'?'badge-purple':'badge-blue'}">${s.tipo}</span></td>
      <td>
        <button class="btn btn-outline btn-sm" onclick="openEditSala('${s.id}')">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="delItem('salas','${s.id}')">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewSala() {
  S.editId = null;
  $("modal-sala-title").textContent = "Nova Sala";
  $("sala-nome").value = ""; $("sala-cap").value = "40"; $("sala-tipo").value = "Sala de Aula";
  openModal("modal-sala");
}

function openEditSala(id) {
  const s = S.salas.find(x => String(x.id) === String(id));
  if (!s) return;
  S.editId = id;
  $("modal-sala-title").textContent = "Editar Sala";
  $("sala-nome").value = s.nome; $("sala-cap").value = s.capacidade; $("sala-tipo").value = s.tipo;
  openModal("modal-sala");
}

async function saveSala() {
  const body = { nome: $("sala-nome").value.trim(), capacidade: $("sala-cap").value, tipo: $("sala-tipo").value };
  if (!body.nome) { toast("Informe o nome.", "error"); return; }
  const r = S.editId
    ? await api(`/api/salas/${S.editId}`, "PUT", body)
    : await api("/api/salas", "POST", body);
  if (r.ok) { closeModal("modal-sala"); toast("Sala salva!"); loadSalas(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Horários Institucionais ────────────────────────────────────────────────────
async function loadHorariosInst() {
  const r = await api("/api/horarios");
  S.horarios = await r.json();
  const tb = $("tb-horarios");
  if (!S.horarios.length) {
    tb.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="es-icon">🕐</div><p>Nenhum horário cadastrado.</p></div></td></tr>`;
    return;
  }
  const ordem = ["Segunda","Terca","Quarta","Quinta","Sexta","Sabado"];
  const sorted = [...S.horarios].sort((a,b) => {
    const di = ordem.indexOf(a.dia_semana) - ordem.indexOf(b.dia_semana);
    return di !== 0 ? di : a.horario_inicio.localeCompare(b.horario_inicio);
  });
  tb.innerHTML = sorted.map(h => `
    <tr>
      <td>${h.id}</td>
      <td><span class="badge ${h.turno==='Manha'?'badge-orange':'badge-blue'}">${h.turno}</span></td>
      <td>${h.dia_semana}</td>
      <td>${h.horario_inicio}</td>
      <td>${h.horario_fim}</td>
      <td>
        <button class="btn btn-danger btn-sm" onclick="delItem('horarios','${h.id}')">🗑</button>
      </td>
    </tr>`).join("");
}

function openNewHorario() {
  $("hor-turno").value = "Manha"; $("hor-dia").value = "Segunda";
  $("hor-inicio").value = "07:00"; $("hor-fim").value = "07:50";
  openModal("modal-horario");
}

async function saveHorario() {
  const body = {
    turno: $("hor-turno").value, dia_semana: $("hor-dia").value,
    horario_inicio: $("hor-inicio").value, horario_fim: $("hor-fim").value,
  };
  const r = await api("/api/horarios", "POST", body);
  if (r.ok) { closeModal("modal-horario"); toast("Horário salvo!"); loadHorariosInst(); }
  else { toast("Erro ao salvar.", "error"); }
}

// ── Aulas (lista) ─────────────────────────────────────────────────────────────
async function loadAulas() {
  await refreshAll();
  const r = await api("/api/grade");
  const grade = await r.json();
  const tb = $("tb-aulas");
  if (!grade.length) {
    tb.innerHTML = `<tr><td colspan="8"><div class="empty-state"><div class="es-icon">📋</div><p>Nenhuma aula cadastrada. Use a Grade para alocar aulas.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = grade.map(a => `
    <tr>
      <td>${a.id_aula}</td>
      <td><span class="badge badge-green">${a.turma}</span></td>
      <td>${a.disciplina}</td>
      <td>${a.professor}</td>
      <td>${a.sala}</td>
      <td>${a.dia}</td>
      <td>${a.inicio} – ${a.fim}</td>
      <td><span class="badge ${a.turno==='Manha'?'badge-orange':'badge-blue'}">${a.turno}</span></td>
      <td>
        <button class="btn btn-warning btn-sm" onclick="editAulaFromList('${a.id_aula}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="delAula('${a.id_aula}')">🗑</button>
      </td>
    </tr>`).join("");
}

async function delAula(id) {
  if (!confirm("Remover esta aula?")) return;
  const r = await api(`/api/aulas/${id}`, "DELETE");
  if (r.ok) { toast("Aula removida!"); loadAulas(); loadGrade(); }
  else toast("Erro.", "error");
}

// ── Alocação Automática ───────────────────────────────────────────────────────
async function alocarAutomatico(id_disc) {
  if (!confirm("Alocar aulas automaticamente para esta disciplina?")) return;
  const r = await api(`/api/alocar-automatico/${id_disc}`, "POST");
  if (r.ok) {
    const d = await r.json();
    toast(`✓ ${d.msg}`);
    loadGrade();
    loadAulas();
    loadDisciplinas();
  } else {
    const d = await r.json();
    toast(d.msg || "Erro ao alocar.", "error");
  }
}

async function clearGrade() {
  if (!confirm("Limpar toda a grade horária?")) return;
  const r = await api("/api/grade/limpar", "POST");
  if (r.ok) {
    toast("Grade limpa com sucesso.");
    loadGrade();
    loadAulas();
  } else {
    toast("Erro ao limpar grade.", "error");
  }
}

async function alocarTudo() {
  if (!confirm("Alocar todas as disciplinas automaticamente?")) return;
  const r = await api("/api/alocar-todos", "POST");
  if (r.ok) {
    const d = await r.json();
    toast("✓ " + d.msg);
    loadGrade();
    loadAulas();
    loadDisciplinas();
  } else {
    const d = await r.json();
    toast(d.msg || "Erro ao alocar.", "error");
  }
}

// ── Grade Visual ──────────────────────────────────────────────────────────────
const DIAS  = ["Segunda","Terca","Quarta","Quinta","Sexta"];
const DIAS_LABEL = { Segunda:"Segunda",Terca:"Terça",Quarta:"Quarta",Quinta:"Quinta",Sexta:"Sexta" };

async function loadGrade() {
  await refreshAll();
  renderGrade();
}

async function refreshAll() {
  const [rP, rD, rT, rS, rH] = await Promise.all([
    api("/api/professores"), api("/api/disciplinas"),
    api("/api/turmas"), api("/api/salas"), api("/api/horarios"),
  ]);
  S.professores  = await rP.json();
  S.disciplinas  = await rD.json();
  S.turmas       = await rT.json();
  S.salas        = await rS.json();
  S.horarios     = await rH.json();
  populateGradeFilters();
}

function populateGradeFilters() {
  const turnoSel  = $("grade-turno");
  const turmaSel  = $("grade-turma-filter");
  const profSel   = $("grade-prof-filter");
  const curTurno  = turnoSel.value;
  const curTurma  = turmaSel.value;
  const curProf   = profSel.value;

  turmaSel.innerHTML = `<option value="">Todas as Turmas</option>` +
    S.turmas.map(t => `<option value="${t.id}">${t.nome}</option>`).join("");
  profSel.innerHTML = `<option value="">Todos os Professores</option>` +
    S.professores.map(p => `<option value="${p.id}">${p.nome}</option>`).join("");

  if (curTurno) turnoSel.value = curTurno;
  if (curTurma) turmaSel.value = curTurma;
  if (curProf)  profSel.value  = curProf;
}

async function renderGrade() {
  const turno     = $("grade-turno").value;
  const turmaFilt = $("grade-turma-filter").value;
  const profFilt  = $("grade-prof-filter").value;

  const r = await api("/api/grade");
  let grade = await r.json();
  S.grade = grade;

  // filter
  if (turmaFilt) grade = grade.filter(a => String(a.id_turma) === String(turmaFilt));
  if (profFilt)  grade = grade.filter(a => String(a.id_professor) === String(profFilt));
  const turnoFilter = turno !== "todos" ? grade.filter(a => a.turno === turno) : grade;

  const ordemDia = ["Segunda","Terca","Quarta","Quinta","Sexta"];
  const DIAS_LABEL_COMPLETO = { 
    Segunda:"Segunda", Terca:"Terça", Quarta:"Quarta", 
    Quinta:"Quinta", Sexta:"Sexta" 
  };

  const filteredGrade = turno !== "todos" ? turnoFilter : grade;
  const manha = filteredGrade.filter(a => a.turno === "Manha");
  const noite = filteredGrade.filter(a => a.turno === "Noite");

  const buildDayGroups = aulas => {
    const grupos = {};
    ordemDia.forEach(d => grupos[d] = []);
    aulas.forEach(a => { if (grupos[a.dia]) grupos[a.dia].push(a); });
    ordemDia.forEach(dia => grupos[dia].sort((a, b) => a.inicio.localeCompare(b.inicio)));
    return grupos;
  };

  const renderShiftSection = (turnoNome, aulasTurno) => {
    const aulaPorDia = buildDayGroups(aulasTurno);
    let section = `
      <div class="grade-shift-section">
        <div class="grade-shift-title">Grade de ${turnoNome}</div>
        <div class="grade-cards-container">
    `;

    ordemDia.forEach(dia => {
      const aulas = aulaPorDia[dia] || [];
      section += `<div class="grade-day-column">
        <div class="grade-day-title">${DIAS_LABEL_COMPLETO[dia]}</div>
        <div class="grade-aulas-list">`;

      if (aulas.length === 0) {
        section += `<div class="grade-day-empty">Nenhuma aula neste período</div>`;
      } else {
        aulas.forEach(a => {
          section += `<div class="aula-card" onclick="openEditAulaModal('${a.id_aula}')">
            <div class="aula-card-time">${a.inicio} às ${a.fim}</div>
            <div class="aula-card-disc"><strong>${a.disciplina}</strong></div>
            <div class="aula-card-prof">Prof: ${a.professor}</div>
            <div class="aula-card-turma">Turma: ${a.turma}</div>
            <div class="aula-card-sala">Sala: ${a.sala}</div>
          </div>`;
        });
      }

      section += `</div></div>`;
    });

    section += `</div></div>`;
    return section;
  };

  const wrap = $("grade-container");
  let html = "";

  if (turno === "todos" || turno === "Manha") {
    html += renderShiftSection("Manhã", manha);
  }
  if (turno === "todos" || turno === "Noite") {
    html += renderShiftSection("Noite", noite);
  }

  if (!html) {
    html = `<div class="empty-state"><div class="es-icon">📅</div><p>Nenhuma aula disponível para este filtro.</p></div>`;
  }

  wrap.innerHTML = html;
}

// ── Aula Modal ────────────────────────────────────────────────────────────────
function openNewAulaModal(dia, hid) {
  S.editId = null;
  $("modal-aula-title").textContent = "Nova Aula";
  populateSelect("aula-prof",   S.professores);
  populateSelect("aula-turma",  S.turmas);
  populateSelect("aula-sala",   S.salas);
  populateSelect("aula-disc",   S.disciplinas);
  populateHorarioSelect("aula-horario", S.horarios, hid);
  $("aula-conflitos").style.display = "none";
  openModal("modal-aula");
}

function openEditAulaModal(id) {
  const a = (S.grade||[]).find(x => String(x.id_aula) === String(id));
  if (!a) return;
  S.editId = id;
  $("modal-aula-title").textContent = "Editar Aula";
  populateSelect("aula-prof",   S.professores, a.id_professor);
  populateSelect("aula-turma",  S.turmas,      a.id_turma);
  populateSelect("aula-sala",   S.salas,       a.id_sala);
  populateSelect("aula-disc",   S.disciplinas, a.id_disciplina);
  populateHorarioSelect("aula-horario", S.horarios, a.id_horario);
  $("aula-conflitos").style.display = "none";
  openModal("modal-aula");
}

async function editAulaFromList(id) {
  await refreshAll();
  const r = await api("/api/grade");
  S.grade = await r.json();
  openEditAulaModal(id);
}

function populateHorarioSelect(selId, horarios, selected) {
  const sel = $(selId);
  const ordemDia = ["Segunda","Terca","Quarta","Quinta","Sexta"];
  const sorted = [...horarios].sort((a,b) => {
    const di = ordemDia.indexOf(a.dia_semana) - ordemDia.indexOf(b.dia_semana);
    return di !== 0 ? di : a.horario_inicio.localeCompare(b.horario_inicio);
  });
  sel.innerHTML = sorted.map(h =>
    `<option value="${h.id}" ${String(h.id)===String(selected)?'selected':''}>
      ${h.dia_semana} | ${h.turno} | ${h.horario_inicio}–${h.horario_fim}
    </option>`).join("");
}

async function checkConflito() {
  const body = {
    id_professor: $("aula-prof").value,
    id_turma:     $("aula-turma").value,
    id_sala:      $("aula-sala").value,
    id_horario:   $("aula-horario").value,
    excluir_id:   S.editId || "",
  };
  const r = await api("/api/verificar_conflito", "POST", body);
  const d = await r.json();
  const box = $("aula-conflitos");
  if (d.conflitos.length) {
    box.style.display = "block";
    box.innerHTML = `⚠️ <strong>Conflitos detectados:</strong><ul>${d.conflitos.map(c=>`<li>${c}</li>`).join("")}</ul>`;
  } else {
    box.style.display = "none";
  }
}

async function saveAula() {
  const body = {
    id_professor:  $("aula-prof").value,
    id_turma:      $("aula-turma").value,
    id_sala:       $("aula-sala").value,
    id_disciplina: $("aula-disc").value,
    id_horario:    $("aula-horario").value,
  };
  let r;
  if (S.editId) {
    body.excluir_id = S.editId;
    r = await api(`/api/aulas/${S.editId}`, "PUT", body);
  } else {
    r = await api("/api/aulas", "POST", body);
  }
  if (r.ok) {
    closeModal("modal-aula");
    toast("Aula salva com sucesso!");
    renderGrade();
    loadDashboard();
  } else {
    const d = await r.json();
    const box = $("aula-conflitos");
    box.style.display = "block";
    box.innerHTML = `⚠️ <strong>Não foi possível salvar:</strong><ul>${(d.conflitos||["Erro desconhecido"]).map(c=>`<li>${c}</li>`).join("")}</ul>`;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function populateSelect(selId, items, selected) {
  const sel = $(selId);
  sel.innerHTML = items.map(i =>
    `<option value="${i.id}" ${String(i.id)===String(selected)?'selected':''}>${i.nome}</option>`
  ).join("");
}

async function delItem(entity, id) {
  if (!confirm("Confirmar exclusão?")) return;
  const r = await api(`/api/${entity}/${id}`, "DELETE");
  if (r.ok) {
    toast("Removido com sucesso!");
    if (entity === "professores") loadProfessores();
    if (entity === "disciplinas") loadDisciplinas();
    if (entity === "turmas")      loadTurmas();
    if (entity === "salas")       loadSalas();
    if (entity === "horarios")    loadHorariosInst();
  } else toast("Erro ao remover.", "error");
}

// ── Export ────────────────────────────────────────────────────────────────────
function exportGrade(tipo) {
  const filtro = tipo === "turma"
    ? $("grade-turma-filter").value
    : $("grade-prof-filter").value;
  window.location = `/api/exportar/${tipo}?valor=${encodeURIComponent(filtro)}`;
}

// ── Logout ────────────────────────────────────────────────────────────────────
async function logout() {
  await api("/api/logout", "POST");
  window.location = "/login";
}

// ── Modal helpers ─────────────────────────────────────────────────────────────
function openModal(id) {
  const m = $(id);
  m.style.display = "flex";
  setTimeout(() => m.style.opacity = "1", 10);
}
function closeModal(id) {
  const m = $(id);
  m.style.opacity = "0";
  setTimeout(() => m.style.display = "none", 200);
}

// close on overlay click
document.addEventListener("click", e => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.style.opacity = "0";
    setTimeout(() => e.target.style.display = "none", 200);
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener("DOMContentLoaded", bootstrap);
