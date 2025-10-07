// Command Palette and Keyboard Shortcuts
// Provides Ctrl/Cmd+K palette, quick nav (g d, g p, g r, g t), and timer controls

(function(){
  if (window.__ttCommandsLoaded) return; // prevent double load
  window.__ttCommandsLoaded = true;

  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

  // Lightweight DOM helpers
  function $(sel, root){ return (root||document).querySelector(sel); }
  function $all(sel, root){ return Array.from((root||document).querySelectorAll(sel)); }

  function openModal(){
    try {
      const el = $('#commandPaletteModal');
      if (!el) return;
      const modal = bootstrap.Modal.getOrCreateInstance(el, { backdrop: 'static' });
      modal.show();
      // Focus input after show animation
      setTimeout(() => $('#commandPaletteInput')?.focus(), 150);
      refreshCommands();
      renderList();
    } catch(e) {}
  }

  function closeModal(){
    try {
      const el = $('#commandPaletteModal');
      if (!el) return;
      const modal = bootstrap.Modal.getOrCreateInstance(el);
      modal.hide();
      clearFilter();
    } catch(e) {}
  }

  // Timer helpers
  async function getActiveTimer(){
    try {
      const res = await fetch('/api/timer/status');
      if (!res.ok) return null;
      const json = await res.json();
      return json && json.active ? json.timer : null;
    } catch(e) { return null; }
  }

  async function startTimerQuick(){
    // Navigate to log time if no quick context; palette is for quick access, not forms
    window.location.href = '/timer/manual';
  }

  async function stopTimerQuick(){
    try {
      const active = await getActiveTimer();
      if (!active) { showToast('No active timer', 'warning'); return; }
      const res = await fetch('/api/timer/stop', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) });
      if (res.ok) {
        showToast('Timer stopped', 'info');
      } else {
        showToast('Failed to stop timer', 'danger');
      }
    } catch(e) {
      showToast('Failed to stop timer', 'danger');
    }
  }

  // Commands registry
  const registry = [];
  function addCommand(cmd){ registry.push(cmd); }
  function nav(href){ window.location.href = href; }

  addCommand({ id: 'goto-dashboard', title: 'Go to Dashboard', hint: 'g d', keywords: 'home main', action: () => nav('/') });
  addCommand({ id: 'goto-projects', title: 'Go to Projects', hint: 'g p', keywords: 'work clients', action: () => nav('/projects') });
  addCommand({ id: 'goto-clients', title: 'Go to Clients', hint: '', keywords: 'work companies', action: () => nav('/clients') });
  addCommand({ id: 'goto-tasks', title: 'Go to Tasks', hint: 'g t', keywords: 'work', action: () => nav('/tasks') });
  addCommand({ id: 'goto-reports', title: 'Go to Reports', hint: 'g r', keywords: 'insights analytics', action: () => nav('/reports') });
  addCommand({ id: 'goto-invoices', title: 'Go to Invoices', hint: '', keywords: 'billing finance', action: () => nav('/invoices') });
  addCommand({ id: 'goto-analytics', title: 'Go to Analytics', hint: '', keywords: 'charts insights', action: () => nav('/analytics') });
  addCommand({ id: 'open-calendar', title: 'Open Calendar', hint: '', keywords: 'day week month schedule', action: () => nav('/timer/calendar') });
  addCommand({ id: 'log-time', title: 'Log Time (Manual Entry)', hint: '', keywords: 'add create', action: () => nav('/timer/manual') });
  addCommand({ id: 'bulk-entry', title: 'Bulk Time Entry', hint: '', keywords: 'multi add', action: () => nav('/timer/bulk') });
  addCommand({ id: 'start-timer', title: 'Start New Timer (Quick → Manual)', hint: '', keywords: 'play run', action: startTimerQuick });
  addCommand({ id: 'stop-timer', title: 'Stop Timer', hint: '', keywords: 'pause end', action: stopTimerQuick });
  addCommand({ id: 'goto-admin', title: 'Open Admin', hint: '', keywords: 'settings system', action: () => nav('/admin') });
  addCommand({ id: 'open-profile', title: 'Open Profile', hint: '', keywords: 'account user', action: () => nav('/profile') });
  addCommand({ id: 'open-help', title: 'Open Help', hint: '', keywords: 'support docs', action: () => nav('/help') });
  addCommand({ id: 'open-about', title: 'Open About', hint: '', keywords: 'info version', action: () => nav('/about') });
  addCommand({ id: 'toggle-theme', title: 'Toggle Theme', hint: isMac ? '⌘⇧L' : 'Ctrl+Shift+L', keywords: 'light dark', action: () => { try { document.getElementById('theme-toggle-global')?.click(); } catch(e) {} } });

  // Filtering and rendering
  let filtered = registry.slice();
  let selectedIdx = 0;

  function clearFilter(){
    const input = $('#commandPaletteInput');
    if (input) input.value = '';
    filtered = registry.slice();
    selectedIdx = 0;
  }

  function normalize(s){ return (s||'').toLowerCase(); }
  function isMatch(cmd, q){
    if (!q) return true;
    const t = normalize(cmd.title);
    const k = normalize(cmd.keywords);
    q = normalize(q);
    return t.indexOf(q) !== -1 || k.indexOf(q) !== -1;
  }

  async function refreshCommands(){
    // Update titles that depend on state (e.g., timer)
    const active = await getActiveTimer();
    const stop = registry.find(c => c.id === 'stop-timer');
    if (stop) stop.title = active ? `Stop Timer (${active.project_name || 'Current'})` : 'Stop Timer';
  }

  function renderList(){
    const list = $('#commandPaletteList');
    if (!list) return;
    list.innerHTML = '';
    filtered.forEach((cmd, idx) => {
      const li = document.createElement('button');
      li.type = 'button';
      li.className = 'list-group-item list-group-item-action d-flex justify-content-between align-items-center';
      li.setAttribute('data-idx', String(idx));
      li.innerHTML = `<span>${cmd.title}</span>${cmd.hint ? `<small class="text-muted">${cmd.hint}</small>` : ''}`;
      li.addEventListener('click', () => { closeModal(); setTimeout(() => cmd.action(), 50); });
      list.appendChild(li);
    });
    highlightSelected();
  }

  function highlightSelected(){
    $all('#commandPaletteList .list-group-item').forEach((el, idx) => {
      el.classList.toggle('active', idx === selectedIdx);
    });
  }

  function onInput(){
    const q = $('#commandPaletteInput')?.value || '';
    filtered = registry.filter(c => isMatch(c, q));
    selectedIdx = 0;
    renderList();
  }

  function onKeyDown(ev){
    // Check if typing in input field
    if (['input','textarea'].includes(ev.target.tagName.toLowerCase())) return;
    
    // Open with Ctrl/Cmd+K
    const openKeys = (ev.key.toLowerCase() === 'k' && (ev.metaKey || ev.ctrlKey));
    if (openKeys){ ev.preventDefault(); openModal(); return; }
    
    // Open with ? key (question mark)
    if (ev.key === '?' && !ev.ctrlKey && !ev.metaKey && !ev.altKey){ 
      ev.preventDefault(); 
      openModal(); 
      return; 
    }

    // Sequence shortcuts: g d / g p / g r / g t
    sequenceHandler(ev);
  }

  // Key sequence handling
  let seq = [];
  let seqTimer = null;
  function resetSeq(){ seq = []; if (seqTimer) { clearTimeout(seqTimer); seqTimer = null; } }
  function sequenceHandler(ev){
    if (ev.repeat) return;
    const key = ev.key.toLowerCase();
    if (['input','textarea'].includes(ev.target.tagName.toLowerCase())) return; // ignore typing fields
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return; // only plain keys
    seq.push(key);
    if (seq.length > 2) seq.shift();
    if (seq.length === 1 && seq[0] === 'g'){
      seqTimer = setTimeout(resetSeq, 1000);
      return;
    }
    if (seq.length === 2 && seq[0] === 'g'){
      const second = seq[1];
      resetSeq();
      if (second === 'd') return nav('/');
      if (second === 'p') return nav('/projects');
      if (second === 'r') return nav('/reports');
      if (second === 't') return nav('/tasks');
    }
  }

  // Modal-specific keyboard handling
  document.addEventListener('keydown', (ev) => {
    if (!$('#commandPaletteModal')?.classList.contains('show')) return;
    if (ev.key === 'Escape'){ ev.preventDefault(); closeModal(); return; }
    if (ev.key === 'ArrowDown'){ ev.preventDefault(); selectedIdx = Math.min(selectedIdx + 1, filtered.length - 1); highlightSelected(); return; }
    if (ev.key === 'ArrowUp'){ ev.preventDefault(); selectedIdx = Math.max(selectedIdx - 1, 0); highlightSelected(); return; }
    if (ev.key === 'Enter'){
      ev.preventDefault();
      const cmd = filtered[selectedIdx];
      if (cmd){ closeModal(); setTimeout(() => cmd.action(), 50); }
      return;
    }
  });

  // Global keydown to open palette and handle sequences
  document.addEventListener('keydown', onKeyDown);

  // Wire input events when DOM is ready
  document.addEventListener('DOMContentLoaded', function(){
    const input = $('#commandPaletteInput');
    if (input){ input.addEventListener('input', onInput); }
    const closeBtn = $('#commandPaletteClose');
    if (closeBtn){ closeBtn.addEventListener('click', closeModal); }
    const help = $('#commandPaletteHelp');
    if (help){
      help.textContent = `Shortcuts: ? or ${isMac ? '⌘' : 'Ctrl'}+K · g d (Dashboard) · g p (Projects) · g r (Reports) · g t (Tasks)`;
    }
  });

  // Expose for programmatic access
  window.openCommandPalette = openModal;
})();


