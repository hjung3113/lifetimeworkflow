"""The single self-contained inlined HTML/JS page for the local memory web UI (MEM2-07, SC1).

``PAGE`` is ONE string: an HTML document with an inline ``<style>`` block (every UI-SPEC token as a
CSS custom property) and inline vanilla JS. It has **zero** external assets — no framework, no CDN,
no web font, no ``<script src>``/``<link href>``, no image URL, no external ``fetch``. "Local only"
is literal (D-16-01 / T-16-06): the JS fetches ONLY the same-origin ``/api/*`` endpoints the server
(:mod:`tools.memory_ui.server`) mounts, using relative paths.

The page implements the UI-SPEC interaction contract:
  * two-column layout (left ~320px list panel + fluid right detail panel);
  * the five item states (empty list, active, retired, unsaved-edit, post-retire);
  * a Referrers ("what points to this") sub-panel reading ``/api/pointers``;
  * the two-tier referential-integrity confirm in a native ``<dialog>`` — a lightweight
    zero-referrer confirm vs an amber N-referrer warning dialog whose DEFAULT keyboard focus is
    ``Cancel`` and whose destructive ``Retire anyway`` is never the default (D-16-03 / T-16-04);
  * real ``<button>`` controls with text labels and text status badges (never colour-only).

The add-agreement ``Because`` field is REQUIRED: the page never fabricates a reason — a blank value
is refused by the sanctioned writer and the verbatim ``REFUSED:`` message is surfaced (anti-invent,
T-16-02). The copy strings below are lifted verbatim from the UI-SPEC Copywriting Contract.
"""

from __future__ import annotations

# ruff: noqa: E501 -- PAGE is a single inlined HTML/CSS/JS data blob; its lines are not Python code.

# NOTE: keep this file free of the substrings "http" + "://" and "//cdn" — the page must reference
# no external URL of any kind (T-16-06); the Task-1 gate greps PAGE for them.
PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Memory</title>
<style>
:root {
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;

  --size-meta: 12px;
  --size-body: 14px;
  --size-title: 18px;
  --size-heading: 22px;

  --weight-regular: 400;
  --weight-semibold: 600;

  --color-surface: #ffffff;
  --color-text: #1a1a1a;
  --color-panel: #f4f5f7;
  --color-hairline: #e4e6ea;
  --color-muted: #6b7280;
  --color-accent: #2563eb;
  --color-destructive: #b91c1c;

  --warn-fill: #fff7ed;
  --warn-text: #c2410c;
  --warn-border: #fdba74;

  --badge-active-fill: #e4e6ea;
  --badge-active-text: #374151;
  --badge-retired-fill: #6b7280;
  --badge-retired-text: #ffffff;
  --dirty: #c2410c;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  height: 100%;
  font-family: var(--font-ui);
  font-size: var(--size-body);
  line-height: 1.5;
  color: var(--color-text);
  background: var(--color-surface);
}

:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }

header.appbar {
  padding: var(--space-md) var(--space-xl);
  border-bottom: 1px solid var(--color-hairline);
  font-size: var(--size-heading);
  font-weight: var(--weight-semibold);
  line-height: 1.2;
}

main {
  display: flex;
  gap: var(--space-lg);
  align-items: stretch;
  min-height: calc(100% - 60px);
}

nav.list {
  flex: 0 0 320px;
  background: var(--color-panel);
  border-right: 1px solid var(--color-hairline);
  padding: var(--space-md);
  overflow-y: auto;
}

section.detail {
  flex: 1 1 auto;
  background: var(--color-surface);
  padding: var(--space-lg);
  overflow-y: auto;
}

.group-label {
  font-size: var(--size-meta);
  font-weight: var(--weight-semibold);
  color: var(--color-muted);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin: var(--space-md) 0 var(--space-sm);
}

ul.rows { list-style: none; margin: 0; padding: 0; }

li.row { margin: 0; }

button.row-btn {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-sm);
  width: 100%;
  text-align: left;
  padding: var(--space-sm);
  border: 0;
  border-left: 2px solid transparent;
  background: transparent;
  font: inherit;
  color: var(--color-text);
  cursor: pointer;
}
button.row-btn:hover { background: var(--color-hairline); }
button.row-btn.selected {
  border-left-color: var(--color-accent);
  color: var(--color-accent);
  font-weight: var(--weight-semibold);
}
button.row-btn.retired .row-name { text-decoration: line-through; color: var(--color-muted); }

