import { PushNotifications } from '@capacitor/push-notifications';
import { registerDeviceToken } from './client';

export async function initPushNotifications() {
  try {
    let perm = await PushNotifications.checkPermissions();
    if (perm.receive !== 'granted') {
      perm = await PushNotifications.requestPermissions();
    }
    if (perm.receive !== 'granted') {
      console.warn('Push notification permission not granted');
      return;
    }

    await PushNotifications.register();

    PushNotifications.addListener('registration', async (token) => {
      try {
        await registerDeviceToken(token.value, 'android');
      } catch (e) {
        // Non-fatal: the app works fine without push, this just means no
        // notifications will arrive until the next successful registration.
        console.warn('Failed to register device token with backend', e);
      }
    });

    PushNotifications.addListener('registrationError', (err) => {
      console.warn('Push registration error', err);
    });
  } catch (e) {
    // Expected when running in a plain browser (npm run dev) - the web
    // implementation of this plugin doesn't support real push.
    console.warn('Push notifications unavailable in this environment', e);
  }
}
