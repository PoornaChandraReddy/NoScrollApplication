export function initAPI() {
  console.log('🌍 API initialized (placeholder)');
}

// Example API call
export async function logUsage(durationSeconds) {
  try {
    console.log(`📡 Logging usage: ${durationSeconds} seconds`);
    // Replace with your real endpoint
    // await fetch('https://your-api.com/log', { method: 'POST', body: JSON.stringify({ durationSeconds }) });
  } catch (err) {
    console.error('❌ Failed to log usage', err);
  }
}
