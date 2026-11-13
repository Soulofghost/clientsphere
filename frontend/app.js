// ClientSphere CRM Client Application
const API_BASE = '/api/v1';

const STAGES = [
  { id: 'qualified', label: 'Qualified', prob: 20 },
  { id: 'meeting', label: 'Discovery / Meeting', prob: 35 },
  { id: 'proposal', label: 'Formal Proposal', prob: 60 },
  { id: 'negotiation', label: 'Negotiation', prob: 80 },
  { id: 'closed_won', label: 'Closed Won', prob: 100 },
  { id: 'closed_lost', label: 'Closed Lost', prob: 0 }
];

let state = {
  deals: [],
  contacts: [],
  metrics: null,
  searchQuery: ''
};

// Elements
const kpiTotalValue = document.getElementById('kpiTotalValue');
const kpiWeightedValue = document.getElementById('kpiWeightedValue');
const kpiWonValue = document.getElementById('kpiWonValue');
const kpiWinRate = document.getElementById('kpiWinRate');
const kpiActiveCount = document.getElementById('kpiActiveCount');
const pipelineBoard = document.getElementById('pipelineBoard');
const dealSearch = document.getElementById('dealSearch');

// Modals
const dealModal = document.getElementById('dealModal');
const btnNewDeal = document.getElementById('btnNewDeal');
const btnCloseDealModal = document.getElementById('btnCloseDealModal');
const btnCancelDeal = document.getElementById('btnCancelDeal');
const dealForm = document.getElementById('dealForm');
const dealContactSelect = document.getElementById('dealContactSelect');

const contactsModal = document.getElementById('contactsModal');
const btnOpenContacts = document.getElementById('btnOpenContacts');
const btnCloseContactsModal = document.getElementById('btnCloseContactsModal');
const contactForm = document.getElementById('contactForm');
const contactsTableBody = document.getElementById('contactsTableBody');

const activityModal = document.getElementById('activityModal');
const btnCloseActivityModal = document.getElementById('btnCloseActivityModal');
const activityForm = document.getElementById('activityForm');
const activityTimeline = document.getElementById('activityTimeline');
const actDealId = document.getElementById('actDealId');
const actContactId = document.getElementById('actContactId');

// Formatters
const formatCurrency = (val) => '$' + Number(val || 0).toLocaleString('en-US', { maximumFractionDigits: 0 });

// Init
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadAllData();
});

function setupEventListeners() {
  btnNewDeal.addEventListener('click', () => {
    populateContactOptions();
    dealModal.classList.remove('hidden');
  });
  btnCloseDealModal.addEventListener('click', () => dealModal.classList.add('hidden'));
  btnCancelDeal.addEventListener('click', () => dealModal.classList.add('hidden'));

  btnOpenContacts.addEventListener('click', () => {
    renderContactsTable();
    contactsModal.classList.remove('hidden');
  });
  btnCloseContactsModal.addEventListener('click', () => contactsModal.classList.add('hidden'));

  btnCloseActivityModal.addEventListener('click', () => activityModal.classList.add('hidden'));

  dealSearch.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase();
    renderPipeline();
  });

  dealForm.addEventListener('submit', handleCreateDeal);
  contactForm.addEventListener('submit', handleCreateContact);
  activityForm.addEventListener('submit', handleCreateActivity);
}

async function loadAllData() {
  try {
    const [dealsRes, contactsRes, metricsRes] = await Promise.all([
      fetch(`${API_BASE}/deals`).then(r => r.json()),
      fetch(`${API_BASE}/contacts`).then(r => r.json()),
      fetch(`${API_BASE}/deals/metrics/forecast`).then(r => r.json())
    ]);

    state.deals = dealsRes;
    state.contacts = contactsRes;
    state.metrics = metricsRes;

    updateKPIs();
    renderPipeline();
  } catch (err) {
    console.error('Failed to load CRM data:', err);
  }
}

