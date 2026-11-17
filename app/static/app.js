'use strict';
const $ = id => document.getElementById(id);
let token = '';
function notice(message) { $('notice').textContent = message; }
function lock() { token = ''; $('workspace').classList.add('hidden'); $('gate').classList.remove('hidden'); $('cases').replaceChildren(); $('documents').replaceChildren(); }
async function api(path, body) {
  const response = await fetch(path, { method: body === undefined ? 'GET' : 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
  const data = await response.json();
  if (response.status === 401) lock();
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}
function action(fn) { return async event => { event?.preventDefault(); const button = event?.submitter || event?.currentTarget; if (button) button.disabled = true; try { await fn(); } catch (error) { notice(error.message); } finally { if (button) button.disabled = false; } }; }
async function load() {
  const data = await api('/api/dashboard');
  $('services').textContent = Object.entries(data.services).map(([name, state]) => `${name}: ${state}`).join(' | ');
  $('queue').textContent = `Approximate queued messages: ${data.queued}. Dead-letter routing configured: ${data.redrive_configured ? 'yes' : 'no'}. Failed jobs remain available for retry.`;
  $('cases').replaceChildren();
  for (const item of data.cases) {
    const row = document.createElement('tr');
    for (const value of [item.reference, item.status, item.created_at]) { const cell = document.createElement('td'); cell.textContent = value; row.append(cell); }
    $('cases').append(row);
  }
  $('documents').replaceChildren();
  for (const item of data.documents) { const row = document.createElement('li'); row.textContent = `${item.key} (${item.bytes} bytes)`; $('documents').append(row); }
}
$('unlock-form').onsubmit = action(async () => {
  token = $('recovery-token').value.trim();
  try { await api('/api/unlock', {}); } catch (error) { lock(); throw error; }
  $('recovery-token').value = ''; $('gate').classList.add('hidden'); $('workspace').classList.remove('hidden');
  notice('Recovery token accepted. Loading live AWS-backed operations.'); await load();
});
$('case-form').onsubmit = action(async () => { await api('/api/cases', { reference: $('reference').value }); $('case-form').reset(); notice('Request stored in PostgreSQL and sent to SQS.'); await load(); });
$('document-form').onsubmit = action(async () => { await api('/api/documents', { text: $('document-text').value }); $('document-form').reset(); notice('Document stored in private S3.'); await load(); });
$('process').onclick = action(async () => { const data = await api('/api/jobs/process', {}); notice(`Completed: ${data.completed}. Retrying: ${data.retrying}.`); await load(); });
$('refresh').onclick = action(load);
$('lock').onclick = () => { lock(); notice('Workspace locked.'); };
