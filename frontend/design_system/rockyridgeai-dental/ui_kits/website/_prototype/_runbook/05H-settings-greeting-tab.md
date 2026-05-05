# Task 05H — settings.html: AI Greeting tab

Append the **AI Greeting** tab to the kit's existing `settings.html`. The 8 existing tabs (Clinic info, Working hours, Operatories, Providers, Users & roles, Integrations, Notifications, Audit log) must remain byte-identical. After this task the page renders 9 tabs total.

## Output

Modify exactly one file: `ui_kits/website/settings.html`.

## Allow-list

`^ui_kits/website/settings\.html$`

## Goal

A new tab labelled `AI Greeting` (index 8). The tab body lets the owner edit the AI receptionist greeting, see the engineer-approval state, and approve the clinic if they have the permission. Reads/writes from `window.AI_CONFIG[currentClinicId].greeting`.

## Approach

The current `TABS` array is on line 60:

```js
const TABS = ['Clinic info','Working hours','Operatories','Providers','Users & roles','Integrations','Notifications','Audit log'];
```

Append `'AI Greeting'` so it becomes:

```js
const TABS = ['Clinic info','Working hours','Operatories','Providers','Users & roles','Integrations','Notifications','Audit log','AI Greeting'];
```

Add a new tab body block before `tab === 7` block ends — but importantly, leave `tab === 0` … `tab === 7` byte-identical. The new block is `tab === 8`.

Also add at the top of the `<script type="text/babel">` section (right after `window.RRD.requireSession?.();`):

```js
const CURRENT_CLINIC_ID = (window.RRD?.getCurrentClinicId?.()) || (window.CLINICS?.[0]?.id) || null;
const AI_CONFIG_FOR_CURRENT = (CURRENT_CLINIC_ID && window.AI_CONFIG?.[CURRENT_CLINIC_ID]) || null;
```

You'll also need to load the new data file. Add this `<script>` line in the `<head>` or near the top of the body's script block:

```html
<script src="../../data/clinics.js"></script>
<script src="../../data/ai_config.js"></script>
```

(Place these next to the existing `<script src="../../lib/query.js">`.)

### Tab body 8 — AI Greeting

```jsx
{tab === 8 && (
  <div style={{ maxWidth: 720 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
      <div>
        <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Greeting</div>
        <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)' }}>What the AI says when it picks up a call.</div>
      </div>
      <span className={`pill ${AI_CONFIG_FOR_CURRENT?.greeting?.status === 'approved' ? 'pill-active' : 'pill-inactive'}`}>
        {AI_CONFIG_FOR_CURRENT?.greeting?.status === 'approved' ? 'Auto-approval enabled' : 'Pending review'}
      </span>
    </div>

    {(!AI_CONFIG_FOR_CURRENT?.greeting?.text) && (
      <div style={{ background: '#FFF8E6', border: '1px solid #F4D58E', borderRadius: 6, padding: '10px 12px', fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: '#7A5B0E', marginBottom: 14 }}>
        No custom greeting persisted yet. The agent uses the YAML default until you save one.
      </div>
    )}

    <div className="field">
      <label className="lbl">Greeting message</label>
      <textarea
        className="d-input"
        rows={4}
        defaultValue={AI_CONFIG_FOR_CURRENT?.greeting?.text || ''}
        placeholder="Welcome to … How can I help you today?"
        maxLength={400}
        style={{ fontFamily: 'var(--font-ui)', resize: 'vertical' }}
        onChange={(e) => {
          const len = e.target.value.length;
          const counter = document.getElementById('rrd-greeting-counter');
          if (counter) {
            counter.textContent = `${len} / 280 characters`;
            counter.style.color = len > 280 ? '#9B2335' : (len > 240 ? '#B45309' : 'var(--rr-slate-dark)');
          }
        }}
      />
      <div id="rrd-greeting-counter" style={{ fontFamily: 'var(--font-mono)', fontSize: '0.74rem', color: 'var(--rr-slate-dark)', marginTop: 4 }}>0 / 280 characters</div>
    </div>

    <button className="btn btn-primary btn-sm" style={{ marginTop: 8 }}>Save greeting</button>

    <div style={{ marginTop: 24, paddingTop: 18, borderTop: '1px solid var(--rr-parchment)' }}>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '0.95rem', color: 'var(--rr-navy-800)', marginBottom: 6 }}>Engineer approval</div>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', lineHeight: 1.5, marginBottom: 12 }}>
        First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.
      </div>
      <button className="btn btn-ghost btn-sm" disabled
              title="Only your engineering partner can click this — they'll do it once, then you're free to edit anytime."
              style={{ opacity: 0.55, cursor: 'not-allowed' }}>
        Approve clinic (engineer-gated)
      </button>
    </div>
  </div>
)}
```

## Verbatim required (must appear in the rendered DOM after this task)

- `AI Greeting`
- `The Greeting`
- `Welcome to … How can I help you today?` (`…` is U+2026)
- `0 / 280 characters`
- `No custom greeting persisted yet. The agent uses the YAML default until you save one.`
- `First-time edits land as pending_review. An engineer (email allow-listed in GREETING_APPROVERS) must call /approve once per clinic; after that, edits auto-approve.`
- `Approve clinic (engineer-gated)`
- `Save greeting`
- `Auto-approval enabled`
- `Pending review`
- `What the AI says when it picks up a call.`

## Verbatim that must STILL be present (existing tabs)

- `'Clinic info'`
- `'Working hours'`
- `'Operatories'`
- `'Providers'`
- `'Users & roles'`
- `'Integrations'`
- `'Notifications'`
- `'Audit log'`
- `<input className="d-input" defaultValue="Oak Dental Calgary" />` *(existing first tab body)*
- `Send SMS + email when appointment is booked` *(existing notifications tab body)*

## Forbidden

- Editing tab bodies for `tab === 0` through `tab === 7`.
- Renaming the `SettingsPage` component.
- Removing existing imports / scripts.
- Adding any new `.css` file or new `<style>` rules outside the existing inline `<style>` block.

## Success criteria

- File size between 12 KB and 60 KB.
- `'AI Greeting'` appears in the `TABS` array (the 9th element).
- All 11 verbatim strings above appear in the file.
- All 8 original tab labels still in `TABS`.
- `data/clinics.js` and `data/ai_config.js` are loaded via `<script src="../../data/...">` lines.