function updateKPIs() {
  if (!state.metrics) return;
  kpiTotalValue.textContent = formatCurrency(state.metrics.total_pipeline_value);
  kpiWeightedValue.textContent = formatCurrency(state.metrics.weighted_pipeline_value);
  kpiWonValue.textContent = formatCurrency(state.metrics.closed_won_value);
  kpiWinRate.textContent = `${state.metrics.win_rate_pct}%`;
  kpiActiveCount.textContent = `${state.metrics.total_active_deals} Active Deals`;
}

function renderPipeline() {
  pipelineBoard.innerHTML = '';

  const filteredDeals = state.deals.filter(d => {
    if (!state.searchQuery) return true;
    const matchTitle = d.title.toLowerCase().includes(state.searchQuery);
    const matchCompany = (d.contact_company || '').toLowerCase().includes(state.searchQuery);
    return matchTitle || matchCompany;
  });

  STAGES.forEach(stage => {
    const stageDeals = filteredDeals.filter(d => d.stage === stage.id);
    const stageSum = stageDeals.reduce((sum, d) => sum + d.value, 0);

    const col = document.createElement('div');
    col.className = 'column';
    col.innerHTML = `
      <div class="column-header">
        <span class="col-title">${stage.label}</span>
        <span class="col-badge">${stageDeals.length}</span>
      </div>
      <div class="col-summary">${formatCurrency(stageSum)} · ${stage.prob}% prob</div>
      <div class="deals-container" id="col-${stage.id}"></div>
    `;

    const container = col.querySelector('.deals-container');
    stageDeals.forEach(deal => {
      const card = createDealCard(deal);
      container.appendChild(card);
    });

    pipelineBoard.appendChild(col);
  });
}

function createDealCard(deal) {
  const card = document.createElement('div');
  card.className = 'deal-card';

  const stageOptions = STAGES.map(s =>
    `<option value="${s.id}" ${s.id === deal.stage ? 'selected' : ''}>Move to: ${s.label}</option>`
  ).join('');

  card.innerHTML = `
    <div class="deal-head">
      <div class="deal-title">${escapeHtml(deal.title)}</div>
    </div>
    <div class="deal-account">${escapeHtml(deal.contact_company || 'Independent')} · ${escapeHtml(deal.contact_name || '')}</div>
    <div class="deal-metrics">
      <div class="deal-value">${formatCurrency(deal.value)}</div>
      <div class="deal-prob">${deal.probability}% Prob</div>
    </div>
    <div class="deal-weighted">Weighted: ${formatCurrency(deal.weighted_value)}</div>
    <div class="deal-actions">
      <select class="stage-select" data-deal-id="${deal.id}">
        ${stageOptions}
      </select>
      <button class="btn-icon btn-activity" title="Interaction History" data-deal-id="${deal.id}" data-contact-id="${deal.contact_id}" data-deal-title="${escapeHtml(deal.title)}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
      </button>
      <button class="btn-icon btn-delete" title="Delete Deal" data-deal-id="${deal.id}">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
      </button>
    </div>
  `;

  // Stage change
  const select = card.querySelector('.stage-select');
  select.addEventListener('change', async (e) => {
    const nextStage = e.target.value;
    try {
      const res = await fetch(`${API_BASE}/deals/${deal.id}/stage?new_stage=${nextStage}`, {
        method: 'PATCH'
      });
      if (!res.ok) throw new Error('Failed to update stage');
      await loadAllData();
    } catch (err) {
      alert('Error updating deal stage: ' + err.message);
    }
  });

  // Open activity
  card.querySelector('.btn-activity').addEventListener('click', (e) => {
    const btn = e.currentTarget;
    openActivityModal(btn.dataset.dealId, btn.dataset.contactId, btn.dataset.dealTitle);
  });

  // Delete deal
  card.querySelector('.btn-delete').addEventListener('click', async () => {
    if (confirm(`Are you sure you want to delete "${deal.title}"?`)) {
      await fetch(`${API_BASE}/deals/${deal.id}`, { method: 'DELETE' });
      await loadAllData();
    }
  });

  return card;
}

