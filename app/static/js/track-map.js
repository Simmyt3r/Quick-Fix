(function () {
  var mapEl = document.getElementById('track-map');
  if (!mapEl) return;

  var config = {
    mapboxToken: mapEl.getAttribute('data-mapbox-token'),
    pusherKey: mapEl.getAttribute('data-pusher-key'),
    pusherCluster: mapEl.getAttribute('data-pusher-cluster'),
    jobId: mapEl.getAttribute('data-job-id'),
    jobLat: parseFloat(mapEl.getAttribute('data-job-lat')),
    jobLng: parseFloat(mapEl.getAttribute('data-job-lng')),
  };
  if (!config.mapboxToken) return;

  var csrfMeta = document.querySelector('meta[name="csrf-token"]');
  var csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';
  var statusEl = document.getElementById('track-status');

  mapboxgl.accessToken = config.mapboxToken;
  var map = new mapboxgl.Map({
    container: 'track-map',
    style: 'mapbox://styles/mapbox/streets-v12',
    center: [config.jobLng, config.jobLat],
    zoom: 13,
  });

  var jobMarker = new mapboxgl.Marker({ color: '#0068B7' })
    .setLngLat([config.jobLng, config.jobLat])
    .addTo(map);

  var proMarker = null;

  function updateProMarker(lat, lng) {
    if (!proMarker) {
      proMarker = new mapboxgl.Marker({ color: '#20A84A' }).setLngLat([lng, lat]).addTo(map);
    } else {
      proMarker.setLngLat([lng, lat]);
    }
    if (statusEl) statusEl.textContent = 'Live \u2014 updated just now';

    var bounds = new mapboxgl.LngLatBounds();
    bounds.extend([config.jobLng, config.jobLat]);
    bounds.extend([lng, lat]);
    map.fitBounds(bounds, { padding: 60, maxZoom: 15 });
  }

  if (!config.pusherKey || typeof Pusher === 'undefined') {
    if (statusEl) statusEl.textContent = 'Live updates aren\u2019t available right now.';
    return;
  }

  var client = new Pusher(config.pusherKey, {
    cluster: config.pusherCluster,
    authEndpoint: '/location/pusher-auth',
    auth: {
      headers: { 'X-CSRFToken': csrfToken },
    },
  });

  var channel = client.subscribe('private-job-' + config.jobId);
  channel.bind('location-update', function (data) {
    if (typeof data.lat === 'number' && typeof data.lng === 'number') {
      updateProMarker(data.lat, data.lng);
    }
  });
  channel.bind('pusher:subscription_error', function () {
    if (statusEl) statusEl.textContent = 'Couldn\u2019t connect for live updates.';
  });
})();
