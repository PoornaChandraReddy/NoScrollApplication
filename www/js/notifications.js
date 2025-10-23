import { LocalNotifications } from '@capacitor/local-notifications';

export async function initNotifications() {
  console.log('🔔 Initializing Local Notifications');

  try {
    const perm = await LocalNotifications.requestPermissions();
    if (perm.display === 'granted') {
      await LocalNotifications.createChannel({
        id: 'alarm',
        name: 'Alarm Notifications',
        description: 'Heads-up alerts for NoScroll App',
        importance: 5,
        sound: 'alarm',
        vibration: true,
        visibility: 'public',
      });
      console.log('✅ Notification channel ready');
    } else {
      console.warn('⚠️ Notifications not granted by user');
    }
  } catch (err) {
    console.error('❌ Notification init failed', err);
  }
}

export async function sendNotification(title, body) {
  try {
    await LocalNotifications.schedule({
      notifications: [
        {
          title,
          body,
          id: Date.now(),
          channelId: 'alarm',
          schedule: { at: new Date(Date.now() + 1000) },
        },
      ],
    });
    console.log('📨 Notification scheduled:', title);
  } catch (err) {
    console.error('❌ Failed to send notification', err);
  }
}
