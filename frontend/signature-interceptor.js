(() => {
  const SECRET = window.AAPDA_SETU_SECRET || "aapda-setu-secure-token";
  const hmac = async (d) => {
    const enc = new TextEncoder(), k = await crypto.subtle.importKey("raw", enc.encode(SECRET), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
    return Array.from(new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(d || "")))).map(b => b.toString(16).padStart(2, "0")).join("");
  };
  const _fetch = window.fetch, { open: _open, send: _send } = XMLHttpRequest.prototype;
  window.fetch = async (url, opts = {}) => {
    const m = (opts.method || "GET").toUpperCase();
    if (["POST", "PUT"].includes(m)) {
      const b = typeof opts.body === "string" ? opts.body : (opts.body ? JSON.stringify(opts.body) : "");
      opts.headers = new Headers(opts.headers || {});
      opts.headers.set("X-Signature", await hmac(b));
    }
    return _fetch(url, opts);
  };
  XMLHttpRequest.prototype.open = function(m, ...a) { this._m = m; return _open.call(this, m, ...a); };
  XMLHttpRequest.prototype.send = function(body) {
    if (["POST", "PUT"].includes((this._m || "").toUpperCase())) {
      hmac(typeof body === "string" ? body : (body ? JSON.stringify(body) : "")).then(s => {
        this.setRequestHeader("X-Signature", s);
        _send.call(this, body);
      });
    } else _send.call(this, body);
  };
})();
