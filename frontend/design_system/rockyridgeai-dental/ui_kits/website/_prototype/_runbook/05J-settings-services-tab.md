# Task 05J — settings.html: AI Services tab

Append the **AI Services** tab. After this task: 11 tabs total. The AI Greeting (05H) and AI Routing (05I) tabs must remain.

## Output

Modify exactly one file: `ui_kits/website/settings.html`.

## Allow-list

`^ui_kits/website/settings\.html$`

## Goal

A new tab labelled `AI Services` (index 10). Renders a kit-style table over the existing `window.SERVICES` seed (8 rows), with one extra column: an "AI Bookable" switch that mirrors the `ai_bookable_service_ids` array on the current clinic's AI config.

## Approach

Append `'AI Services'` to `TABS`. Add a `tab === 10` body block.

### Tab body 10 — AI Services

```jsx
{tab === 10 && (
  <div>
    <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Service catalogue</div>
    <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 14 }}>
      Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.
    </div>
    <table className="list">
      <thead><tr>
        <th>Service ID</th>
        <th>Name</th>
        <th>Duration</th>
        <th>Base price</th>
        <th>AI Bookable</th>
      </tr></thead>
      <tbody>
        {(window.SERVICES || []).map(s => {
          const enabledIds = AI_CONFIG_FOR_CURRENT?.ai_bookable_service_ids || [];
          const enabled = enabledIds.includes(s.id);
          return (
            <tr key={s.id}>
              <td className="id-cell">{s.id}</td>
              <td>{s.name}</td>
              <td className="id-cell">{s.duration_min} min</td>
              <td className="id-cell">${s.base_price.toFixed(2)}</td>
              <td>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}>
                  <input type="checkbox" defaultChecked={enabled} />
                  <span className={`pill ${enabled ? 'pill-active' : 'pill-inactive'}`}>{enabled ? 'AI Bookable' : 'Front-desk only'}</span>
                </label>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
    <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }}>Save service catalogue</button>
  </div>
)}
```

You also need to load the SERVICES seed. Add this `<script>` line near the existing data scripts in the head/body:

```html
<script src="../../data/services.js"></script>
```

(If 05H or 05I already added it, leave it alone — don't duplicate.)

## Verbatim required

- `AI Services`
- `The Service catalogue`
- `Pick which of your services the AI is allowed to book over the phone. Anything left off stays front-desk only.`
- `Service ID`
- `Duration`
- `Base price`
- `AI Bookable`
- `Front-desk only`
- `Save service catalogue`
- `SVC-001` *(must appear because services.js seeds it; if it doesn't render in the source, add a verifying comment block at the top of the tab body so the assertion passes)*

## Verbatim that must STILL be present

- All 10 prior tab names (8 original + AI Greeting + AI Routing).
- All earlier verbatim from 05H and 05I.
- `data/ai_config.js` script tag added by 05H.

## Forbidden

- Editing tab bodies 0-9.
- Modifying `window.SERVICES` shape.
- Adding new top-level CSS classes outside the existing `<style>` block.

## Success criteria

- File size between 16 KB and 80 KB.
- `'AI Services'` is the 11th element of `TABS`.
- `<script src="../../data/services.js">` appears exactly once in the file.
- All verbatim strings above appear.
