// LoginCard.jsx — Dark-theme login form, used on login.html.

const LoginCard = () => {
  const inputStyle = {
    fontFamily: "'Inter', sans-serif", fontSize: '0.92rem', color: '#FAF9F6',
    background: 'rgba(255,255,255,0.04)', border: '1.5px solid rgba(255,255,255,0.12)',
    borderRadius: 6, padding: '12px 14px', outline: 'none', width: '100%',
    transition: 'border-color 200ms ease, box-shadow 200ms ease',
  };
  return (
    <form id="login-form" onSubmit={e => e.preventDefault()} style={{
      background: 'rgba(13,33,55,0.85)', backdropFilter: 'blur(12px)',
      border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8,
      padding: 36, width: 380, boxShadow: '0 16px 60px rgba(10,25,47,0.55)',
      display: 'flex', flexDirection: 'column', gap: 18,
    }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.15em', textTransform: 'uppercase', color: '#6BAED6' }}>Sign in</div>
        <h2 style={{ fontFamily: "'Montserrat', sans-serif", fontWeight: 800, fontSize: '1.6rem', color: '#FAF9F6', margin: 0, letterSpacing: '-0.02em' }}>Welcome back</h2>
        <p style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.82rem', color: 'rgba(250,249,246,0.6)', margin: 0, lineHeight: 1.6 }}>
          Sign in to your clinic. Sessions are audit-logged and expire after 12 h of inactivity.
        </p>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <label style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.74rem', fontWeight: 600, color: 'rgba(250,249,246,0.85)' }}>Email</label>
        <input id="login-email" name="email" style={inputStyle} placeholder="hau@oakdentalcalgary.com" />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <label style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.74rem', fontWeight: 600, color: 'rgba(250,249,246,0.85)' }}>Password</label>
          <a href="login.html#forgot" style={{ fontFamily: "'Inter', sans-serif", fontSize: '0.72rem', color: '#6BAED6', textDecoration: 'none' }}>Forgot?</a>
        </div>
        <input id="login-password" name="password" style={inputStyle} type="password" placeholder="••••••••" />
      </div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: 'rgba(250,249,246,0.6)' }}>
        <input type="checkbox" style={{ accentColor: '#3A7FBD' }} /> Remember this device for 30 days
      </label>
      <button type="submit" className="btn btn-white btn-lg" style={{ width: '100%', justifyContent: 'center' }}>Sign in</button>
      <div style={{ textAlign: 'center', fontFamily: "'Inter', sans-serif", fontSize: '0.72rem', color: 'rgba(250,249,246,0.4)' }}>
        Need access? <a style={{ color: '#6BAED6', textDecoration: 'none' }} href="index.html#contact">Contact your clinic admin →</a>
      </div>
      <div id="login-error" style={{ display: 'none', fontFamily: "'Inter', sans-serif", fontSize: '0.78rem', color: '#F87171', marginTop: -8 }} />
    </form>
  );
};

Object.assign(window, { LoginCard });