.divider {
  border: 0;
  border-top: 1px solid var(--color-hairline);
  margin: var(--space-md) 0;
}

.toggle {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--size-meta);
  color: var(--color-muted);
  margin-top: var(--space-sm);
}

.badge {
  font-size: var(--size-meta);
  font-weight: var(--weight-semibold);
  line-height: 1.4;
  padding: var(--space-xs) var(--space-sm);
  border-radius: 3px;
}
.badge.active { background: var(--badge-active-fill); color: var(--badge-active-text); }
.badge.retired { background: var(--badge-retired-fill); color: var(--badge-retired-text); }

.item-title {
  font-size: var(--size-title);
  font-weight: var(--weight-semibold);
  line-height: 1.3;
  margin: 0;
}
.item-title.retired { text-decoration: line-through; color: var(--color-muted); }

.title-row { display: flex; align-items: center; gap: var(--space-sm); flex-wrap: wrap; }

.meta { font-size: var(--size-meta); color: var(--color-muted); line-height: 1.4; }

.dirty-dot {
  display: inline-block;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--dirty);
  margin-right: var(--space-xs);
}

.referrers {
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  padding: var(--space-md);
  margin: var(--space-md) 0;
  background: var(--color-panel);
}
.referrers h3 { margin: 0 0 var(--space-sm); font-size: var(--size-body); }
.referrers .freshness { font-size: var(--size-meta); color: var(--color-muted); }
ul.referrer-list { list-style: none; margin: var(--space-sm) 0 0; padding: 0; font-family: var(--font-mono); font-size: var(--size-meta); }
ul.referrer-list li { padding: var(--space-xs) 0; }
.kind-tag { color: var(--color-muted); margin-left: var(--space-sm); }

.warn-banner {
  background: var(--warn-fill);
  color: var(--warn-text);
  border: 1px solid var(--warn-border);
  border-radius: 4px;
  padding: var(--space-sm) var(--space-md);
  margin: var(--space-md) 0;
  font-size: var(--size-body);
}

.error { color: var(--color-destructive); font-size: var(--size-body); margin: var(--space-md) 0; }

textarea.editor {
  width: 100%;
  min-height: 280px;
  font-family: var(--font-mono);
  font-size: var(--size-body);
  line-height: 1.5;
  padding: var(--space-md);
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  resize: vertical;
}

pre.body-view {
  font-family: var(--font-mono);
  font-size: var(--size-body);
  line-height: 1.5;
  white-space: pre-wrap;
  background: var(--color-panel);
  padding: var(--space-md);
  border-radius: 4px;
}

label.field { display: block; margin: var(--space-md) 0; }
label.field span { display: block; font-size: var(--size-meta); color: var(--color-muted); margin-bottom: var(--space-xs); }
label.field input, label.field textarea {
  width: 100%;
  font: inherit;
  padding: var(--space-sm);
  border: 1px solid var(--color-hairline);
  border-radius: 4px;
  background: var(--color-panel);
}

.actions { display: flex; gap: var(--space-sm); margin-top: var(--space-md); flex-wrap: wrap; }

button {
  font: inherit;
  height: 32px;
  padding: var(--space-sm) var(--space-md);
  border-radius: 4px;
  cursor: pointer;
}
button.secondary { background: var(--color-surface); border: 1px solid var(--color-hairline); color: var(--color-text); }
button.primary { background: var(--color-accent); border: 1px solid var(--color-accent); color: #ffffff; }
button.destructive { background: var(--color-destructive); border: 1px solid var(--color-destructive); color: #ffffff; }

dialog {
  border: 1px solid var(--color-hairline);
  border-radius: 6px;
  padding: 0;
  max-width: 520px;
}
dialog .dlg-body { padding: var(--space-lg); }
dialog.warn .dlg-header {
  background: var(--warn-fill);
  color: var(--warn-text);
  border-bottom: 1px solid var(--warn-border);
  padding: var(--space-md) var(--space-lg);
  font-weight: var(--weight-semibold);
}
dialog .dlg-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); padding: var(--space-md) var(--space-lg); border-top: 1px solid var(--color-hairline); }
</style>
</head>
<body>
<header class="appbar">Memory</header>
<main>
  <nav class="list" aria-label="Memory items">
    <div class="group-label">Progress state</div>
    <ul class="rows" id="state-list"></ul>
    <div class="group-label">Agreements</div>
    <ul class="rows" id="agreement-list"></ul>
    <div class="actions">
      <button class="secondary" id="new-agreement" type="button">New agreement</button>
    </div>
    <label class="toggle">
      <input type="checkbox" id="show-retired"> Show retired
    </label>
  </nav>
  <section class="detail" id="detail" aria-live="polite">
    <p class="meta">Select an item on the left.</p>
  </section>
