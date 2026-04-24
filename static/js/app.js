// ── Estado global ──────────────────────────────────────────────────────────
let _gradeData = [];
let _allData   = { professores:[], disciplinas:[], turmas:[], cursos:[], salas:[], horarios:[] };
let _editingId = null;

// ── Navegação ──────────────────────────────────────────────────────────────
function navTo(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const pg = document.getElementById(page);
  if (pg) pg.classList.add('active');
  document.querySelectorAll(`.nav-item[data-page="${page}"]`).forEach(n => n.classList.add('active'));
  if (page === 'grade')        loadGrade();
  if (page === 'aulas')        loadAulas();
  if (page === 'professores')  loadProfessores();
  if (page === 'disciplinas')  loadDisciplinas();
  if (page === 'turmas')       loadTurmas();
  if (page === 'cursos')       loadCursos();
  if (page === 'salas')        loadSalas();
  if (page === 'horarios')     loadHorarios();
  if (page === 'dashboard')    loadDashboard();
  if (page === 'disponibilidade') loadDisponibilidade();
}

// ── API helper ─────────────────────────────────────────────────────────────
async function api(url, opts = {}) {
  const r = await fetch(url, { headers:{'Content-Type':'application/json'}, ...opts });
  return r.json();
}
async function apiGet(url)       { return api(url); }
async function apiPost(url, d)   { return api(url,{method:'POST',  body:JSON.stringify(d)}); }
async function apiPut(url, d)    { return api(url,{method:'PUT',   body:JSON.stringify(d)}); }
async function apiDelete(url)    { return api(url,{method:'DELETE'}); }

// ── Toast ──────────────────────────────────────────────────────────────────
function toast(msg, type='success') {
  let el = document.getElementById('_toast');
  if (!el) { el=document.createElement('div'); el.id='_toast'; el.className='toast'; document.body.appendChild(el); }
  el.textContent = msg; el.className = `toast show ${type}`;
  setTimeout(() => el.classList.remove('show'), 3000);
}

// ── Modal ──────────────────────────────────────────────────────────────────
function openModal(id)  { const m=document.getElementById(id); if(m){m.style.display='flex'; setTimeout(()=>m.classList.add('open'),10);} }
function closeModal(id) { const m=document.getElementById(id); if(m){m.classList.remove('open'); setTimeout(()=>m.style.display='none',200);} }

// ── Auth ───────────────────────────────────────────────────────────────────
async function logout() {
  await apiPost('/api/logout',{}); window.location.href='/login';
}

// ── Dashboard ──────────────────────────────────────────────────────────────
async function loadDashboard() {
  const d = await apiGet('/api/resumo');
  document.getElementById('stat-profs').textContent   = d.professores ?? '—';
  document.getElementById('stat-turmas').textContent  = d.turmas      ?? '—';
  document.getElementById('stat-discs').textContent   = d.disciplinas ?? '—';
  document.getElementById('stat-salas').textContent   = d.salas       ?? '—';
  document.getElementById('stat-aulas').textContent   = d.aulas       ?? '—';
  document.getElementById('stat-alunos').textContent  = d.alunos      ?? '—';
}

// ── Carga de dados auxiliares ──────────────────────────────────────────────
async function loadAux() {
  const [p,d,t,c,s,h] = await Promise.all([
    apiGet('/api/professores'), apiGet('/api/disciplinas'),
    apiGet('/api/turmas'),      apiGet('/api/cursos'),
    apiGet('/api/salas'),       apiGet('/api/horarios'),
  ]);
  _allData = { professores:p||[], disciplinas:d||[], turmas:t||[], cursos:c||[], salas:s||[], horarios:h||[] };
}

// ── GRADE ──────────────────────────────────────────────────────────────────
async function loadGrade() {
  await loadAux();
  _gradeData = await apiGet('/api/grade');
  populateGradeFilters();
  renderGrade();
}

