// ── State ────────────────────────────────────────────────────────────────────
const S = {
  professores: [], disciplinas: [], turmas: [],
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
  if (page === "salas")        loadSalas();
  if (page === "horarios")     loadHorariosInst();
  if (page === "grade")        loadGrade();
  if (page === "aulas")        loadAulas();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
async function bootstrap() {
  await Promise.all([
    api("/api/professores").then(r=>r.json()).then(d=>S.professores=d),
    api("/api/disciplinas").then(r=>r.json()).then(d=>S.disciplinas=d),
    api("/api/turmas").then(r=>r.json()).then(d=>S.turmas=d),
    api("/api/salas").then(r=>r.json()).then(d=>S.salas=d),
    api("/api/horarios").then(r=>r.json()).then(d=>S.horarios=d),
  ]);
  navTo("dashboard");
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
    tb.innerHTML = `<tr><td colspan="5"><div class="empty-state"><div class="es-icon">👨‍🏫</div><p>Nenhum professor cadastrado.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.professores.map(p => `
    <tr>
      <td>${p.id}</td>
      <td><strong>${p.nome}</strong></td>
      <td>${p.email}</td>
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
    tb.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="es-icon">🏫</div><p>Nenhuma turma cadastrada.</p></div></td></tr>`;
    return;
  }
  tb.innerHTML = S.turmas.map(t => `
    <tr>
      <td>${t.id}</td>
      <td><strong>${t.nome}</strong></td>
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
  openModal("modal-turma");
}

function openEditTurma(id) {
  const t = S.turmas.find(x => String(x.id) === String(id));
  if (!t) return;
  S.editId = id;
  $("modal-turma-title").textContent = "Editar Turma";
  $("turma-nome").value   = t.nome;
  $("turma-alunos").value = t.quantidade_alunos;
  openModal("modal-turma");
}

async function saveTurma() {
  const body = { nome: $("turma-nome").value.trim(), quantidade_alunos: $("turma-alunos").value };
  if (!body.nome) { toast("Informe o nome.", "error"); return; }
  const r = S.editId
    ? await api(`/api/turmas/${S.editId}`, "PUT", body)
    : await api("/api/turmas", "POST", body);
  if (r.ok) { closeModal("modal-turma"); toast("Turma salva!"); loadTurmas(); }
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

  // horarios for selected turno
  let hSlots = S.horarios.filter(h => turno === "todos" || h.turno === turno);
  const ordemDia = ["Segunda","Terca","Quarta","Quinta","Sexta"];
  hSlots = hSlots.sort((a,b) => {
    const di = ordemDia.indexOf(a.dia_semana) - ordemDia.indexOf(b.dia_semana);
    return di !== 0 ? di : a.horario_inicio.localeCompare(b.horario_inicio);
  });

  // unique horario times
  const uniqueTimes = [...new Set(hSlots.map(h => `${h.horario_inicio}–${h.horario_fim}`))];
  const gradeMap = {};
  turnoFilter.forEach(a => {
    const key = `${a.dia}|${a.inicio}–${a.fim}`;
    if (!gradeMap[key]) gradeMap[key] = [];
    gradeMap[key].push(a);
  });

  const wrap = $("grade-container");
  if (!uniqueTimes.length) {
    wrap.innerHTML = `<div class="empty-state"><div class="es-icon">📅</div><p>Nenhum horário institucional encontrado para este turno.</p></div>`;
    return;
  }

  let html = `<div class="grade-table-wrap"><table class="grade-table">
    <thead><tr><th style="min-width:110px">Horário</th>`;
  DIAS.forEach(d => { html += `<th>${DIAS_LABEL[d]}</th>`; });
  html += `</tr></thead><tbody>`;

  uniqueTimes.forEach(time => {
    html += `<tr><td class="grade-day-header" style="font-size:11px;white-space:nowrap">${time.replace("–"," – ")}</td>`;
    DIAS.forEach(dia => {
      const key = `${dia}|${time}`;
      const items = gradeMap[key] || [];
      if (items.length === 0) {
        const slot = S.horarios.find(h => h.dia_semana === dia && `${h.horario_inicio}–${h.horario_fim}` === time);
        const hid = slot ? slot.id : "";
        html += `<td><div class="grade-cell-empty" onclick="openNewAulaModal('${dia}','${hid}')">＋</div></td>`;
      } else {
        html += `<td>`;
        items.forEach(a => {
          html += `<div class="grade-cell ocupada" onclick="openEditAulaModal('${a.id_aula}')">
            <span class="gc-disc">${a.disciplina}</span>
            <span class="gc-turma">${a.turma}</span>
            <span class="gc-prof">${a.professor}</span>
            <span class="gc-sala">${a.sala}</span>
          </div>`;
        });
        html += `</td>`;
      }
    });
    html += `</tr>`;
  });

  html += `</tbody></table></div>`;
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

// ── Senha ─────────────────────────────────────────────────────────────────────
async function salvarSenha() {
  const body = { atual: $("senha-atual").value, nova: $("senha-nova").value };
  if (!body.atual || !body.nova) { toast("Preencha os campos.", "error"); return; }
  if (body.nova.length < 6) { toast("Senha deve ter ao menos 6 caracteres.", "warn"); return; }
  const r = await api("/api/senha", "PUT", body);
  if (r.ok) { toast("Senha alterada!"); $("senha-atual").value=""; $("senha-nova").value=""; }
  else { const d = await r.json(); toast(d.msg || "Erro.", "error"); }
}

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
