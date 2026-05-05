window.ML_CARDS_CONFIG = {
  // Replace with the Worker URL in your target Cloudflare account.
  workerUrl: 'https://ml-cards-worker.holiday-radar-api.workers.dev',

  // Optional TikTok worker URL if you still use live feed features.
  tiktokWorkerUrl: 'https://tiktok-live-worker.holiday-radar-api.workers.dev',

  // Optional Cloudflare Web Analytics token for the target account.
  // Leave empty to disable analytics beacon loading.
  cfBeaconToken: '',
};