function populateGradeFilters() {
  const turmasSel = document.getElementById('grade-turma-filter');
  const profsSel  = document.getElementById('grade-prof-filter');
  if (!turmasSel || !profsSel) return;
  const turmas = [...new Set(_gradeData.map(a=>a.turma))].sort();
  const profs  = [...new Set(_gradeData.map(a=>a.professor))].sort();
  turmasSel.innerHTML = '<option value="">Todas as Turmas</option>' + turmas.map(t=>`<option>${t}</option>`).join('');
  profsSel.innerHTML  = '<option value="">Todos os Professores</option>' + profs.map(p=>`<option>${p}</option>`).join('');
}

function renderGrade() {
  const container = document.getElementById('grade-container');
  if (!container) return;
  const turno  = document.getElementById('grade-turno')?.value  || 'todos';
  const turma  = document.getElementById('grade-turma-filter')?.value || '';
  const prof   = document.getElementById('grade-prof-filter')?.value  || '';
  let data = _gradeData.filter(a => {
    if (turno !== 'todos' && a.turno !== turno) return false;
    if (turma && a.turma !== turma) return false;
    if (prof  && a.professor !== prof) return false;
    return true;
  });
  if (!data.length) {
    container.innerHTML = '<div class="empty-state"><div class="es-icon">📅</div><p>Nenhuma aula encontrada.</p></div>';
    return;
  }
  const dias = ['Segunda','Terca','Quarta','Quinta','Sexta','Sabado','Domingo'];
  const diasNome = {'Segunda':'Segunda-feira','Terca':'Terça-feira','Quarta':'Quarta-feira',
                    'Quinta':'Quinta-feira','Sexta':'Sexta-feira','Sabado':'Sábado','Domingo':'Domingo'};
  const porDia = {};
  data.forEach(a => { (porDia[a.dia] = porDia[a.dia]||[]).push(a); });
  container.innerHTML = dias.filter(d=>porDia[d]).map(dia => `
    <div class="day-block">
      <div class="day-header">📆 ${diasNome[dia] || dia}</div>
      <div class="day-slots">
        ${porDia[dia].sort((a,b)=>a.inicio.localeCompare(b.inicio)).map(a => `
          <div class="aula-card ${a.turno==='Noite'?'noite':''}" onclick="openEditAula('${a.id_aula}')">
            <div class="aula-time">⏰ ${a.inicio} – ${a.fim}</div>
            <div class="aula-disc">${a.disciplina}</div>
            <div class="aula-meta">
              <span>👨‍🏫 ${a.professor}</span>
              <span>🏫 ${a.turma} · 🚪 ${a.sala}</span>
            </div>
            <span class="aula-tag ${a.turno==='Noite'?'tag-noite':'tag-manha'}">${a.turno==='Noite'?'Noite':'Manhã'}</span>
          </div>`).join('')}
      </div>
    </div>`).join('');
}

// ── ALOCAÇÃO AUTOMÁTICA ────────────────────────────────────────────────────
async function alocarGradeCompleta() {
  const btn     = document.getElementById('btn-alocar');
  const label   = document.getElementById('btn-alloc-label');
  const spinner = document.getElementById('btn-alloc-spinner');
  const result  = document.getElementById('alloc-result');
  btn.disabled=true; label.style.display='none'; spinner.style.display='inline';
  result.style.display='none';
  try {
    const data = await apiPost('/api/alocar-completo', {});
    let html = '';
    if (data.sucesso) {
      const av = data.avisos?.length
        ? `<div class="alloc-avisos">⚠️ <strong>Avisos:</strong><br>${data.avisos.map(a=>`• ${a}`).join('<br>')}</div>` : '';
      html = `<div class="alloc-result-ok">
        <div class="alloc-res-head">✅ Grade alocada com sucesso!</div>
        <div class="alloc-stats">
          <span class="alloc-stat">📋 ${data.total_aulas} aula(s)</span>
          <span class="alloc-stat">🏫 ${data.turmas_atendidas} turma(s)</span>
          <span class="alloc-stat">📚 ${data.disciplinas_atendidas} disciplina(s)</span>
        </div>${av}</div>`;
      loadGrade();
    } else {
      html = `<div class="alloc-result-err">
        <div class="alloc-res-head">❌ Não foi possível alocar a grade</div>
        <div style="font-size:12px;color:#7f1d1d">${data.mensagem||'Erro desconhecido.'}</div></div>`;
    }
    result.innerHTML=html; result.style.display='block';
  } catch(e) {
    result.innerHTML=`<div class="alloc-result-err"><div class="alloc-res-head">❌ Erro</div><div style="font-size:12px">${e.message}</div></div>`;
    result.style.display='block';
  } finally { btn.disabled=false; label.style.display='inline'; spinner.style.display='none'; }
}

