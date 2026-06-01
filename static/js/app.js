'use strict';
// ── State ─────────────────────────────────────────────────────────────────────
const S = { profs:[], discs:[], turmas:[], salas:[], hors:[], grade:[], editId:null };
const $ = id => document.getElementById(id);
const q = sel => document.querySelector(sel);

// ── API ───────────────────────────────────────────────────────────────────────
async function api(path, method='GET', body=null) {
  const o = { method, headers:{'Content-Type':'application/json'} };
  if (body) o.body = JSON.stringify(body);
  return fetch(path, o);
}
function lk(arr, id, f='nome') {
  const i = arr.find(x => String(x.id) === String(id));
  return i ? i[f] : String(id);
}

// ── Toast ─────────────────────────────────────────────────────────────────────
function toast(msg, type='s') {
  const t = document.createElement('div');
  t.className = `toast ${type}`; t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(()=>t.classList.add('show'), 30);
  setTimeout(()=>{ t.classList.remove('show'); setTimeout(()=>t.remove(),350); }, 3500);
}

// ── Nav ───────────────────────────────────────────────────────────────────────
function navTo(page) {
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  const pg=$('pg-'+page); if(pg) pg.classList.add('active');
  const ni=q(`[data-page="${page}"]`); if(ni) ni.classList.add('active');
  const fns = {
    dashboard:   loadDash,
    grade:       loadGrade,
    aulas:       loadAulasList,
    professores: loadProfs,
    disciplinas: loadDiscs,
    turmas:      loadTurmas,
    salas:       loadSalas,
    horarios:    loadHors,
    senha:       ()=>{},
  };
  if (fns[page]) fns[page]();
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────
async function boot() {
  await reload();
  navTo('dashboard');
}

async function reload() {
  const [rP,rD,rT,rS,rH] = await Promise.all([
    api('/api/professores'), api('/api/disciplinas'),
    api('/api/turmas'), api('/api/salas'), api('/api/horarios'),
  ]);
  S.profs  = await rP.json();
  S.discs  = await rD.json();
  S.turmas = await rT.json();
  S.salas  = await rS.json();
  S.hors   = await rH.json();
  populateFilters();
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
async function loadDash() {
  const d = await api('/api/resumo').then(r=>r.json());
  $('s-profs').textContent  = d.professores;
  $('s-turmas').textContent = d.turmas;
  $('s-discs').textContent  = d.disciplinas;
  $('s-salas').textContent  = d.salas;
  $('s-aulas').textContent  = d.aulas;
  $('s-alunos').textContent = d.alunos;
}

// ── Loading overlay ───────────────────────────────────────────────────────────
const STEPS = [
  'Limpando grade anterior',
  'Identificando turmas por curso',
  'Embaralhando professores (rotação)',
  'Alocando turmas A e B',
  'Alocando turmas C e D',
  'Verificando conflitos',
  'Salvando grade completa',
];

function showLoading() {
  const ov = $('loading-ov');
  $('prog-bar').style.width = '0%';
  $('prog-pct').textContent = '0%';
  $('load-steps-list').innerHTML = STEPS.map((s,i)=>
    `<div class="load-step" id="ls-${i}"><span>⏳</span><span>${s}</span></div>`
  ).join('');
  ov.classList.add('on');
}

function hideLoading() { $('loading-ov').classList.remove('on'); }

function animateLoading(totalMs) {
  const n = STEPS.length;
  const step = totalMs / n;
  let cur = 0;
  function tick() {
    if (cur > 0) {
      const prev = $(`ls-${cur-1}`);
      if (prev) { prev.classList.remove('active'); prev.classList.add('done'); prev.querySelector('span').textContent='✅'; }
    }
    if (cur < n) {
      const el = $(`ls-${cur}`);
      if (el) { el.classList.add('active'); el.querySelector('span').textContent='⚡'; }
      cur++;
      const pct = Math.round(cur/n*100);
      $('prog-bar').style.width = pct+'%';
      $('prog-pct').textContent = pct+'%';
      if (cur < n) setTimeout(tick, step);
    }
  }
  tick();
}

// ── Gerar grade ───────────────────────────────────────────────────────────────
async function gerarGrade() {
  showLoading();
  animateLoading(8500);
  const [res] = await Promise.all([
    api('/api/gerar_grade','POST').then(r=>r.json()),
    new Promise(r=>setTimeout(r,9000)),
  ]);
  STEPS.forEach((_,i)=>{
    const el=$(`ls-${i}`);
    if(el){el.classList.remove('active');el.classList.add('done');el.querySelector('span').textContent='✅';}
  });
  $('prog-bar').style.width='100%'; $('prog-pct').textContent='100%';
  await new Promise(r=>setTimeout(r,500));
  hideLoading();
  if(res.ok){
    const extra = res.turmas_sem && res.turmas_sem.length ? ` ⚠️ Sem cobertura: ${res.turmas_sem.join(', ')}` : '';
    toast(res.msg+extra, extra?'w':'s');
    await reload(); renderGrade(); loadDash();
  } else toast(res.msg||'Erro ao gerar.','e');
}

// ── Grade visual ──────────────────────────────────────────────────────────────
const DIAS = ['Segunda','Terca','Quarta','Quinta','Sexta'];
const DIAS_PT = {Segunda:'Segunda-feira',Terca:'Terça-feira',Quarta:'Quarta-feira',Quinta:'Quinta-feira',Sexta:'Sexta-feira'};
const CURSO_COLOR = {
  'ADS':'#3B5BDB','SI':'#7C3AED','Ciberseguranca':'#059669','Banco de Dados':'#D97706'
};

function populateFilters() {
  const tf=$('f-turma'), pf=$('f-prof');
  const ct=tf.value, cp=pf.value;
  tf.innerHTML='<option value="">Todas as Turmas</option>'+S.turmas.map(t=>`<option value="${t.id}">${t.nome}</option>`).join('');
  pf.innerHTML='<option value="">Todos os Professores</option>'+S.profs.map(p=>`<option value="${p.id}">${p.nome}</option>`).join('');
  if(ct) tf.value=ct; if(cp) pf.value=cp;
}

async function loadGrade() { await reload(); renderGrade(); }

async function renderGrade() {
  let grade = await api('/api/grade').then(r=>r.json());
  S.grade = grade;
  const turno = $('f-turno').value;
  const turmaF= $('f-turma').value;
  const profF = $('f-prof').value;

  if(turno !== 'todos') grade = grade.filter(a=>a.turno===turno);
  if(turmaF) grade = grade.filter(a=>String(a.id_turma)===String(turmaF));
  if(profF)  grade = grade.filter(a=>String(a.id_professor)===String(profF));

  const wrap = $('grade-wrap');
  if(!grade.length){
    wrap.innerHTML=`<div class="empty"><div class="ei">📅</div><p>Nenhuma aula encontrada. Gere a grade ou use os filtros.</p></div>`;
    return;
  }

  // Agrupa por dia
  const byDay = {};
  DIAS.forEach(d=>{ byDay[d]=[]; });
  grade.forEach(a=>{ if(byDay[a.dia]) byDay[a.dia].push(a); });

  let html = '';
  DIAS.forEach(dia=>{
    const aulas = byDay[dia];
    if(!aulas.length) return;
    aulas.sort((a,b)=>a.inicio.localeCompare(b.inicio));
    html += `<div class="grade-day-block">
      <div class="grade-day-header">📅 ${DIAS_PT[dia]}</div>
      <div class="grade-cards-row">`;
    aulas.forEach(a=>{
      const cor = CURSO_COLOR[a.curso] || '#3B5BDB';
      const isNoite = a.turno==='Noite';
      html += `<div class="aula-card ${isNoite?'turno-noite':''}" style="border-left-color:${cor}" onclick="openEditAula('${a.id_aula}')">
        <div class="aula-time">🕐 ${a.inicio} – ${a.fim}</div>
        <div class="aula-disc">${a.disciplina}</div>
        <div class="aula-meta">
          <span>👨‍🏫 ${a.professor}</span>
          <span>🏫 ${a.turma} · 🚪 ${a.sala}</span>
        </div>
        <span class="aula-turno-badge ${isNoite?'noite':'manha'}">${a.turno==='Manha'?'Manhã':'Noite'}</span>
      </div>`;
    });
    // Botão adicionar
    html+=`<div class="add-aula-btn" onclick="openNewAula('${dia}','')">＋</div>`;
    html+=`</div></div>`;
  });
  wrap.innerHTML = html;
}

// ── Modal Aula ────────────────────────────────────────────────────────────────
function openNewAula(dia, hid) {
  S.editId = null;
  $('m-aula-title').textContent = 'Nova Aula';
  sel('m-prof',  S.profs);
  sel('m-turma', S.turmas);
  sel('m-sala',  S.salas);
  sel('m-disc',  S.discs);
  selHor('m-hor', S.hors, hid);
  $('m-conflitos').style.display='none';
  openM('m-aula');
}

function openEditAula(id) {
  const a = S.grade.find(x=>String(x.id_aula)===String(id)); if(!a) return;
  S.editId = id;
  $('m-aula-title').textContent = 'Editar Aula';
  sel('m-prof',  S.profs,  a.id_professor);
  sel('m-turma', S.turmas, a.id_turma);
  sel('m-sala',  S.salas,  a.id_sala);
  sel('m-disc',  S.discs,  a.id_disciplina);
  selHor('m-hor', S.hors, a.id_horario);
  $('m-conflitos').style.display='none';
  openM('m-aula');
}

async function checkConflito() {
  const body = { id_professor:$('m-prof').value, id_turma:$('m-turma').value,
                 id_sala:$('m-sala').value, id_horario:$('m-hor').value, excluir_id:S.editId||'' };
  const d = await api('/api/verificar_conflito','POST',body).then(r=>r.json());
  const box=$('m-conflitos');
  if(d.conflitos.length){
    box.style.display='block';
    box.innerHTML=`⚠️ <strong>Conflitos detectados:</strong><ul>${d.conflitos.map(c=>`<li>${c}</li>`).join('')}</ul>`;
  } else box.style.display='none';
}

async function saveAula() {
  const body = { id_professor:$('m-prof').value, id_turma:$('m-turma').value,
                 id_sala:$('m-sala').value, id_disciplina:$('m-disc').value, id_horario:$('m-hor').value };
  const r = S.editId
    ? await api(`/api/aulas/${S.editId}`,'PUT',{...body,excluir_id:S.editId})
    : await api('/api/aulas','POST',body);
  if(r.ok){ closeM('m-aula'); toast('Aula salva!'); renderGrade(); loadDash(); }
  else {
    const d=await r.json();
    $('m-conflitos').style.display='block';
    $('m-conflitos').innerHTML=`⚠️ <strong>Não foi possível salvar:</strong><ul>${(d.conflitos||['Erro']).map(c=>`<li>${c}</li>`).join('')}</ul>`;
  }
}

async function deleteAulaModal() {
  if(!S.editId||!confirm('Remover esta aula?')) return;
  await api(`/api/aulas/${S.editId}`,'DELETE');
  closeM('m-aula'); toast('Aula removida!','w'); renderGrade(); loadDash();
}

// ── Lista de Aulas ────────────────────────────────────────────────────────────
async function loadAulasList() {
  await reload();
  const grade = await api('/api/grade').then(r=>r.json());
  const tb=$('tb-aulas');
  if(!grade.length){tb.innerHTML=`<tr><td colspan="9"><div class="empty"><div class="ei">📋</div><p>Nenhuma aula alocada.</p></div></td></tr>`;return;}
  tb.innerHTML=grade.map(a=>`<tr>
    <td>${a.id_aula}</td>
    <td><span class="badge b-blue">${a.turma}</span></td>
    <td><span class="badge b-purple">${a.curso}</span></td>
    <td>${a.disciplina}</td><td>${a.professor}</td><td>${a.sala}</td>
    <td>${a.dia}</td><td>${a.inicio}–${a.fim}</td>
    <td><span class="badge ${a.turno==='Manha'?'b-orange':'b-purple'}">${a.turno==='Manha'?'Manhã':'Noite'}</span></td>
    <td>
      <button class="btn btn-ghost btn-sm" onclick="editAulaFromList('${a.id_aula}')">✏️</button>
      <button class="btn btn-danger btn-sm" onclick="delAula('${a.id_aula}')">🗑</button>
    </td>
  </tr>`).join('');
}

async function delAula(id){
  if(!confirm('Remover?')) return;
  await api(`/api/aulas/${id}`,'DELETE');
  toast('Removida!','w'); loadAulasList();
}

async function editAulaFromList(id){
  await reload();
  S.grade = await api('/api/grade').then(r=>r.json());
  openEditAula(id);
}

function parseIds(v){
  return (v||'').split(',').map(x=>String(x).trim()).filter(Boolean);
}
function nomesDisciplinas(ids){
  const arr = parseIds(ids);
  if(!arr.length) return '—';
  return arr.map(id=>lk(S.discs,id)).join(', ');
}
function renderProfDiscChecks(selected=''){
  const box = $('p-discs-box');
  if(!box) return;
  const selIds = new Set(parseIds(selected));
  const ord = [...S.discs].sort((a,b)=>String(a.nome||'').localeCompare(String(b.nome||'')));
  box.innerHTML = ord.map(d=>`<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer"><input type="checkbox" class="p-dcheck" value="${d.id}" ${selIds.has(String(d.id))?'checked':''}>${d.nome} <span style="opacity:.7">(${d.curso||'—'})</span></label>`).join('');
}
function renderTurmaDiscChecks(selected=''){
  const box = $('t-discs-box');
  if(!box) return;
  const curso = $('t-curso') ? $('t-curso').value : '';
  const selIds = new Set(parseIds(selected));
  const base = S.discs.filter(d=>!curso || d.curso===curso);
  const ord = [...base].sort((a,b)=>String(a.nome||'').localeCompare(String(b.nome||'')));
  box.innerHTML = ord.map(d=>`<label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer"><input type="checkbox" class="t-dcheck" value="${d.id}" ${selIds.has(String(d.id))?'checked':''}>${d.nome}</label>`).join('');
}

// ── CRUD Professores ──────────────────────────────────────────────────────────
async function loadProfs(){
  S.profs = await api('/api/professores').then(r=>r.json());
  const tb=$('tb-profs');
  if(!S.profs.length){tb.innerHTML=`<tr><td colspan="7"><div class="empty"><div class="ei">👨‍🏫</div><p>Nenhum professor.</p></div></td></tr>`;return;}
  tb.innerHTML=S.profs.map(p=>`<tr>
    <td>${p.id}</td><td><strong>${p.nome}</strong></td><td>${p.email}</td>
    <td style="font-size:11px">${(p.dias_disponiveis||'').replace(/,/g,', ')}</td>
    <td>${p.max_aulas_dia}</td>
    <td style="font-size:11px">${nomesDisciplinas(p.disciplinas_ids)}</td>
    <td><button class="btn btn-ghost btn-sm" onclick="editProf('${p.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="del('professores','${p.id}',loadProfs)">🗑</button></td>
  </tr>`).join('');
}
function newProf(){ S.editId=null; $('m-prof-title').textContent='Novo Professor';
  $('p-nome').value='';$('p-email').value='';$('p-max').value='4';
  document.querySelectorAll('.dcheck').forEach(c=>c.checked=false);
  renderProfDiscChecks('');
  openM('m-prof'); }
function editProf(id){ const p=S.profs.find(x=>String(x.id)===String(id)); if(!p) return; S.editId=id;
  $('m-prof-title').textContent='Editar Professor'; $('p-nome').value=p.nome; $('p-email').value=p.email; $('p-max').value=p.max_aulas_dia;
  const dias=(p.dias_disponiveis||'').split(',');
  document.querySelectorAll('.dcheck').forEach(c=>c.checked=dias.includes(c.value));
  renderProfDiscChecks(p.disciplinas_ids||'');
  openM('m-prof'); }
async function saveProf(){
  const dias=[...document.querySelectorAll('.dcheck:checked')].map(c=>c.value).join(',');
  const disciplinas_ids=[...document.querySelectorAll('.p-dcheck:checked')].map(c=>c.value).join(',');
  const body={nome:$('p-nome').value.trim(),email:$('p-email').value.trim(),dias_disponiveis:dias,max_aulas_dia:$('p-max').value,disciplinas_ids};
  if(!body.nome||!body.email){toast('Nome e e-mail obrigatórios.','e');return;}
  if(!body.disciplinas_ids){toast('Selecione ao menos uma matéria do professor.','e');return;}
  const r=S.editId?await api(`/api/professores/${S.editId}`,'PUT',body):await api('/api/professores','POST',body);
  if(r.ok){closeM('m-prof');toast('Professor salvo!');loadProfs();}else { const d=await r.json(); toast(d.msg||'Erro.','e'); }
}

// ── CRUD Disciplinas ──────────────────────────────────────────────────────────
async function loadDiscs(){
  S.discs=await api('/api/disciplinas').then(r=>r.json());
  const tb=$('tb-discs');
  if(!S.discs.length){tb.innerHTML=`<tr><td colspan="5"><div class="empty"><div class="ei">📚</div><p>Nenhuma disciplina.</p></div></td></tr>`;return;}
  tb.innerHTML=S.discs.map(d=>`<tr>
    <td>${d.id}</td><td><strong>${d.nome}</strong></td>
    <td><span class="badge b-purple">${d.curso||'—'}</span></td>
    <td><span class="badge b-blue">${d.carga_horaria}h/sem</span></td>
    <td><button class="btn btn-ghost btn-sm" onclick="editDisc('${d.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="del('disciplinas','${d.id}',loadDiscs)">🗑</button></td>
  </tr>`).join('');
}
function newDisc(){S.editId=null;$('m-disc-title').textContent='Nova Disciplina';$('d-nome').value='';$('d-carga').value='2';$('d-curso').value='ADS';openM('m-disc');}
function editDisc(id){const d=S.discs.find(x=>String(x.id)===String(id));if(!d)return;S.editId=id;$('m-disc-title').textContent='Editar Disciplina';$('d-nome').value=d.nome;$('d-carga').value=d.carga_horaria;$('d-curso').value=d.curso||'ADS';openM('m-disc');}
async function saveDisc(){
  const body={nome:$('d-nome').value.trim(),carga_horaria:$('d-carga').value,curso:$('d-curso').value,id_professor:''};
  if(!body.nome){toast('Nome obrigatório.','e');return;}
  const r=S.editId?await api(`/api/disciplinas/${S.editId}`,'PUT',body):await api('/api/disciplinas','POST',body);
  if(r.ok){closeM('m-disc');toast('Disciplina salva!');loadDiscs();}else { const d=await r.json(); toast(d.msg||'Erro.','e'); }
}

// ── CRUD Turmas ───────────────────────────────────────────────────────────────
async function loadTurmas(){
  S.turmas=await api('/api/turmas').then(r=>r.json());
  const tb=$('tb-turmas');
  if(!S.turmas.length){tb.innerHTML=`<tr><td colspan="7"><div class="empty"><div class="ei">🏫</div><p>Nenhuma turma.</p></div></td></tr>`;return;}
  tb.innerHTML=S.turmas.map(t=>`<tr>
    <td>${t.id}</td><td><strong>${t.nome}</strong></td>
    <td><span class="badge b-blue">${t.curso||'—'}</span></td>
    <td><span class="badge ${t.periodo==='Manha'?'b-orange':'b-purple'}">${t.periodo==='Manha'?'Manhã':'Noite'}</span></td>
    <td>${t.quantidade_alunos||'—'}</td>
    <td style="font-size:11px">${nomesDisciplinas(t.disciplinas_exigidas)}</td>
    <td><button class="btn btn-ghost btn-sm" onclick="editTurma('${t.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="del('turmas','${t.id}',loadTurmas)">🗑</button></td>
  </tr>`).join('');
}
function newTurma(){S.editId=null;$('m-turma-title').textContent='Nova Turma';$('t-nome').value='';$('t-curso').value='ADS';$('t-periodo').value='Manha';$('t-semestre').value='1';$('t-alunos').value='';renderTurmaDiscChecks('');openM('m-turma');}
function editTurma(id){const t=S.turmas.find(x=>String(x.id)===String(id));if(!t)return;S.editId=id;$('m-turma-title').textContent='Editar Turma';$('t-nome').value=t.nome;$('t-curso').value=t.curso||'ADS';$('t-periodo').value=t.periodo||'Manha';$('t-semestre').value=t.semestre||'1';$('t-alunos').value=t.quantidade_alunos;renderTurmaDiscChecks(t.disciplinas_exigidas||'');openM('m-turma');}
async function saveTurma(){
  const disciplinas_exigidas=[...document.querySelectorAll('.t-dcheck:checked')].map(c=>c.value).join(',');
  const body={nome:$('t-nome').value.trim(),curso:$('t-curso').value,periodo:$('t-periodo').value,semestre:$('t-semestre').value,quantidade_alunos:$('t-alunos').value,disciplinas_exigidas};
  if(!body.nome){toast('Nome obrigatório.','e');return;}
  if(!body.semestre){toast('Semestre obrigatório.','e');return;}
  if(!body.disciplinas_exigidas){toast('Selecione ao menos uma matéria exigida da turma.','e');return;}
  const r=S.editId?await api(`/api/turmas/${S.editId}`,'PUT',body):await api('/api/turmas','POST',body);
  if(r.ok){closeM('m-turma');toast('Turma salva!');loadTurmas();}else { const d=await r.json(); toast(d.msg||'Erro.','e'); }
}

// ── CRUD Salas ────────────────────────────────────────────────────────────────
async function loadSalas(){
  S.salas=await api('/api/salas').then(r=>r.json());
  const tb=$('tb-salas');
  if(!S.salas.length){tb.innerHTML=`<tr><td colspan="5"><div class="empty"><div class="ei">🚪</div><p>Nenhuma sala.</p></div></td></tr>`;return;}
  tb.innerHTML=S.salas.map(s=>`<tr>
    <td>${s.id}</td><td><strong>${s.nome}</strong></td><td>${s.capacidade}</td>
    <td><span class="badge b-gray">${s.tipo}</span></td>
    <td><button class="btn btn-ghost btn-sm" onclick="editSala('${s.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="del('salas','${s.id}',loadSalas)">🗑</button></td>
  </tr>`).join('');
}
function newSala(){S.editId=null;$('m-sala-title').textContent='Nova Sala';$('sl-nome').value='';$('sl-cap').value='40';$('sl-tipo').value='Sala de Aula';openM('m-sala');}
function editSala(id){const s=S.salas.find(x=>String(x.id)===String(id));if(!s)return;S.editId=id;$('m-sala-title').textContent='Editar Sala';$('sl-nome').value=s.nome;$('sl-cap').value=s.capacidade;$('sl-tipo').value=s.tipo;openM('m-sala');}
async function saveSala(){
  const body={nome:$('sl-nome').value.trim(),capacidade:$('sl-cap').value,tipo:$('sl-tipo').value};
  if(!body.nome){toast('Nome obrigatório.','e');return;}
  const r=S.editId?await api(`/api/salas/${S.editId}`,'PUT',body):await api('/api/salas','POST',body);
  if(r.ok){closeM('m-sala');toast('Sala salva!');loadSalas();}else toast('Erro.','e');
}

// ── CRUD Horários ─────────────────────────────────────────────────────────────
async function loadHors(){
  S.hors=await api('/api/horarios').then(r=>r.json());
  const tb=$('tb-hors');
  if(!S.hors.length){tb.innerHTML=`<tr><td colspan="6"><div class="empty"><div class="ei">🕐</div><p>Nenhum horário.</p></div></td></tr>`;return;}
  const ord={Segunda:0,Terca:1,Quarta:2,Quinta:3,Sexta:4};
  const sorted=[...S.hors].sort((a,b)=>(ord[a.dia_semana]-ord[b.dia_semana])||a.horario_inicio.localeCompare(b.horario_inicio));
  tb.innerHTML=sorted.map(h=>`<tr>
    <td>${h.id}</td>
    <td><span class="badge ${h.turno==='Manha'?'b-orange':'b-purple'}">${h.turno==='Manha'?'Manhã':'Noite'}</span></td>
    <td>${h.dia_semana}</td><td>${h.horario_inicio}</td><td>${h.horario_fim}</td>
    <td><button class="btn btn-danger btn-sm" onclick="del('horarios','${h.id}',loadHors)">🗑</button></td>
  </tr>`).join('');
}
function newHor(){$('h-turno').value='Manha';$('h-dia').value='Segunda';$('h-ini').value='07:00';$('h-fim').value='07:50';openM('m-hor-inst');}
async function saveHor(){
  const body={turno:$('h-turno').value,dia_semana:$('h-dia').value,horario_inicio:$('h-ini').value,horario_fim:$('h-fim').value};
  const r=await api('/api/horarios','POST',body);
  if(r.ok){closeM('m-hor-inst');toast('Slot salvo!');loadHors();}else toast('Erro.','e');
}

// ── Senha ─────────────────────────────────────────────────────────────────────
async function saveSenha(){
  const body={atual:$('s-atual').value,nova:$('s-nova').value};
  if(!body.atual||!body.nova){toast('Preencha os campos.','e');return;}
  if(body.nova.length<6){toast('Mínimo 6 caracteres.','w');return;}
  const r=await api('/api/senha','PUT',body);
  const d=await r.json();
  if(r.ok){toast('Senha alterada!');$('s-atual').value='';$('s-nova').value='';}else toast(d.msg||'Erro.','e');
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function sel(id, items, selected='') {
  $(id).innerHTML = items.map(i=>`<option value="${i.id}" ${String(i.id)===String(selected)?'selected':''}>${i.nome}</option>`).join('');
}
function selHor(id, hors, selected='') {
  const ord={Segunda:0,Terca:1,Quarta:2,Quinta:3,Sexta:4};
  const sorted=[...hors].sort((a,b)=>(ord[a.dia_semana]-ord[b.dia_semana])||a.horario_inicio.localeCompare(b.horario_inicio));
  $(id).innerHTML=sorted.map(h=>`<option value="${h.id}" ${String(h.id)===String(selected)?'selected':''}>${h.dia_semana} | ${h.turno==='Manha'?'Manhã':'Noite'} | ${h.horario_inicio}–${h.horario_fim}</option>`).join('');
}
async function del(ent, id, reload){
  if(!confirm('Confirmar exclusão?')) return;
  await api(`/api/${ent}/${id}`,'DELETE');
  toast('Removido!','w'); reload();
}
function exportar(tipo){
  const v=tipo==='turma'?$('f-turma').value:$('f-prof').value;
  window.location=`/api/exportar/${tipo}?valor=${encodeURIComponent(v)}`;
}
async function logout(){ await api('/api/logout','POST'); window.location='/login'; }

// ── Modal ─────────────────────────────────────────────────────────────────────
function openM(id){ const m=$(id); m.style.display='flex'; requestAnimationFrame(()=>m.classList.add('open')); }
function closeM(id){ const m=$(id); m.classList.remove('open'); setTimeout(()=>m.style.display='none',200); }
document.addEventListener('click',e=>{
  if(e.target.classList.contains('modal-overlay')) closeM(e.target.id);
});

window.addEventListener('DOMContentLoaded', boot);
