# IntelliOps — Roadmap

Current priority: backend optimizations and agent quality. The React frontend is the last phase.

---

## Current Phase — Backend & Agent

- [ ] Latency and token usage optimizations
- [ ] Report quality improvements per intelligence mode
- [ ] Integration tests per mode

---

## Phase 2 — SaaS Frontend (React)

**Stack:** Vite + React SPA · Supabase · existing FastAPI (unchanged)

### Auth
- [ ] Email/password login (Supabase Auth)
- [ ] Google OAuth login (Supabase Auth)
- [ ] AuthGuard — protected route wrapper
- [ ] User profile (`/settings`)

### Dashboard — Research history
- [ ] Card grid per research (company, mode, date, status)
- [ ] Filter sidebar: mode, date presets (today / week / month), company search
- [ ] Card click opens `/report/:id`

### Research
- [ ] Mode-specific form (`ResearchForm`) replicating current `build_query()` logic
- [ ] Real-time SSE streaming (`StreamViewer`) — Activity + Report panels
- [ ] Auto-save report on `done` event

### Saved report
- [ ] Rendered markdown view at `/report/:id`
- [ ] Export: PDF, Obsidian, Slack

### Backend (FastAPI)
- [ ] `POST /reports/save` — persists research + report to Supabase after stream ends

### Database (Supabase)
- [ ] `profiles` table (id = auth.uid, full_name, avatar, org_id)
- [ ] `researches` table (id, user_id, mode, company, query, status, token_count, created_at)
- [ ] `reports` table (id, research_id, markdown_content, pdf_url, updated_at)
- [ ] Row Level Security by user_id on all tables
- [ ] Supabase Storage — PDFs per research

---

## Phase 3 — New Intelligence Modes

Each mode = new file in `backend/prompts/modes/` + form in `ResearchForm` + entry in `MODE_FILES`.

- [ ] **Market Mapping** — map players, segments, and positioning across a sector
- [ ] **Leadership Intel** — executive background, track record, and professional connections
- [ ] **Funding & Deal Intelligence** — investment rounds, M&A activity, and capital movements
- [ ] **Risk Assessment** — multi-dimensional scorecard: reputational, financial, regulatory, geopolitical
- [ ] **Regulatory Watch** — regulatory changes by sector and jurisdiction
- [ ] **Talent Signal** — hiring patterns as a proxy for undisclosed strategic direction
- [ ] **Partnership & Ecosystem Mapping** — alliances, integrations, and partner ecosystem

---

## Phase 4 — Collaboration & Org

- [ ] Organization workspaces (multi-tenant)
- [ ] Internal report sharing (link within org)
- [ ] Multi-user orgs with roles (admin / member)

---

## Phase 10 — Monetization

- [ ] Credit-based plans (X credits per subscription tier)
- [ ] Pay as You Go for Pro plan
- [ ] Per-seat pricing add-on
- [ ] Billing dashboard
