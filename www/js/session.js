import { sendNotification } from './notifications.js';
import { showPage, updateTimerDisplay } from './ui.js';
import { logUsage } from './api.js';

let timerInterval;
let startTime;
let timeLimitMinutes;

export function initSession() {
  const startBtn = document.getElementById('start-session-btn');
  const endBtn = document.getElementById('end-session-btn');
  const backBtn = document.getElementById('back-btn');

  if (startBtn) startBtn.addEventListener('click', startSessionHandler);
  if (endBtn) endBtn.addEventListener('click', () => endSession(false));
  if (backBtn) backBtn.addEventListener('click', () => showPage('setup-card'));

  console.log('✅ Session buttons attached');
}

async function startSessionHandler() {
  const appPackage = document.getElementById('socialApp').value;
  timeLimitMinutes = parseInt(document.getElementById('timeLimit').value);

  showPage('tracker-card');
  startTime = Date.now();

  sendNotification('Session Started', `Your ${timeLimitMinutes}-minute session is active.`);

  // ✅ Launch the selected app
  await openAppByPackage(appPackage);

  // ✅ Start timer
  timerInterval = setInterval(() => updateTimer(), 1000);
}

function updateTimer() {
  const elapsedSeconds = Math.floor((Date.now() - startTime) / 1000);
  const remaining = timeLimitMinutes * 60 - elapsedSeconds;

  updateTimerDisplay(elapsedSeconds, timeLimitMinutes);

  if (remaining === 60) sendNotification('1 Minute Left', 'Your session is ending soon!');
  if (remaining <= 0) endSession(true);
}

function endSession(autoEnded) {
  clearInterval(timerInterval);

  const totalSeconds = Math.floor((Date.now() - startTime) / 1000);
  logUsage(totalSeconds);

  showPage('summary-card');

  if (autoEnded) {
    sendNotification('Session Ended', 'Time limit reached!');
  } else {
    sendNotification('Session Ended', 'You ended the session early.');
  }
}

/* ----------------------------------------------------------
   ✅ App Launcher Logic
   - Opens the selected app (Instagram, Facebook, YouTube, etc.)
   - Falls back to browser if the app is not installed
----------------------------------------------------------- */
async function openAppByPackage(packageValue) {
  // Map dropdown values → readable app names + URLs
  const APP_MAP = {
    'com.instagram.android': {
      name: 'Instagram',
      app: 'instagram://user?username=_',
      web: 'https://www.instagram.com/'
    },
    'com.facebook.katana': {
      name: 'Facebook',
      app: 'fb://',
      web: 'https://www.facebook.com/'
    },
    'com.youtube.android': {
      name: 'YouTube',
      app: 'youtube://',
      web: 'https://www.youtube.com/'
    },
    'com.twitter.android': {
      name: 'Twitter',
      app: 'twitter://',
      web: 'https://twitter.com/'
    },
    'com.snapchat.android': {
      name: 'Snapchat',
      app: 'snapchat://',
      web: 'https://www.snapchat.com/'
    }
  };

  const target = APP_MAP[packageValue] || APP_MAP['com.instagram.android'];

  try {
    const canOpen = await window.AppLauncher.canOpenUrl({ url: target.app });

    if (canOpen.value) {
      console.log(`🚀 Opening ${target.name} via AppLauncher`);
      await window.AppLauncher.openUrl({ url: target.app });
    } else {
      console.warn(`${target.name} app not installed — opening web version`);
      window.open(target.web, '_blank');
    }
  } catch (e) {
    console.error(`${target.name} AppLauncher error, fallback to browser:`, e);
    window.open(target.web, '_blank');
  }
}