</main>

<dialog id="confirm-dialog">
  <div class="dlg-header" id="dlg-header" hidden></div>
  <div class="dlg-body" id="dlg-body"></div>
  <div class="dlg-actions">
    <button class="secondary" id="dlg-cancel" autofocus>Cancel</button>
    <button class="destructive" id="dlg-confirm">Retire anyway</button>
  </div>
</dialog>

<script>
"use strict";

// ---- copy strings (verbatim from the UI-SPEC Copywriting Contract) ----------------------------
const COPY = {
  emptyAgreementsHeading: "No active agreements",
  emptyAgreementsBody: "This is expected. Agreements are captured only from explicit feedback via /agree — never authored by a tool. Retired agreements, if any, appear under Show retired.",
  emptyReferrers: "Nothing points to this item. No .memory/… path or slug references were found in the scanned roots (docs/, harness/, inject.py, .memory/README.md, AGENTS.md). Retiring or renaming it will not orphan anything.",
  becauseRequired: "Can't add: a reason is required. The Because field explains why this agreement exists. Enter the reason from your own feedback — the tool will not invent one.",
  staleIndex: "Referrers below are from the last regen. Run /refresh-memory (or reload) to rescan before relying on this list.",
  savedConfirm: (d) => "Saved. updated: stamped " + d + "; body unchanged elsewhere.",
  postRetire: (slug) => "Retired. " + slug + " is now status: retired — kept, not deleted. It stays listed under Show retired.",
  retireZero: (slug) => "Retire " + slug + "? It will be marked status: retired, not deleted.",
  retireN: (n, item) => n + " references point to " + item + ". Retiring it will orphan them. This tool will not rewrite those files — you must reconcile them by hand.",
  discardPrompt: (item) => "Discard unsaved changes to " + item + "?",
};

// ---- tiny state -------------------------------------------------------------------------------
let selected = null;      // {id, kind: "state"|"agreement", status}
let dirty = false;

const $ = (id) => document.getElementById(id);
const el = (tag, attrs, ...kids) => {
  const n = document.createElement(tag);
  for (const k in (attrs || {})) {
    if (k === "class") n.className = attrs[k];
    else if (k === "text") n.textContent = attrs[k];
    else n.setAttribute(k, attrs[k]);
  }
  for (const kid of kids) n.append(kid);
  return n;
};

async function api(path, opts) {
  const res = await fetch(path, opts);  // same-origin relative path only
  return res;
}

// ---- list panel -------------------------------------------------------------------------------
async function loadList() {
  const showRetired = $("show-retired").checked;
  const res = await api("/api/items?show_retired=" + (showRetired ? "1" : "0"));
  const data = await res.json();

  const stateUl = $("state-list");
  stateUl.replaceChildren();
  for (const name of data.state) stateUl.append(rowItem(name, "state", null));

  const agUl = $("agreement-list");
  agUl.replaceChildren();
  const active = data.agreements.filter((a) => a.status !== "retired");
  const retired = data.agreements.filter((a) => a.status === "retired");
  if (active.length === 0 && retired.length === 0) {
    agUl.append(el("li", { class: "row" },
      el("p", { class: "meta", text: COPY.emptyAgreementsHeading }),
      el("p", { class: "meta", text: COPY.emptyAgreementsBody })));
  } else {
    for (const a of active) agUl.append(rowItem(a.slug, "agreement", a.status));
    if (retired.length) {
      agUl.append(el("hr", { class: "divider" }));
      for (const a of retired) agUl.append(rowItem(a.slug, "agreement", a.status));
    }
  }
}

function rowItem(id, kind, status) {
  const li = el("li", { class: "row" });
  const cls = "row-btn" + (status === "retired" ? " retired" : "") +
    (selected && selected.id === id ? " selected" : "");
  const btn = el("button", { class: cls, type: "button" }, el("span", { class: "row-name", text: id }));
  if (kind === "agreement" && status) {
    const badge = el("span", { class: "badge " + (status === "retired" ? "retired" : "active"),
      text: status === "retired" ? "RETIRED" : "ACTIVE" });
    btn.append(badge);
  }
  btn.addEventListener("click", () => select(id, kind, status));
  li.append(btn);
  return li;
}

