// MonoText — renders children in JetBrains Mono
const MonoText = ({ children, style }) => (
  <span style={{ fontFamily: 'var(--font-mono)', letterSpacing: '0.02em', ...style }}>
    {children}
  </span>
);

window.MonoText = MonoText;
