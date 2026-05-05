// console-tap.js — captures runtime JS errors and POSTs them to /__log__
// for the dev http server to print. Used during the white-page debug.
(function () {
  function send(payload) {
    try {
      fetch('/__log__', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(Object.assign({ url: location.pathname }, payload)),
        keepalive: true,
      });
    } catch (_) { /* no-op */ }
  }
  window.addEventListener('error', function (e) {
    send({
      kind: 'error',
      message: e.message,
      filename: e.filename,
      lineno: e.lineno,
      colno: e.colno,
      stack: e.error && e.error.stack ? e.error.stack.split('\n').slice(0, 6).join('\n') : null,
    });
  });
  window.addEventListener('unhandledrejection', function (e) {
    send({
      kind: 'unhandledrejection',
      reason: String(e.reason && e.reason.message || e.reason),
      stack: e.reason && e.reason.stack ? e.reason.stack.split('\n').slice(0, 6).join('\n') : null,
    });
  });
  // Tap console.error too, since React surfaces some failures there.
  var orig = console.error.bind(console);
  console.error = function () {
    try {
      send({ kind: 'console.error', message: Array.from(arguments).map(String).join(' ') });
    } catch (_) {}
    return orig.apply(console, arguments);
  };
  // One probe so we can verify the tap is active.
  send({ kind: 'tap-loaded' });
})();