// ---- detail panel -----------------------------------------------------------------------------
async function select(id, kind, status) {
  if (dirty && !confirmDiscard()) return;
  dirty = false;
  selected = { id, kind, status };
  await loadList();       // refresh selection highlight
  await renderDetail();
}

function confirmDiscard() {
  return window.confirm(COPY.discardPrompt(selected ? selected.id : ""));
}

async function renderDetail() {
  const detail = $("detail");
  detail.replaceChildren();
  if (!selected) { detail.append(el("p", { class: "meta", text: "Select an item on the left." })); return; }

  const { id, kind, status } = selected;
  const titleRow = el("div", { class: "title-row" });
  titleRow.append(el("h2", { class: "item-title" + (status === "retired" ? " retired" : ""), text: id }));
  if (kind === "agreement" && status) {
    titleRow.append(el("span", { class: "badge " + (status === "retired" ? "retired" : "active"),
      text: status === "retired" ? "RETIRED" : "ACTIVE" }));
  }
  detail.append(titleRow);

  // referrers sub-panel
  detail.append(await referrersPanel(id));

  // body view + edit affordance
  const bodyRes = await api("/api/item?id=" + encodeURIComponent(id));
  const bodyText = bodyRes.ok ? await bodyRes.text() : "";
  detail.append(el("pre", { class: "body-view", text: bodyText }));

  const actions = el("div", { class: "actions" });
  if (kind === "state") {
    actions.append(button("Edit", "secondary", () => editState(id, bodyText)));
  } else {
    if (status !== "retired") {
      actions.append(button("Retire", "secondary", () => startRetire(id)));
    }
  }
  detail.append(actions);
}

async function referrersPanel(id) {
  const panel = el("div", { class: "referrers" });
  panel.append(el("h3", { text: "Referrers — what points to this" }));
  panel.append(el("div", { class: "freshness", text: "from last regen" }));
  const referrers = await fetchReferrers(id);
  if (!referrers.length) {
    panel.append(el("p", { class: "meta", text: COPY.emptyReferrers }));
  } else {
    const ul = el("ul", { class: "referrer-list" });
    for (const r of referrers) {
      const li = el("li", {}, document.createTextNode(r.file + ":" + r.line));
      li.append(el("span", { class: "kind-tag", text: r.kind }));
      ul.append(li);
    }
    panel.append(ul);
  }
  return panel;
}

async function fetchReferrers(id) {
  const res = await api("/api/pointers?item=" + encodeURIComponent(id));
  if (!res.ok) return [];
  const data = await res.json();
  return data.referrers || [];
}

function button(label, variant, onClick) {
  const b = el("button", { class: variant, type: "button", text: label });
  b.addEventListener("click", onClick);
  return b;
}

// ---- edit a state file ------------------------------------------------------------------------
function editState(id, bodyText) {
  const detail = $("detail");
  detail.replaceChildren();
  detail.append(el("h2", { class: "item-title", text: id }));
  const meta = el("p", { class: "meta" });
  detail.append(meta);
  const ta = el("textarea", { class: "editor" });
  ta.value = bodyText;
  ta.addEventListener("input", () => {
    dirty = true;
    meta.replaceChildren(el("span", { class: "dirty-dot" }), document.createTextNode("Unsaved changes"));
  });
  detail.append(ta);
  const status = el("p", { class: "meta" });
  const actions = el("div", { class: "actions" });
  actions.append(button("Save changes", "primary", async () => {
    const res = await api("/api/progress/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item: id, body: ta.value }),
    });
    if (res.ok) {
      dirty = false;
      const today = new Date().toISOString().slice(0, 10);
      status.className = "meta";
      status.textContent = COPY.savedConfirm(today);
      meta.replaceChildren();
    } else {
      status.className = "error";
      status.textContent = "Refused. " + (await res.text());
    }
  }));
  actions.append(button("Cancel", "secondary", () => { dirty = false; renderDetail(); }));
  detail.append(actions, status);
}

