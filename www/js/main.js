import { initNotifications } from './notifications.js';
import { initSession } from './session.js';
import { setupUI } from './ui.js';
import { initAPI } from './api.js';

document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 DOM loaded — starting NoScroll app initialization');

  // Wait for Capacitor bridge to be ready
  await waitForCapacitorReady();

  console.log('✅ Capacitor ready — initializing modules');

  await initNotifications();
  setupUI();
  initSession();
  initAPI();

  console.log('✅ NoScroll App initialization complete');
});

async function waitForCapacitorReady() {
  return new Promise((resolve) => {
    const check = () => {
      if (window.Capacitor && window.Capacitor.isNativePlatform()) {
        resolve();
      } else {
        console.log('⏳ Waiting for Capacitor bridge...');
        setTimeout(check, 300);
      }
    };
    check();
  });
}
