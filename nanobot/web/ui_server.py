"""Serve admin UI on port 3000 (no auth). Injects gateway URL + token form; API calls go to gateway with token."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Connector script: prompt for gateway URL + token if missing, override fetch to use them
_CONNECTOR_SCRIPT = """
(function(){
  var STORAGE_KEY_BASE = 'nanobot_gateway_base';
  var STORAGE_KEY_TOKEN = 'nanobot_gateway_token';
  function getBase() { return (localStorage.getItem(STORAGE_KEY_BASE) || '').replace(/\\/$/, ''); }
  function getToken() { return localStorage.getItem(STORAGE_KEY_TOKEN) || ''; }
  function showConnector() {
    var base = getBase();
    var token = getToken();
    if (base && token) return;
    var wrap = document.createElement('div');
    wrap.id = 'nanobot-connector';
    wrap.style.cssText = 'position:fixed;inset:0;z-index:99999;background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;font-family:system-ui,sans-serif;';
    wrap.innerHTML = '<div style="background:#1a1a1a;padding:2rem;border-radius:12px;min-width:320px;color:#e0e0e0;">' +
      '<h2 style="margin:0 0 1rem;">ربط البوابة</h2>' +
      '<p style="margin:0 0 1rem;font-size:0.9rem;color:#999;">أدخل رابط البوابة (Gateway) وتوكن الإدارة.</p>' +
      '<label style="display:block;margin-bottom:0.5rem;">رابط البوابة</label>' +
      '<input id="nb-base" type="text" placeholder="http://localhost:18790" value="' + (base || 'http://localhost:18790') + '" style="width:100%;padding:0.5rem;margin-bottom:1rem;border:1px solid #444;border-radius:6px;background:#222;color:#fff;">' +
      '<label style="display:block;margin-bottom:0.5rem;">التوكن</label>' +
      '<input id="nb-token" type="password" placeholder="GATEWAY_ADMIN_TOKEN" value="' + token + '" style="width:100%;padding:0.5rem;margin-bottom:1rem;border:1px solid #444;border-radius:6px;background:#222;color:#fff;">' +
      '<button id="nb-save" style="width:100%;padding:0.6rem;background:#0d7377;border:none;border-radius:6px;color:#fff;cursor:pointer;">حفظ وفتح</button>' +
      '</div>';
    document.body.appendChild(wrap);
    document.getElementById('nb-save').onclick = function() {
      var b = document.getElementById('nb-base').value.trim();
      var t = document.getElementById('nb-token').value.trim();
      if (b) localStorage.setItem(STORAGE_KEY_BASE, b);
      if (t) localStorage.setItem(STORAGE_KEY_TOKEN, t);
      document.getElementById('nanobot-connector').remove();
      location.reload();
    };
  }
  if (!getBase() || !getToken()) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', showConnector);
    else showConnector();
  }
  var origFetch = window.fetch;
  window.fetch = function(url, opts) {
    opts = opts || {};
    var u = typeof url === 'string' ? url : (url && url.url);
    if (u && (u.startsWith('/api/') || u.startsWith('/api'))) {
      var base = getBase();
      if (base) {
        url = base + (u.startsWith('/') ? u : '/' + u);
        opts.headers = opts.headers || {};
        var h = new Headers(opts.headers);
        if (getToken()) h.set('Authorization', 'Bearer ' + getToken());
        opts.headers = h;
      }
    }
    return origFetch.call(this, url, opts);
  };
})();
"""


def create_ui_app(static_dir: Path) -> FastAPI:
    """Create FastAPI app that serves admin-ui with connector injected."""
    app = FastAPI(title="Nanobot Admin UI")
    static_dir = static_dir.resolve()
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    index_html_path = static_dir / "index.html"
    if not index_html_path.exists():
        # Fallback: return minimal page asking to build admin-ui
        @app.get("/", response_class=HTMLResponse)
        def _():
            return """<!DOCTYPE html><html><body style="font-family:system-ui;padding:2rem;">
            <h1>Nanobot Admin UI</h1>
            <p>No <code>admin-ui/dist</code> found. Build the UI first: <code>cd admin-ui && npm run build</code></p>
            </body></html>"""
        return app

    raw_index = index_html_path.read_text(encoding="utf-8")
    injected_index = raw_index.replace("</head>", f"<script>{_CONNECTOR_SCRIPT}</script></head>")

    @app.get("/", response_class=HTMLResponse)
    @app.get("/index.html", response_class=HTMLResponse)
    def _index():
        return injected_index

    @app.get("/admin", response_class=HTMLResponse)
    def _admin():
        return injected_index

    return app