// ---- add an agreement (Because is REQUIRED — the tool never fabricates one) -------------------
function showAddForm() {
  if (dirty && !confirmDiscard()) return;
  dirty = false;
  selected = null;
  loadList();
  const detail = $("detail");
  detail.replaceChildren();
  detail.append(el("h2", { class: "item-title", text: "New agreement" }));

  const mk = (name, label, required, mono) => {
    const wrap = el("label", { class: "field" });
    wrap.append(el("span", { text: label + (required ? " (required)" : "") }));
    const input = name === "rule" || name === "because"
      ? el("textarea", { rows: "3" })
      : el("input", { type: "text" });
    input.id = "add-" + name;
    if (required) input.required = true;
    if (mono) input.style.fontFamily = "var(--font-mono)";
    wrap.append(input);
    detail.append(wrap);
  };
  mk("slug", "Slug", true, true);
  mk("title", "Title", true, false);
  mk("rule", "Rule", true, false);
  mk("because", "Because", true, false);   // anti-invent: user's own reason, never fabricated
  mk("related", "Related", false, true);

  const status = el("p", { class: "meta" });
  const actions = el("div", { class: "actions" });
  actions.append(button("Add agreement", "primary", async () => {
    const because = $("add-because").value.trim();
    if (!because) {   // client-side guard; the server refuses too (never invents a reason)
      status.className = "error";
      status.textContent = COPY.becauseRequired;
      return;
    }
    const payload = {
      slug: $("add-slug").value.trim(),
      title: $("add-title").value,
      rule: $("add-rule").value,
      because: because,
      related: $("add-related").value.trim() || null,
    };
    const res = await api("/api/agreement/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      await select(payload.slug, "agreement", "active");
    } else {
      status.className = "error";
      status.textContent = "Refused. " + (await res.text());
    }
  }));
  actions.append(button("Cancel", "secondary", () => renderDetail()));
  detail.append(actions, status);
}

// ---- retire flow (referential-integrity confirm, D-16-03) -------------------------------------
async function startRetire(slug) {
  const referrers = await fetchReferrers(slug);
  const dlg = $("confirm-dialog");
  const header = $("dlg-header");
  const bodyDiv = $("dlg-body");
  const confirmBtn = $("dlg-confirm");
  bodyDiv.replaceChildren();

  if (!referrers.length) {
    // zero-referrer lightweight confirm — routine state flip, no amber/red framing
    dlg.classList.remove("warn");
    header.hidden = true;
    bodyDiv.append(el("p", { text: COPY.retireZero(slug) }));
    confirmBtn.textContent = "Retire";
    confirmBtn.className = "secondary";
  } else {
    // N-referrer amber warning dialog
    dlg.classList.add("warn");
    header.hidden = false;
    header.textContent = "Reconcile before retiring";
    bodyDiv.append(el("p", { text: COPY.retireN(referrers.length, slug) }));
    const ul = el("ul", { class: "referrer-list" });
    for (const r of referrers) {
      const li = el("li", {}, document.createTextNode(r.file + ":" + r.line));
      li.append(el("span", { class: "kind-tag", text: r.kind }));
      ul.append(li);
    }
    bodyDiv.append(ul);
    confirmBtn.textContent = "Retire anyway";
    confirmBtn.className = "destructive";
  }

  const onConfirm = async () => {
    cleanup();
    dlg.close();
    await doRetire(slug);
  };
  const onCancel = () => { cleanup(); dlg.close(); };
  function cleanup() {
    confirmBtn.removeEventListener("click", onConfirm);
    $("dlg-cancel").removeEventListener("click", onCancel);
  }
  confirmBtn.addEventListener("click", onConfirm);
  $("dlg-cancel").addEventListener("click", onCancel);

  dlg.showModal();
  $("dlg-cancel").focus();   // Cancel is the DEFAULT focus; Esc also cancels
}

async function doRetire(slug) {
  const res = await api("/api/agreement/retire", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ slug: slug, confirm: true }),
  });
  if (res.ok) {
    selected = { id: slug, kind: "agreement", status: "retired" };
    $("show-retired").checked = true;
    await loadList();
    await renderDetail();
    $("detail").prepend(el("p", { class: "meta", text: COPY.postRetire(slug) }));
  } else {
    $("detail").prepend(el("p", { class: "error", text: "Refused. " + (await res.text()) }));
  }
}

// ---- boot -------------------------------------------------------------------------------------
$("show-retired").addEventListener("change", loadList);
$("new-agreement").addEventListener("click", showAddForm);
loadList();
</script>
</body>
</html>
"""