async function handleCreateDeal(e) {
  e.preventDefault();
  const payload = {
    contact_id: dealContactSelect.value,
    title: document.getElementById('dealTitle').value.trim(),
    value: parseFloat(document.getElementById('dealValue').value),
    stage: document.getElementById('dealStage').value,
    expected_close: document.getElementById('dealCloseDate').value || null
  };

  try {
    const res = await fetch(`${API_BASE}/deals`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create deal');
    }
    dealForm.reset();
    dealModal.classList.add('hidden');
    await loadAllData();
  } catch (err) {
    alert(err.message);
  }
}

async function handleCreateContact(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('ctName').value.trim(),
    email: document.getElementById('ctEmail').value.trim(),
    company: document.getElementById('ctCompany').value.trim(),
    role: document.getElementById('ctRole').value.trim() || 'Stakeholder',
    phone: document.getElementById('ctPhone').value.trim() || null
  };

  try {
    const res = await fetch(`${API_BASE}/contacts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create contact');
    }
    contactForm.reset();
    state.contacts = await fetch(`${API_BASE}/contacts`).then(r => r.json());
    renderContactsTable();
    populateContactOptions();
  } catch (err) {
    alert(err.message);
  }
}

function populateContactOptions() {
  dealContactSelect.innerHTML = state.contacts.map(c =>
    `<option value="${c.id}">${escapeHtml(c.name)} (${escapeHtml(c.company)})</option>`
  ).join('');
}

function renderContactsTable() {
  contactsTableBody.innerHTML = state.contacts.map(c => `
    <tr>
      <td><strong>${escapeHtml(c.name)}</strong></td>
      <td>${escapeHtml(c.company)}</td>
      <td>${escapeHtml(c.role || '-')}</td>
      <td>${escapeHtml(c.email)}</td>
      <td>${escapeHtml(c.phone || '-')}</td>
      <td>
        <button class="btn btn-sm btn-secondary" onclick="deleteContact('${c.id}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

window.deleteContact = async function(id) {
  if (confirm('Delete contact and any linked pipeline items?')) {
    await fetch(`${API_BASE}/contacts/${id}`, { method: 'DELETE' });
    state.contacts = await fetch(`${API_BASE}/contacts`).then(r => r.json());
    renderContactsTable();
    await loadAllData();
  }
};

async function openActivityModal(dId, cId, title) {
  actDealId.value = dId;
  actContactId.value = cId;
  document.getElementById('actModalTitle').textContent = `Interaction Log: ${title}`;
  activityModal.classList.remove('hidden');
  await loadActivities(dId);
}

async function loadActivities(dId) {
  try {
    const res = await fetch(`${API_BASE}/activities?deal_id=${dId}`);
    const activities = await res.json();
    activityTimeline.innerHTML = activities.length === 0
      ? '<p style="color:var(--text-muted);font-size:0.85rem;">No logged interactions yet.</p>'
      : activities.map(a => `
        <div class="act-item">
          <div class="act-meta">
            <span class="act-badge">${escapeHtml(a.activity_type)}</span>
            <span>${new Date(a.created_at).toLocaleString()}</span>
          </div>
          <div>${escapeHtml(a.notes)}</div>
        </div>
      `).join('');
  } catch (err) {
    console.error('Error fetching activities:', err);
  }
}

async function handleCreateActivity(e) {
  e.preventDefault();
  const dId = actDealId.value;
  const cId = actContactId.value;
  const payload = {
    deal_id: dId,
    contact_id: cId,
    activity_type: document.getElementById('actType').value,
    notes: document.getElementById('actNotes').value.trim()
  };

  try {
    const res = await fetch(`${API_BASE}/activities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to record activity');
    document.getElementById('actNotes').value = '';
    await loadActivities(dId);
  } catch (err) {
    alert(err.message);
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, tag => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    "'": '&#39;',
    '"': '&quot;'
  }[tag] || tag));
}
