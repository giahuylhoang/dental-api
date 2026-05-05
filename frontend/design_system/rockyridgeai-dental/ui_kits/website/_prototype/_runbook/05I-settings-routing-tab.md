# Task 05I — settings.html: AI Routing tab

Append the **AI Routing** tab. After this task: 10 tabs total. Both the original 8 tabs and the 9th tab (AI Greeting from task 05H) must remain.

## Output

Modify exactly one file: `ui_kits/website/settings.html`.

## Allow-list

`^ui_kits/website/settings\.html$`

## Goal

A new tab labelled `AI Routing` (index 9). The tab body lets the owner edit hours, holidays, ring timeout, front-desk numbers, backup number, and AI behaviour toggles. Reads/writes `window.AI_CONFIG[currentClinicId].routing`.

## Approach

Append `'AI Routing'` to the existing `TABS` array. After this task the array reads:

```js
const TABS = ['Clinic info','Working hours','Operatories','Providers','Users & roles','Integrations','Notifications','Audit log','AI Greeting','AI Routing'];
```

Add a `tab === 9` body block after the `tab === 8` block.

### Tab body 9 — AI Routing

```jsx
{tab === 9 && (
  <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0,1.4fr) minmax(0,1fr)', gap: 24, alignItems: 'start' }}>
    <div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Routing</div>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 16 }}>How calls flow between the front desk and the AI.</div>

      <div className="field-row">
        <div className="field">
          <label className="lbl">Timezone</label>
          <select className="d-input" defaultValue={AI_CONFIG_FOR_CURRENT?.routing?.timezone || 'America/Edmonton'}>
            <option value="America/Edmonton">America/Edmonton</option>
            <option value="America/Vancouver">America/Vancouver</option>
            <option value="America/Toronto">America/Toronto</option>
          </select>
        </div>
        <div className="field">
          <label className="lbl">Ring timeout (seconds)</label>
          <input className="d-input" type="number" min={0} max={30}
                 defaultValue={AI_CONFIG_FOR_CURRENT?.routing?.ring_timeout_seconds ?? 5} />
          <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>How long the front desk rings before the AI picks up.</span>
        </div>
      </div>

      <div className="field">
        <label className="lbl">Front desk numbers (comma-separated, E.164)</label>
        <input className="d-input"
               defaultValue={(AI_CONFIG_FOR_CURRENT?.routing?.front_desk_numbers || []).join(', ')}
               placeholder="+15879738089" />
        <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Example: +15879738089</span>
      </div>

      <div className="field">
        <label className="lbl">Backup number (optional)</label>
        <input className="d-input" defaultValue={AI_CONFIG_FOR_CURRENT?.routing?.backup_number || ''} />
        <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Used when the front desk numbers don't answer.</span>
      </div>

      <div className="field">
        <label className="lbl">AI SIP URI (read-only here; engineer-managed)</label>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <input className="d-input" disabled
                 value={AI_CONFIG_FOR_CURRENT?.routing?.ai_sip_uri || ''}
                 style={{ flex: 1, background: 'var(--rr-warm-white)', cursor: 'not-allowed' }} />
          <span className="pill pill-inactive" title="Your engineering partner sets this up. You can copy it, but only they can change it.">Engineer-managed</span>
        </div>
      </div>

      <div className="field">
        <label className="lbl">Hours per weekday</label>
        <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginBottom: 6 }}>Both blank means closed that day.</span>
        <table className="list" style={{ marginTop: 6 }}>
          <thead><tr><th>Day</th><th>Open</th><th>Close</th></tr></thead>
          <tbody>
            {['mon','tue','wed','thu','fri','sat','sun'].map(d => {
              const hr = (AI_CONFIG_FOR_CURRENT?.routing?.hours?.[d]) || [];
              return (
                <tr key={d}>
                  <td style={{ textTransform: 'capitalize' }}>{d}</td>
                  <td><input className="d-input" style={{ width: 90 }} defaultValue={hr[0] || ''} placeholder="--:--" /></td>
                  <td><input className="d-input" style={{ width: 90 }} defaultValue={hr[1] || ''} placeholder="--:--" /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="field">
        <label className="lbl">Holidays (YYYY-MM-DD, one per line)</label>
        <textarea className="d-input" rows={3}
                  defaultValue={(AI_CONFIG_FOR_CURRENT?.routing?.holidays || []).join('\n')}
                  style={{ fontFamily: 'var(--font-mono)' }} />
        <span style={{ fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>Add days you're closed beyond regular hours. The AI will follow the after-hours rule on these days.</span>
      </div>

      <div className="toggle-row">
        <div>
          <div className="toggle-label">AI handles after-hours calls</div>
          <div className="toggle-sub">When you're closed, the AI takes the call instead of voicemail.</div>
        </div>
        <input type="checkbox" defaultChecked={!!AI_CONFIG_FOR_CURRENT?.routing?.ai_after_hours} />
      </div>
      <div className="toggle-row">
        <div>
          <div className="toggle-label">AI handles in-hours overflow</div>
          <div className="toggle-sub">If the front desk can't pick up in time, the AI steps in.</div>
        </div>
        <input type="checkbox" defaultChecked={!!AI_CONFIG_FOR_CURRENT?.routing?.ai_in_hours_overflow} />
      </div>

      <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }}>Save routing</button>
    </div>

    <aside style={{ position: 'sticky', top: 16, background: 'var(--rr-warm-white)', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: 18 }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--rr-navy-800)', marginBottom: 8 }}>Preview</div>
      <p style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', lineHeight: 1.55, marginTop: 0 }}>
        What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)
      </p>
      <div className="field">
        <label className="lbl">When (your local TZ)</label>
        <input className="d-input" type="datetime-local" />
      </div>
      <div className="toggle-row" style={{ borderBottom: 'none', padding: '6px 0' }}>
        <div className="toggle-label">Assume AI healthy</div>
        <input type="checkbox" defaultChecked />
      </div>
      <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }}>Preview decision</button>
    </aside>
  </div>
)}
```

## Verbatim required

- `AI Routing`
- `The Routing`
- `Ring timeout (seconds)`
- `Front desk numbers (comma-separated, E.164)`
- `Backup number (optional)`
- `AI SIP URI (read-only here; engineer-managed)`
- `Engineer-managed`
- `Hours per weekday`
- `Both blank means closed that day.`
- `Holidays (YYYY-MM-DD, one per line)`
- `AI handles after-hours calls`
- `AI handles in-hours overflow`
- `Save routing`
- `What would the agent do at a given moment, against the currently saved rules? (Save first if you want to preview a draft.)`
- `Preview decision`
- `Assume AI healthy`

## Verbatim that must STILL be present

- `AI Greeting` *(from 05H)*
- `Save greeting` *(from 05H)*
- All 8 original tab names + their first-line content.

## Forbidden

- Editing the AI Greeting tab body (`tab === 8`).
- Editing tab bodies 0-7.
- Removing scripts loaded by 05H.

## Success criteria

- File size between 14 KB and 70 KB.
- `'AI Routing'` is the 10th element of `TABS`.
- All verbatim strings above appear.
- All 8 original tabs + AI Greeting still in `TABS`.
