# Task 05K — settings.html: AI Knowledge tab

Append the **AI Knowledge** tab. After this task: 12 tabs total. AI Greeting (05H), AI Routing (05I), AI Services (05J) must remain.

## Output

Modify exactly one file: `ui_kits/website/settings.html`.

## Allow-list

`^ui_kits/website/settings\.html$`

## Goal

A new tab labelled `AI Knowledge` (index 11). Lists the `knowledge_docs` array from the current clinic's AI config. Each row shows filename, title, last updated, word count, and an expand-to-edit textarea for the body.

## Approach

Append `'AI Knowledge'` to `TABS`. Add a `tab === 11` body block.

### Tab body 11 — AI Knowledge

```jsx
{tab === 11 && (() => {
  const docs = AI_CONFIG_FOR_CURRENT?.knowledge_docs || [];
  const [openId, setOpenId] = React.useState(null);
  return (
    <div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '1.05rem', color: 'var(--rr-navy-800)', marginBottom: 4 }}>The Knowledge base</div>
      <div style={{ fontFamily: 'var(--font-ui)', fontSize: '0.82rem', color: 'var(--rr-slate-dark)', marginBottom: 14 }}>
        Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.
      </div>

      {docs.length === 0 && (
        <div style={{ background: 'var(--rr-warm-white)', border: '1px solid var(--rr-parchment)', borderRadius: 6, padding: 18, textAlign: 'center', fontFamily: 'var(--font-ui)', fontSize: '0.85rem', color: 'var(--rr-slate-dark)' }}>
          No knowledge yet. Drop a markdown file in to give the agent something to draw on.
        </div>
      )}

      {docs.map(doc => {
        const isOpen = openId === doc.filename;
        return (
          <div key={doc.filename} style={{ border: '1px solid var(--rr-parchment)', borderRadius: 6, marginBottom: 10, overflow: 'hidden' }}>
            <div onClick={() => setOpenId(isOpen ? null : doc.filename)}
                 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 18px', cursor: 'pointer', background: isOpen ? 'var(--rr-warm-white)' : '#fff' }}>
              <div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--rr-slate-dark)' }}>{doc.filename}</div>
                <div style={{ fontFamily: 'var(--font-ui)', fontWeight: 600, fontSize: '0.92rem', color: 'var(--rr-navy-800)', marginTop: 2 }}>{doc.title}</div>
              </div>
              <div style={{ display: 'flex', gap: 18, alignItems: 'center', fontFamily: 'var(--font-ui)', fontSize: '0.78rem', color: 'var(--rr-slate-dark)' }}>
                <span>Last updated: {doc.last_updated}</span>
                <span>Word count: {doc.word_count}</span>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                     strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
                     style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 200ms' }}>
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
            </div>
            {isOpen && (
              <div style={{ padding: '14px 18px', borderTop: '1px solid var(--rr-parchment)', background: '#fff' }}>
                <textarea
                  className="d-input"
                  rows={10}
                  defaultValue={doc.body}
                  style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', resize: 'vertical' }}
                />
              </div>
            )}
          </div>
        );
      })}

      <button className="btn btn-primary btn-sm" style={{ marginTop: 14 }}>Save knowledge updates</button>
    </div>
  );
})()}
```

## Verbatim required

- `AI Knowledge`
- `The Knowledge base`
- `Edit your AI's knowledge base. The agent uses these files as ground truth when answering caller questions.`
- `Last updated`
- `Word count`
- `Save knowledge updates`
- `denture_faq.md`
- `practice_info.md`
- `No knowledge yet. Drop a markdown file in to give the agent something to draw on.`

## Verbatim that must STILL be present

- All 11 prior tab names.
- All earlier verbatim from 05H, 05I, 05J.

## Forbidden

- Editing tab bodies 0-10.
- Adding new top-level CSS classes outside the existing `<style>` block.
- Calling `React.useState` outside the IIFE arrow body — must be at the top of the IIFE returned by `(() => { … })()` so React's rules-of-hooks aren't violated.

## Success criteria

- File size between 18 KB and 90 KB.
- `'AI Knowledge'` is the 12th element of `TABS`.
- All verbatim strings above appear.
- The `<script src="../../data/ai_config.js">` line still present.
