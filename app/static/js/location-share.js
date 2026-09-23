(function () {
  // Only runs on pages that opt in by including this script AND marking
  // the body with data-share-location="true" (set server-side, based on
  // current_user.is_professional and their available flag — see
  // dashboard.html). Browsers require an explicit permission prompt for
  // geolocation, so this can only ever be a foreground, user-visible
  // thing — never truly silent background tracking.
  var root = document.body;
  if (!root || root.getAttribute('data-share-location') !== 'true') return;
  if (!('geolocation' in navigator)) return;

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
  var jobId = root.getAttribute('data-tracking-job-id') || '';

  function sendPosition(position) {
    var body = new URLSearchParams();
    body.set('lat', position.coords.latitude);
    body.set('lng', position.coords.longitude);
    if (jobId) body.set('job_id', jobId);

    fetch('/location/update', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken,
      },
      body: body.toString(),
    }).catch(function () {
      // A missed update isn't worth surfacing to the user — the next
      // interval just tries again.
    });
  }

  function tick() {
    navigator.geolocation.getCurrentPosition(sendPosition, function () {
      // Permission denied or position unavailable — nothing to do here;
      // the pro just won't show up as located until they allow it.
    }, { enableHighAccuracy: true, timeout: 8000, maximumAge: 20000 });
  }

  tick();
  setInterval(tick, 30000);
})();