async function clearGrade() {
  if (!confirm('Limpar TODAS as aulas? Esta ação não pode ser desfeita.')) return;
  const r = await apiPost('/api/limpar_grade',{});
  if (r.ok) { toast('Grade limpa.'); loadGrade(); }
  else toast(r.msg||'Erro ao limpar.','error');
}

async function exportGrade(tipo) {
  window.location.href = `/api/exportar/${tipo}`;
}

// ── LISTA DE AULAS ─────────────────────────────────────────────────────────
async function loadAulas() {
  if (!_gradeData.length) _gradeData = await apiGet('/api/grade');
  const tb = document.getElementById('tb-aulas'); if(!tb) return;
  tb.innerHTML = _gradeData.length ? _gradeData.map(a=>`
    <tr>
      <td>${a.id_aula}</td><td>${a.turma}</td><td>${a.disciplina}</td>
      <td>${a.professor}</td><td>${a.sala}</td><td>${a.dia}</td>
      <td>${a.inicio}–${a.fim}</td><td>${a.turno}</td>
      <td>
        <button class="action-btn" onclick="openEditAula('${a.id_aula}')">✏️</button>
        <button class="action-btn del" onclick="deleteAula('${a.id_aula}')">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="9" style="text-align:center;color:#94a3b8">Nenhuma aula cadastrada.</td></tr>';
}

async function deleteAula(id) {
  if (!confirm('Excluir esta aula?')) return;
  const r = await apiDelete(`/api/aulas/${id}`);
  if (r.ok) { toast('Aula excluída.'); loadGrade(); loadAulas(); }
  else toast(r.msg||'Erro.','error');
}

// ── MODAL AULA ─────────────────────────────────────────────────────────────
function _fillAulaSelects() {
  const ps = document.getElementById('aula-prof');
  const ts = document.getElementById('aula-turma');
  const ds = document.getElementById('aula-disc');
  const ss = document.getElementById('aula-sala');
  const hs = document.getElementById('aula-horario');
  if(ps) ps.innerHTML = _allData.professores.map(p=>`<option value="${p.id}">${p.nome}</option>`).join('');
  if(ts) ts.innerHTML = _allData.turmas.map(t=>`<option value="${t.id}">${t.nome}</option>`).join('');
  if(ds) ds.innerHTML = _allData.disciplinas.map(d=>`<option value="${d.id}">${d.nome}</option>`).join('');
  if(ss) ss.innerHTML = _allData.salas.map(s=>`<option value="${s.id}">${s.nome} (cap.${s.capacidade})</option>`).join('');
  if(hs) hs.innerHTML = _allData.horarios.map(h=>`<option value="${h.id}">${h.dia_semana} ${h.horario_inicio}–${h.horario_fim} (${h.turno})</option>`).join('');
}

async function openNewAulaModal(turno, dia) {
  if (!_allData.professores.length) await loadAux();
  _editingId = null;
  document.getElementById('modal-aula-title').textContent = 'Nova Aula';
  document.getElementById('aula-conflitos').style.display = 'none';
  _fillAulaSelects(); openModal('modal-aula');
}

async function openEditAula(id) {
  if (!_allData.professores.length) await loadAux();
  const a = _gradeData.find(x=>x.id_aula===id); if(!a) return;
  _editingId = id;
  document.getElementById('modal-aula-title').textContent = 'Editar Aula';
  document.getElementById('aula-conflitos').style.display = 'none';
  _fillAulaSelects();
  document.getElementById('aula-prof').value    = a.id_professor;
  document.getElementById('aula-turma').value   = a.id_turma;
  document.getElementById('aula-disc').value    = a.id_disciplina;
  document.getElementById('aula-sala').value    = a.id_sala;
  document.getElementById('aula-horario').value = a.id_horario;
  openModal('modal-aula');
}

async function checkConflito() {
  const d = _aulaFormData();
  const r = await apiPost('/api/verificar_conflito', {...d, excluir_id: _editingId||''});
  const el = document.getElementById('aula-conflitos');
  if (r.conflitos?.length) { el.style.display='block'; el.textContent='⚠️ '+r.conflitos.join(' | '); }
  else el.style.display = 'none';
}

function _aulaFormData() {
  return {
    id_professor:  document.getElementById('aula-prof')?.value,
    id_turma:      document.getElementById('aula-turma')?.value,
    id_disciplina: document.getElementById('aula-disc')?.value,
    id_sala:       document.getElementById('aula-sala')?.value,
    id_horario:    document.getElementById('aula-horario')?.value,
  };
}

async function saveAula() {
  const d = _aulaFormData();
  let r;
  if (_editingId) r = await apiPut(`/api/aulas/${_editingId}`, d);
  else            r = await apiPost('/api/aulas', d);
  if (r.ok) { toast(_editingId?'Aula atualizada.':'Aula criada.'); closeModal('modal-aula'); loadGrade(); loadAulas(); }
  else if (r.conflitos?.length) {
    const el = document.getElementById('aula-conflitos');
    el.style.display='block'; el.textContent='❌ '+r.conflitos.join(' | ');
  } else toast(r.msg||'Erro.','error');
}

// ── PROFESSORES ────────────────────────────────────────────────────────────
async function loadProfessores() {
  const data = await apiGet('/api/professores');
  const turmas = (await apiGet('/api/turmas'))||[];
  const tb = document.getElementById('tb-professores'); if(!tb) return;
  tb.innerHTML = data.length ? data.map(p=>`
    <tr>
      <td>${p.id}</td><td>${p.nome}</td><td>${p.email||'—'}</td>
      <td>${p.turma||'—'}</td><td>${p.dias_disponiveis||'—'}</td>
      <td>${p.max_aulas_dia||'—'}</td>
      <td>
        <button class="action-btn" onclick="openEditProf('${p.id}')">✏️</button>
        <button class="action-btn del" onclick="delItem('professores','${p.id}',loadProfessores)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="7" style="text-align:center;color:#94a3b8">Nenhum professor.</td></tr>';
}

function openNewProf() {
  _editingId = null;
  document.getElementById('modal-prof-title').textContent = 'Novo Professor';
  document.getElementById('prof-nome').value  = '';
  document.getElementById('prof-email').value = '';
  document.getElementById('prof-max').value   = '6';
  document.querySelectorAll('.dia-check').forEach(c=>c.checked=false);
  openModal('modal-prof');
}

function openEditProf(id) {
  apiGet('/api/professores').then(data => {
    const p = data.find(x=>x.id===id); if(!p) return;
    _editingId = id;
    document.getElementById('modal-prof-title').textContent = 'Editar Professor';
    document.getElementById('prof-nome').value  = p.nome||'';
    document.getElementById('prof-email').value = p.email||'';
    document.getElementById('prof-max').value   = p.max_aulas_dia||'6';
    const dias = (p.dias_disponiveis||'').split(',').map(d=>d.trim());
    document.querySelectorAll('.dia-check').forEach(c=>c.checked=dias.includes(c.value));
    openModal('modal-prof');
  });
}

async function saveProf() {
  const dias = [...document.querySelectorAll('.dia-check:checked')].map(c=>c.value);
  const d = { nome:document.getElementById('prof-nome').value,
              email:document.getElementById('prof-email').value,
              max_aulas_dia:document.getElementById('prof-max').value,
              dias_disponiveis:dias.join(',') };
  let r;
  if (_editingId) r = await apiPut(`/api/professores/${_editingId}`, d);
  else            r = await apiPost('/api/professores', d);
  if (r.ok) { toast(_editingId?'Professor atualizado.':'Professor criado.'); closeModal('modal-prof'); loadProfessores(); }
  else toast(r.msg||'Erro.','error');
}

// ── DISCIPLINAS ────────────────────────────────────────────────────────────
async function loadDisciplinas() {
  const [data, profs] = await Promise.all([apiGet('/api/disciplinas'), apiGet('/api/professores')]);
  const profMap = Object.fromEntries((profs||[]).map(p=>[p.id,p.nome]));
  const tb = document.getElementById('tb-disciplinas'); if(!tb) return;
  tb.innerHTML = data.length ? data.map(d=>`
    <tr>
      <td>${d.id}</td><td>${d.nome}</td><td>${d.carga_horaria}h (${d.duracao_blocos} bloco(s))</td>
      <td>${profMap[d.id_professor]||d.id_professor}</td>
      <td>
        <button class="action-btn" onclick="openEditDisc('${d.id}')">✏️</button>
        <button class="action-btn del" onclick="delItem('disciplinas','${d.id}',loadDisciplinas)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="5" style="text-align:center;color:#94a3b8">Nenhuma disciplina.</td></tr>';
}

function openNewDisc() {
  _editingId = null;
  document.getElementById('modal-disc-title').textContent = 'Nova Disciplina';
  document.getElementById('disc-nome').value  = '';
  document.getElementById('disc-carga').value = '4';
  document.getElementById('disc-dur').value   = '1';
  apiGet('/api/professores').then(p => {
    document.getElementById('disc-prof').innerHTML = (p||[]).map(x=>`<option value="${x.id}">${x.nome}</option>`).join('');
  });
  apiGet('/api/cursos').then(c => {
    document.getElementById('disc-curso').innerHTML = (c||[]).map(x=>`<option value="${x.id}">${x.nome}</option>`).join('');
  });
  openModal('modal-disc');
}

function openEditDisc(id) {
  Promise.all([apiGet('/api/disciplinas'), apiGet('/api/professores'), apiGet('/api/cursos')]).then(([discs,profs,cursos])=>{
    const d = discs.find(x=>x.id===id); if(!d) return;
    _editingId = id;
    document.getElementById('modal-disc-title').textContent = 'Editar Disciplina';
    document.getElementById('disc-nome').value  = d.nome||'';
    document.getElementById('disc-carga').value = d.carga_horaria||'4';
    document.getElementById('disc-dur').value   = d.duracao_blocos||'1';
    document.getElementById('disc-prof').innerHTML = (profs||[]).map(p=>`<option value="${p.id}" ${p.id===d.id_professor?'selected':''}>${p.nome}</option>`).join('');
    document.getElementById('disc-curso').innerHTML = (cursos||[]).map(c=>`<option value="${c.id}" ${c.id===d.id_curso?'selected':''}>${c.nome}</option>`).join('');
    openModal('modal-disc');
  });
}

async function saveDisc() {
  const d = { nome:document.getElementById('disc-nome').value,
              carga_horaria:document.getElementById('disc-carga').value,
              duracao_blocos:document.getElementById('disc-dur').value,
              id_professor:document.getElementById('disc-prof').value,
              id_curso:document.getElementById('disc-curso').value };
  let r;
  if (_editingId) r = await apiPut(`/api/disciplinas/${_editingId}`, d);
  else            r = await apiPost('/api/disciplinas', d);
  if (r.ok) { toast('Disciplina salva.'); closeModal('modal-disc'); loadDisciplinas(); }
  else toast(r.msg||'Erro.','error');
}

// ── TURMAS ─────────────────────────────────────────────────────────────────
async function loadTurmas() {
  const [data, cursos] = await Promise.all([apiGet('/api/turmas'), apiGet('/api/cursos')]);
  const cursoMap = Object.fromEntries((cursos||[]).map(c=>[c.id,c.nome]));
  const tb = document.getElementById('tb-turmas'); if(!tb) return;
  tb.innerHTML = data.length ? data.map(t=>`
    <tr>
      <td>${t.id}</td><td>${t.nome}</td><td>${cursoMap[t.id_curso]||t.id_curso}</td>
      <td>${t.quantidade_alunos}</td>
      <td>
        <button class="action-btn" onclick="openEditTurma('${t.id}')">✏️</button>
        <button class="action-btn del" onclick="delItem('turmas','${t.id}',loadTurmas)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="5" style="text-align:center;color:#94a3b8">Nenhuma turma.</td></tr>';
}

function openNewTurma() {
  _editingId = null;
  document.getElementById('modal-turma-title').textContent = 'Nova Turma';
  document.getElementById('turma-nome').value   = '';
  document.getElementById('turma-alunos').value = '';
  apiGet('/api/cursos').then(c => {
    document.getElementById('turma-curso').innerHTML = (c||[]).map(x=>`<option value="${x.id}">${x.nome}</option>`).join('');
  });
  openModal('modal-turma');
}

function openEditTurma(id) {
  Promise.all([apiGet('/api/turmas'), apiGet('/api/cursos')]).then(([turmas,cursos])=>{
    const t = turmas.find(x=>x.id===id); if(!t) return;
    _editingId = id;
    document.getElementById('modal-turma-title').textContent = 'Editar Turma';
    document.getElementById('turma-nome').value   = t.nome||'';
    document.getElementById('turma-alunos').value = t.quantidade_alunos||'';
    document.getElementById('turma-curso').innerHTML = (cursos||[]).map(c=>`<option value="${c.id}" ${c.id===t.id_curso?'selected':''}>${c.nome}</option>`).join('');
    openModal('modal-turma');
  });
}

async function saveTurma() {
  const d = { nome:document.getElementById('turma-nome').value,
              id_curso:document.getElementById('turma-curso').value,
              quantidade_alunos:document.getElementById('turma-alunos').value };
  let r;
  if (_editingId) r = await apiPut(`/api/turmas/${_editingId}`, d);
  else            r = await apiPost('/api/turmas', d);
  if (r.ok) { toast('Turma salva.'); closeModal('modal-turma'); loadTurmas(); }
  else toast(r.msg||'Erro.','error');
}

// ── CURSOS ─────────────────────────────────────────────────────────────────
async function loadCursos() {
  const data = await apiGet('/api/cursos');
  const tb = document.getElementById('tb-cursos'); if(!tb) return;
  tb.innerHTML = data.length ? data.map(c=>`
    <tr>
      <td>${c.id}</td><td>${c.nome}</td>
      <td>
        <button class="action-btn" onclick="openEditCurso('${c.id}')">✏️</button>
        <button class="action-btn del" onclick="delItem('cursos','${c.id}',loadCursos)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="3" style="text-align:center;color:#94a3b8">Nenhum curso.</td></tr>';
}

function openNewCurso() {
  _editingId = null;
  document.getElementById('modal-curso-title').textContent = 'Novo Curso';
  document.getElementById('curso-nome').value = '';
  openModal('modal-curso');
}

function openEditCurso(id) {
  apiGet('/api/cursos').then(data => {
    const c = data.find(x=>x.id===id); if(!c) return;
    _editingId = id;
    document.getElementById('modal-curso-title').textContent = 'Editar Curso';
    document.getElementById('curso-nome').value = c.nome||'';
    openModal('modal-curso');
  });
}

async function saveCurso() {
  const d = { nome: document.getElementById('curso-nome').value };
  let r;
  if (_editingId) r = await apiPut(`/api/cursos/${_editingId}`, d);
  else            r = await apiPost('/api/cursos', d);
  if (r.ok) { toast('Curso salvo.'); closeModal('modal-curso'); loadCursos(); }
  else toast(r.msg||'Erro.','error');
}

// ── SALAS ──────────────────────────────────────────────────────────────────
async function loadSalas() {
  const data = await apiGet('/api/salas');
  const tb = document.getElementById('tb-salas'); if(!tb) return;
  tb.innerHTML = data.length ? data.map(s=>`
    <tr>
      <td>${s.id}</td><td>${s.nome}</td><td>${s.capacidade}</td><td>${s.tipo}</td>
      <td>
        <button class="action-btn" onclick="openEditSala('${s.id}')">✏️</button>
        <button class="action-btn del" onclick="delItem('salas','${s.id}',loadSalas)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="5" style="text-align:center;color:#94a3b8">Nenhuma sala.</td></tr>';
}

function openNewSala() {
  _editingId = null;
  document.getElementById('modal-sala-title').textContent = 'Nova Sala';
  document.getElementById('sala-nome').value = '';
  document.getElementById('sala-cap').value  = '40';
  document.getElementById('sala-tipo').value = 'Sala de Aula';
  openModal('modal-sala');
}

function openEditSala(id) {
  apiGet('/api/salas').then(data => {
    const s = data.find(x=>x.id===id); if(!s) return;
    _editingId = id;
    document.getElementById('modal-sala-title').textContent = 'Editar Sala';
    document.getElementById('sala-nome').value = s.nome||'';
    document.getElementById('sala-cap').value  = s.capacidade||'40';
    document.getElementById('sala-tipo').value = s.tipo||'Sala de Aula';
    openModal('modal-sala');
  });
}

async function saveSala() {
  const d = { nome:document.getElementById('sala-nome').value,
              capacidade:document.getElementById('sala-cap').value,
              tipo:document.getElementById('sala-tipo').value };
  let r;
  if (_editingId) r = await apiPut(`/api/salas/${_editingId}`, d);
  else            r = await apiPost('/api/salas', d);
  if (r.ok) { toast('Sala salva.'); closeModal('modal-sala'); loadSalas(); }
  else toast(r.msg||'Erro.','error');
}

// ── HORÁRIOS ───────────────────────────────────────────────────────────────
async function loadHorarios() {
  const data = await apiGet('/api/horarios');
  const dias = {'Segunda':1,'Terca':2,'Quarta':3,'Quinta':4,'Sexta':5,'Sabado':6,'Domingo':7};
  const sorted = [...data].sort((a,b)=>(dias[a.dia_semana]||9)-(dias[b.dia_semana]||9)||a.horario_inicio.localeCompare(b.horario_inicio));
  const tb = document.getElementById('tb-horarios'); if(!tb) return;
  tb.innerHTML = sorted.length ? sorted.map(h=>`
    <tr>
      <td>${h.id}</td><td>${h.turno}</td><td>${h.dia_semana}</td>
      <td>${h.horario_inicio}</td><td>${h.horario_fim}</td>
      <td>
        <button class="action-btn del" onclick="delItem('horarios','${h.id}',loadHorarios)">🗑️</button>
      </td>
    </tr>`).join('') : '<tr><td colspan="6" style="text-align:center;color:#94a3b8">Nenhum slot.</td></tr>';
}

function openNewHorario() {
  openModal('modal-horario');
}

async function saveHorario() {
  const d = { turno:document.getElementById('hor-turno').value,
              dia_semana:document.getElementById('hor-dia').value,
              horario_inicio:document.getElementById('hor-inicio').value,
              horario_fim:document.getElementById('hor-fim').value };
  const r = await apiPost('/api/horarios', d);
  if (r.ok) { toast('Slot criado.'); closeModal('modal-horario'); loadHorarios(); }
  else toast(r.msg||'Erro.','error');
}

// ── DELETE GENÉRICO ────────────────────────────────────────────────────────
async function delItem(entidade, id, cb) {
  if (!confirm('Excluir este registro?')) return;
  const r = await apiDelete(`/api/${entidade}/${id}`);
  if (r.ok) { toast('Excluído.'); cb(); }
  else toast(r.msg||'Erro.','error');
}

// ── DISPONIBILIDADE (professor) ────────────────────────────────────────────
async function loadDisponibilidade() {
  const uid = window._user?.id_vinculo || window._user?.id;
  if (!uid) return;
  const profs = await apiGet('/api/professores');
  const prof  = profs.find(p => p.id === uid);
  if (!prof) return;
  const dias  = (prof.dias_disponiveis||'').split(',').map(d=>d.trim());
  document.querySelectorAll('.dia-btn').forEach(b => {
    b.classList.toggle('sel', dias.includes(b.dataset.dia));
  });
}

async function saveDisponibilidade() {
  const uid  = window._user?.id_vinculo || window._user?.id;
  const dias = [...document.querySelectorAll('.dia-btn.sel')].map(b=>b.dataset.dia);
  const r    = await apiPut(`/api/professores/${uid}/disponibilidade`, { dias });
  if (r.ok) toast('Disponibilidade atualizada!')
  else toast(r.msg||'Erro.','error');
}

// ── Fechar modal ao clicar fora ────────────────────────────────────────────
document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
    setTimeout(()=>e.target.style.display='none',200);
  }
});
