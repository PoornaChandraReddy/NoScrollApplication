export function setupUI() {
  showPage('setup-card');
  console.log('✅ UI setup complete');
}

export function showPage(pageId) {
  const pages = ['setup-card', 'tracker-card', 'summary-card'];
  pages.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden', id !== pageId);
  });
}

export function showAlert(message) {
  alert(message);
}

export function updateTimerDisplay(elapsed, totalMinutes) {
  const remaining = Math.max(0, totalMinutes * 60 - elapsed);
  const min = Math.floor(remaining / 60).toString().padStart(2, '0');
  const sec = (remaining % 60).toString().padStart(2, '0');
  document.getElementById('timer-display').textContent = `${min}:${sec}`;
}
