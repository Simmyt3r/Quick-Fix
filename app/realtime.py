"""
Thin wrapper around Pusher Channels — broadcasts a professional's live
location so a customer's browser can update a map pin in near-real-time,
without this app needing to hold a persistent connection itself (Vercel's
serverless runtime doesn't support that).

Two kinds of channel:
- A private per-job channel (private-job-<id>), subscribed to only by
  that job's customer, for live tracking once a job is in_progress.
- (Nearby-pro matching for the dashboard is a plain page reload/poll for
  now, not pushed — see TODO.md. Only in-progress job tracking is
  genuinely real-time in this first pass.)
"""
import os

import pusher

_client = None


def pusher_configured():
    return bool(
        os.environ.get("PUSHER_APP_ID")
        and os.environ.get("PUSHER_KEY")
        and os.environ.get("PUSHER_SECRET")
        and os.environ.get("PUSHER_CLUSTER")
    )


def _get_client():
    global _client
    if _client is None:
        _client = pusher.Pusher(
            app_id=os.environ["PUSHER_APP_ID"],
            key=os.environ["PUSHER_KEY"],
            secret=os.environ["PUSHER_SECRET"],
            cluster=os.environ["PUSHER_CLUSTER"],
            ssl=True,
        )
    return _client


def job_channel_name(service_request_id):
    return f"private-job-{service_request_id}"


def broadcast_professional_location(service_request_id, lat, lng):
    """Push a location update to whoever's subscribed to this job's
    channel (the customer, once they've been auth'd for it — see
    app/routes/location.py's channel-auth endpoint). No-op, not an
    error, if Pusher isn't configured — location updates still get
    saved to the DB either way (see Professional.current_lat/lng),
    just without the live push."""
    if not pusher_configured():
        return
    try:
        _get_client().trigger(
            job_channel_name(service_request_id),
            "location-update",
            {"lat": lat, "lng": lng},
        )
    except Exception:
        # A broadcast failure shouldn't break the location-update request
        # itself — the DB write already happened, worst case is the
        # customer's map is a beat behind until the next update lands.
        pass


def authenticate_channel(channel_name, socket_id):
    """Server-side auth for a private Pusher channel subscription — the
    client's Pusher JS SDK calls our /location/pusher-auth endpoint,
    which calls this, before it's allowed to subscribe. Raises if Pusher
    isn't configured; callers should have already checked pusher_configured()."""
    return _get_client().authenticate(channel=channel_name, socket_id=socket_id)
