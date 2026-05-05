// Simulated localStorage-backed auth. Wired in Phase 5.
// Each app page should call window.RRD.requireSession() at top of <script>.
(function () {
  const RRD = (window.RRD = window.RRD || {});
  const KEY = 'rrd_session';

  RRD.getSession = function () {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? JSON.parse(raw) : null;
    } catch (_) {
      return null;
    }
  };

  RRD.login = function (email, password) {
    if (!email || !password || password.length < 6) {
      return { ok: false, error: 'Email and a password of 6+ characters are required.' };
    }
    const users = window.USERS || [];
    const match = users.find((u) => u.email.toLowerCase() === email.toLowerCase()) || users[0];
    if (!match) return { ok: false, error: 'No demo user available.' };
    const session = {
      clinic_id: match.clinic_id,
      user_id: match.id,
      full_name: match.full_name,
      email: match.email,
      role: match.role,
      issued_at: new Date().toISOString(),
      assigned_clinic_ids: match.assigned_clinic_ids || [match.clinic_id],
    };
    localStorage.setItem(KEY, JSON.stringify(session));
    return { ok: true, session };
  };

  RRD.logout = function () {
    localStorage.removeItem(KEY);
  };

  RRD.requireSession = function (loginPath) {
    const path = loginPath || 'login.html';
    const sess = RRD.getSession();
    if (!sess) {
      const next = encodeURIComponent(window.location.pathname.split('/').pop() + window.location.search);
      window.location.replace(`${path}?next=${next}`);
      return null;
    }
    return sess;
  };
  RRD.getCurrentClinicId = function () {
    return RRD.getSession()?.clinic_id || null;
  };

  RRD.getAssignedClinicIds = function () {
    return RRD.getSession()?.assigned_clinic_ids || [];
  };

  RRD.setCurrentClinic = function (id) {
    const sess = RRD.getSession();
    if (!sess) return false;
    const allowed = sess.assigned_clinic_ids || [];
    if (allowed.length && !allowed.includes(id)) return false;
    sess.clinic_id = id;
    localStorage.setItem(KEY, JSON.stringify(sess));
    try {
      window.dispatchEvent(new CustomEvent('clinic-changed', { detail: { id } }));
    } catch (_) { /* no-op */ }
    return true;
  };
})();
