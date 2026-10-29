# Catalog Gap Analysis Report
## skill-admin — marketplace-wishlist & catalog coverage audit

**Date:** 2026-10-28
**Catalog baseline:** 23 marketplaces, 363 plugins, 1261 skills, 266 commands, 419 agents (1946 total capabilities)

---

## 1. Executive Summary

| Category | Count | Share | Assessment |
|---|---|---|---|
| React/Next.js + React-adjacent | ~47 capabilities | ~2.4% | **Over-represented** (13 react-* / nextjs-* skills alone) |
| Marketing / sales / growth | ~15 plugins, ~30+ skills | ~1.8% | **Over-represented** |
| Documents / office-suite | ~25+ skills across 6+ plugins | ~1.5% | **Over-represented** |
| Finance / legal / healthcare / life-sciences | ~3 marketplaces, ~20+ skills | ~1.2% | **Misaligned** with dev build-phase focus |
| .NET (dotnet-agent-skills, dotnet-skills, dotnet-claude-kit) | 3 marketplaces, ~170 capabilities | ~9% | **Adequate** but unbalanced (test-migration heavy, diagnostics thin) |
| Vue.js / Nuxt / Pinia / Vite | **0 capabilities** | 0% | **Critical gap** |
| Reverse engineering / Ghidra / IDA | **0 capabilities** | 0% | **Critical gap** |
| Multi-agent orchestration / parallel-execution governance | ~6 agents, 4 commands, 0 dedicated skills | ~0.5% | **Significant gap** |
| Security — offensive / pentest | 2 skills (attacker, claude-security) | 0.1% | **Critical gap** |
| TypeScript type-level / zod / zustand | ~3 skills (mattpocock TS + type-design) | 0.2% | **Critical gap** |

---

## 2. Over-Represented Capabilities

### 2.1 React/Next.js saturation

The catalog carries the following React/Next-specific skills (partial list from `awesome-claude-code-plugins`, `claude-code-workflows`, `anthropic-agent-skills`):

- `react-patterns`, `react-performance`, `react-native-patterns`, `react-native-dev`
- `nextjs-app`, `nextjs-app-router-patterns`, `nextjs-turbopack`
- `motion-foundations`, `motion-patterns`, `motion-advanced` (React-specific motion)
- `web-artifacts-builder`, `frontend-design`, `web-design-guidelines`
- `component-scaffold` (React/React Native)
- `hookify` (React hooks), `context7-docs-fetcher` (React-heavy)

**Assessment:** ~13 dedicated React/Next skills vs. **zero** Vue/Svelte/Angular skills. This bias skews the routing engine's semantic matches toward React even when the user asks for Vue or Svelte.

**Action:** No new additions. Optionally **downweight** React/Next matches in `recommend.py` when the query explicitly names an alternative framework (Vue/Svelte/Angular/Solid).

### 2.2 Marketing / sales / growth plugins

Installed via `awesome-claude-code-plugins` (the 195-plugin mega-aggregator):

| Plugin | Domain |
|---|---|
| `agentkits-marketing` | Marketing agent kit |
| `analytics-reporter` | Metrics reporting |
| `app-store-optimizer` | ASO |
| `b2b-project-shipper` | B2B launch |
| `brand-guardian` | Brand intelligence |
| `pricing-packaging-specialist` | Pricing strategy |
| `product-sales-specialist` | Sales |
| `product-org-os` | Product management |
| `reddit-community-builder` | Community marketing |
| `social-media-publisher` | Social media |
| `social-visualization` | Social data viz |
| `hermes-tweet` | Twitter/X ops |
| `app-store-optimizer` | ASO |
| `launch` | Product launch |
| `growth-hacker` | Growth engineering |
| `copywriting-*` | Copywriting |
| `seo-*` | SEO |
| `outreach-*` | Cold outreach |

**Assessment:** ~17+ plugins, ~35+ skills. These capabilities are commercially available, well-maintained, and broadly useful — but they consume ranking-engine attention when the actual ask is dev build-phase work. They are not "bad"; they are **miscategorized for this router's stated purpose**.

**Action:** Add an explicit `business-growth` domain to the routing tables with a lower default weight for dev-build-phase queries. Do not remove (they may still be valid for launch-phase routing).

### 2.3 Document / office-suite skills

Six separate plugins / skills cover office documents:

| Source | Capability |
|---|---|
| `anthropic-agent-skills` | `docx`, `xlsx`, `pptx`, `pdf`, `pdf-reading` |
| `awesome-claude-code-plugins` | `document-skills` plugin |
| `claude-plugins-official` | `docx`, `xlsx`, `pptx` |
| `claude-code-workflows` | `pptx-quality-gates` |

**Assessment:** Redundant coverage. The `anthropic-agent-skills` versions (from Anthropic) are the canonical implementations; the others are community mirrors. **Keep Anthropic versions; remove or downgrade community duplicates.**

### 2.4 Vertical / domain-specific marketplaces

Three marketplaces with zero general-purpose dev-build-phase value:

| Marketplace | Plugins | Skills | Purpose |
|---|---|---|---|
| `healthcare` | 1 | 10 | Clinical decision support, HIPAA |
| `life-sciences` | 0 | 0 | (empty) |
| `knowledge-work-plugins` | 0 | 0 | (empty) |
| `impeccable` | 0 | 0 | (empty) |
| `token-optimizer` | 0 | 0 | (empty) |
| `mattpocock` | 0 | 0 | (empty — but high reputation; see §4) |
| `pixelbin-claude-skill` | 0 | 1 | Image optimization (single-skill marketplace) |
| `super-board` | 0 | 8 | GitHub Project board runner |

**Assessment:** `life-sciences`, `knowledge-work-plugins`, `impeccable`, `token-optimizer` are **completely empty** — 0 plugins, 0 skills, 0 agents. They exist in the registry but contribute nothing to the catalog. `mattpocock` is empty in the current catalog but is a high-reputation marketplace that should be populated.

---

## 3. Under-Represented Capabilities

### 3.1 Vue.js / Nuxt / Pinia / Vite / Reka UI

**Current state: 0 capabilities.** Not one skill, command, agent, or plugin mentions Vue, Nuxt, Pinia, Vite, or Reka UI.

The user's routing tables explicitly list `vue` as a primary frontend domain with zero entries to route to. This is the single largest gap in the catalog.

### 3.2 Reverse Engineering / Binary Analysis / Firmware

**Current state: 0 capabilities.** No Ghidra, IDA Pro, radare2, Binary Ninja, decompile, disassemble, APK/IPA analysis, or embedded firmware skills exist.

The catalog has `attacker` (adversarial self-review) and `claude-security` (Anthropic's plugin), but these are **defensive code-review tools**, not reverse-engineering tools.

### 3.3 Security — Offensive / Pentest / CTF

**Current state: 2 capabilities.**
- `attacker` (adversarial self-review skill)
- `claude-security` (Anthropic's plugin)

No pentest workflow, no SecLists integration, no injection payload library, no CTF solver, no OSINT capability, no cloud-security posture review.

### 3.4 .NET Diagnostics / Profiling / Performance

**Current state:** `dotnet-agent-skills` has some coverage:
- `build-perf-baseline`, `build-perf-diagnostics`, `eval-performance`
- `dotnet-trace-collect` (exists in skills list)
- `optimizing-dotnet-performance` (agent)
- `database-performance`, `type-design-performance`

But there is **no dedicated diagnostics marketplace** covering `dotnet-dump`, `dotnet-counters`, `dotnet-gcdump`, Visual Studio Profiler, PerfView, or ETW/ETL trace analysis as first-class capabilities. The existing skills are high-level patterns, not tool-wrapping skills.

### 3.5 Multi-Agent Orchestration / Parallel Execution

**Current state:** ~6 agents, 4 commands, 0 dedicated skills.

Existing orchestration-adjacent capabilities:
- `conductor-orchestrator` (agent)
- `orchestrator` (agent)
- `ai-engineer` (agent)
- `/multi-agent-review` (command)
- `/fan-out` (command)
- `/dispatch` (command)
- `agent-manager-skill` (command)

What's missing:
- A **governing skill** that describes when to fan out vs. stay single-threaded (the SKILL.md mentions a "parallel-split safety rubric" but no installed capability enforces it)
- A **workflow orchestrator** skill for n8n/Airflow/Prefect-style DAG authoring
- A **session-manager** skill for coordinating multiple Claude Code sessions
- A **conflict-resolution** skill for when parallel agents modify the same files

### 3.6 TypeScript / Type-Level Programming

**Current state:** `mattpocock` marketplace exists but **has 0 entries in the catalog**. This is the highest-reputation TypeScript skill author (Total TypeScript, 100K+ students) and the marketplace is installed but empty.

Skills that do exist:
- `type-design-performance` (from dotnet-agent-skills — .NET-specific)
- `typescript-lsp` (from claude-plugins-official — language server, not type-level patterns)
- `zod` (community, exists in some form within awesome-claude-code-plugins)

**Missing:** `ts-pattern` / type-level pattern matching, `zustand` state management, advanced generic inference, conditional types, template literal types, mapped type transforms.

---

## 4. Wishlist Additions

### 4.1 Vue.js / Nuxt / Pinia / Vite / Reka UI

| Marketplace | URL | Est. Reputation | Rationale |
|---|---|---|---|
| `vuejs-ai/skills` | https://github.com/vuejs-ai/skills | 75 | Official Vue.js org skills collection. Vue 3 Composition API, Pinia, Vue Router, Vite. Source: community; Maintenance: active; Adoption: official (Vue org); Docs: good; Eval: untested |
| `onmax/nuxt-skills` | https://github.com/onmax/nuxt-skills | 70 | Vue + Nuxt + NuxtHub skills. Covers the full-stack Nuxt workflow including server routes, Nitro, and NuxtHub deployment. Source: community; Maintenance: active; Adoption: niche-to-popular; Docs: good; Eval: untested |
| `alexanderop/claude-skill-vue-development` | https://github.com/alexanderop/claude-skill-vue-development | 55 | Vue 3 + TypeScript-first development patterns. Smaller scope but focused. Source: community; Maintenance: active; Adoption: niche; Docs: minimal; Eval: untested |
| `harlan-zw/harlan-claude-code` | https://github.com/harlan-zw/harlan-claude-code | 65 | Nuxt/Vue/TypeScript personal agent kit by a prominent Nuxt community member. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |

**Priority: HIGH.** This is the largest single gap. Install `vuejs-ai/skills` first.

### 4.2 .NET Diagnostics / Profiling / Performance

| Marketplace | URL | Est. Reputation | Rationale |
|---|---|---|---|
| `dotnet-diag-skills` *(to be created or sourced)* | TBD | — | No existing marketplace found wrapping `dotnet-dump`, `dotnet-counters`, `dotnet-gcdump`, `dotnet-trace`, or PerfView. **Recommend authoring** rather than installing. Wrap the `Microsoft.Diagnostics.NETCore.Client` tooling as Claude Code skills. |
| `dotnet-skills` (already installed) | https://github.com/Aaronontheweb/dotnet-skills | 80 | Already in catalog but underutilized. Contains `dotnet-diag` plugin. **No new install needed — activate existing coverage.** |

**Priority: MEDIUM.** The `dotnet-diag` plugin inside the already-installed `dotnet-skills` marketplace provides the foundation. A dedicated marketplace would be ideal but does not yet exist publicly.

### 4.3 Multi-Agent Orchestration / Parallel Execution

| Marketplace | URL | Est. Reputation | Rationale |
|---|---|---|---|
| `wshobson/agents` | https://github.com/wshobson/agents | 78 | 33K★. Multi-agent orchestration with 97+ specialized agents and a 6-phase protocol. The same author as `claude-code-workflows` (already installed). Source: community; Maintenance: active; Adoption: popular; Docs: good; Eval: partial |
| `markus41/claude` | https://github.com/markus41/claude | 62 | Enterprise multi-agent orchestration with 27 plugins. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |
| `ananddtyagi/cc-marketplace` | https://github.com/ananddtyagi/cc-marketplace | 55 | 673★. 119 plugins, general marketplace with orchestration coverage. Source: community; Maintenance: active; Adoption: niche; Docs: minimal; Eval: untested |

**Priority: HIGH.** The user's routing tables already describe three orchestration modes (full orchestration, near-safe parallel, single-thread with gates) but there is no installed capability that executes these patterns. `wshobson/agents` is the best fit.

### 4.4 Security Pentesting / Reverse Engineering

| Marketplace | URL | Est. Reputation | Rationale |
|---|---|---|---|
| `Eyadkelleh/awesome-claude-skills-security` | https://github.com/Eyadkelleh/awesome-claude-skills-security | 72 | Security testing toolkit with curated SecLists wordlists and injection payloads. For authorized pentesting, CTFs, bug bounties. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |
| `tanweai/wooyun-legacy` | https://github.com/tanweai/wooyun-legacy | 68 | Security plugins by Tanwe Security Lab (1.8K★). Broader coverage than just pentest. Source: community; Maintenance: active; Adoption: niche; Docs: minimal; Eval: untested |
| `AgentSecOps/SecOpsAgentKit` | https://github.com/AgentSecOps/SecOpsAgentKit | 58 | Security operations toolkit for AI coding agents. Container scanning, secret detection, vulnerability identification. Source: community; Maintenance: active; Adoption: niche; Docs: minimal; Eval: untested |
| `cyberkaida/reverse-engineering-assistant` | https://github.com/cyberkaida/reverse-engineering-assistant | 65 | AI-assisted binary analysis and RE with Ghidra integration. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |
| `HexRaysSA/ida-claude-plugins` | https://github.com/HexRaysSA/ida-claude-plugins | 70 | Official Hex-Rays marketplace for IDA Pro RE workflows. Source: partner (Hex-Rays is the IDA vendor); Maintenance: active; Adoption: niche; Docs: excellent; Eval: untested |
| `blacktop/ipsw-skill` | https://github.com/blacktop/ipsw-skill | 62 | Apple firmware and binary RE using the `ipsw` CLI. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |

**Priority: HIGH for security; HIGH for RE.** The user's CLAUDE.md explicitly flags both as gaps. Install `awesome-claude-skills-security` and `cyberkaida/reverse-engineering-assistant` first; add `ida-claude-plugins` if IDA Pro is available on the target machine.

### 4.5 TypeScript / Type-Level Programming

| Marketplace | URL | Est. Reputation | Rationale |
|---|---|---|---|
| `mattpocock/skills` | https://github.com/mattpocock/skills | 88 | Already installed but **empty in catalog**. Matt Pocock (Total TypeScript) — the definitive TypeScript skills collection. Source: community; Maintenance: active; Adoption: popular; Docs: excellent; Eval: tested |
| `TanStack/ai` | https://github.com/TanStack/ai | 68 | TanStack AI agent skills — type-safe, provider-agnostic TypeScript AI SDK patterns. Source: partner (TanStack org); Maintenance: active; Adoption: popular; Docs: good; Eval: untested |
| `guillempuche/ai-standards` | https://github.com/guillempuche/ai-standards | 55 | TypeScript + Effect + React + local-first patterns. Source: community; Maintenance: active; Adoption: niche; Docs: good; Eval: untested |

**Priority: HIGH for `mattpocock/skills`** — the marketplace is already installed; the catalog refresh is not picking up its entries. This is a **bug in `refresh_catalog.py`** or the marketplace metadata, not a true gap.

---

## 5. Wishlist Removals / Downgrades

### 5.1 Remove (empty / zero-value)

| Marketplace | Reason |
|---|---|
| `life-sciences` | 0 plugins, 0 skills, 0 agents. Completely empty. |
| `knowledge-work-plugins` | 0 plugins, 0 skills, 0 agents. Completely empty. |
| `impeccable` | 0 plugins, 0 skills, 0 agents. Completely empty. |
| `token-optimizer` | 0 plugins, 0 skills, 0 agents. Completely empty. |

**Action:** Remove from wishlist and uninstall from Claude Code to reduce registry noise.

### 5.2 Downgrade (low reputation / narrow scope)

| Marketplace | Current | Recommended | Reason |
|---|---|---|---|
| `pixelbin-claude-skill` | Not in wishlist | Exclude | Single-skill marketplace (1 image-optimization skill). Low value-per-install. |
| `super-board` | Not in wishlist | Exclude | 8 skills for GitHub Project board automation. Very narrow scope. |
| `healthcare` | Not in wishlist | Exclude | 1 plugin, 10 skills. Clinical decision support and HIPAA compliance — far outside the dev build-phase routing scope. |
| `compound-knowledge-plugin` | Not in wishlist | Exclude | 1 plugin, 6 skills. Knowledge management — not dev build-phase. |
| `rampstack` | Not in wishlist | Review | 107 skills covering "the website lifecycle." Assess whether these are high-quality or generic. |

### 5.3 Redundant within awesome-claude-code-plugins

The `awesome-claude-code-plugins` marketplace (195 plugins) contains duplicates of capabilities available in higher-reputation marketplaces:

| Plugin in `awesome-claude-code-plugins` | Canonical version in |
|---|---|
| `docx` | `anthropic-agent-skills` |
| `xlsx` | `anthropic-agent-skills` |
| `pptx` | `anthropic-agent-skills` |
| `pdf` | `anthropic-agent-skills` |
| `security-guidance` | `claude-plugins-official` |
| `pr-review-toolkit` | `claude-plugins-official` |

**Action:** These are not separate marketplaces, so removal is not applicable. Instead, add a **deduplication rule** to `recommend.py` that prefers the higher-reputation source when multiple marketplaces provide the same capability.

---

## 6. Missing Capability Types (Taxonomy Gaps)

The current taxonomy organizes by domain (web-frontend, security, etc.) and type (Skill/Command/Agent). The following **capability archetypes** are missing from the taxonomy entirely:

### 6.1 Workflow Orchestrator

**What it is:** A skill that governs multi-step, multi-agent workflows — decides when to fan out, when to gate, when to merge.

**Current state:** The routing tables in SKILL.md describe three orchestration modes but there is no installed skill that *enforces* or *guides* this. The `conductor-orchestrator` and `orchestrator` agents exist but are black boxes.

**Recommended taxonomy addition:**
```
workflow-orchestrator   — governs multi-agent fan-out/fan-in with safety gates
```

### 6.2 Debug Session Manager

**What it is:** A skill that wraps a debugging session — captures state, manages breakpoints across files, correlates logs with source, and produces a structured root-cause analysis.

**Current state:** `debugging-toolkit` and `bug-detective` exist as general debugging aids. But there is no skill that manages a *session* — correlating multiple debug runs, maintaining state across context compaction, or integrating with an external debugger (WinDbg, GDB, VS Debugger).

**Recommended taxonomy addition:**
```
debug-session-manager   — structured debugging across multiple runs / context windows
```

### 6.3 Performance Profiler

**What it is:** A skill that wraps a specific profiling tool (dotTrace, PerfView, Chrome DevTools Performance tab, py-spy) and interprets the output.

**Current state:** `build-perf-baseline` and `build-perf-diagnostics` exist for .NET build performance. `react-performance` exists for React rendering. But there is no general-purpose profiler skill.

**Recommended taxonomy addition:**
```
performance-profiler   — wraps a specific profiling tool and interprets output
```

### 6.4 Parallel-Split Safety Governor

**What it is:** A skill that evaluates whether a task can be safely parallelized — checks for shared file dependencies, conflicting edits, and resource contention before allowing fan-out.

**Current state:** Mentioned in SKILL.md's routing tables but not implemented as an installed capability.

**Recommended taxonomy addition:**
```
parallel-safety-governor   — evaluates split safety before allowing parallel execution
```

### 6.5 Capability Deduplicator

**What it is:** Not a user-facing skill — a meta-capability within `recommend.py` that detects when multiple marketplaces provide the same capability and prefers the higher-reputation source.

**Current state:** Does not exist. The catalog has multiple `docx`, `pdf`, `xlsx` entries from different marketplaces.

**Recommended taxonomy addition:**
```
capability-dedup   — meta-rule in recommend.py for source preference
```

### 6.6 Marketplace Health Monitor

**What it is:** A scheduled command that checks whether installed marketplaces have new versions, security advisories, or have been archived.

**Current state:** Does not exist. Marketplaces are installed and forgotten.

**Recommended taxonomy addition:**
```
marketplace-health   — scheduled audit of marketplace freshness and security
```

---

## 7. Summary Table

| Gap | Severity | Action | Marketplace to Install/Create |
|---|---|---|---|
| Vue/Nuxt/Pinia/Vite | **Critical** | Install | `vuejs-ai/skills`, `onmax/nuxt-skills` |
| Reverse engineering | **Critical** | Install | `cyberkaida/reverse-engineering-assistant`, `HexRaysSA/ida-claude-plugins` |
| Security pentest | **Critical** | Install | `Eyadkelleh/awesome-claude-skills-security` |
| TypeScript type-level | **High** | Fix catalog bug | `mattpocock/skills` (already installed, 0 entries) |
| .NET diagnostics | **High** | Author new | Custom `dotnet-diag-skills` marketplace |
| Multi-agent orchestration | **High** | Install | `wshobson/agents` |
| Workflow orchestrator skill | **Medium** | Author new | Add to SKILL.md routing tables |
| Debug session manager | **Medium** | Author new | New skill in router repo |
| Performance profiler | **Medium** | Author new | New skill wrapping dotTrace/PerfView |
| Capability dedup | **Low** | Update recommend.py | Meta-rule in ranking engine |
| Empty marketplaces (4) | **Low** | Uninstall | `life-sciences`, `knowledge-work-plugins`, `impeccable`, `token-optimizer` |
| Document skill duplicates | **Low** | Update recommend.py | Deduplication rule |

---

## 8. Recommended wishlist.md Changes

### Additions (9 entries)

```markdown
### `vuejs-ai/skills`
- **URL**: https://github.com/vuejs-ai/skills
- **Source**: community · **Maintenance**: active · **Adoption**: official
- **Docs**: good · **Eval**: untested
- **Reputation**: 75
- **Domains**: web-frontend, vue, nuxt, pinia, vite, typescript
- **Notable plugins**: vue-skills
- **When to recommend**: Vue.js / Nuxt / Pinia / Vite project requirement

### `onmax/nuxt-skills`
- **URL**: https://github.com/onmax/nuxt-skills
- **Source**: community · **Maintenance**: active · **Adoption**: niche
- **Docs**: good · **Eval**: untested
- **Reputation**: 70
- **Domains**: web-frontend, nuxt, vue, fullstack
- **When to recommend**: Nuxt full-stack / NuxtHub deployment requirement

### `wshobson/agents`
- **URL**: https://github.com/wshobson/agents
- **Source**: community · **Maintenance**: active · **Adoption**: popular
- **Docs**: good · **Eval**: partial
- **Reputation**: 78
- **Domains**: orchestration, multi-agent, parallel-execution, workflow
- **When to recommend**: Multi-agent orchestration / parallel task execution

### `Eyadkelleh/awesome-claude-skills-security`
- **URL**: https://github.com/Eyadkelleh/awesome-claude-skills-security
- **Source**: community · **Maintenance**: active · **Adoption**: niche
- **Docs**: good · **Eval**: untested
- **Reputation**: 72
- **Domains**: security, pentest, ctf, injection, seclists
- **When to recommend**: Authorized pentest / CTF / security testing requirement

### `cyberkaida/reverse-engineering-assistant`
- **URL**: https://github.com/cyberkaida/reverse-engineering-assistant
- **Source**: community · **Maintenance**: active · **Adoption**: niche
- **Docs**: good · **Eval**: untested
- **Reputation**: 65
- **Domains**: reverse-engineering, ghidra, binary-analysis, decompile
- **When to recommend**: Reverse engineering / binary analysis requirement

### `HexRaysSA/ida-claude-plugins`
- **URL**: https://github.com/HexRaysSA/ida-claude-plugins
- **Source**: partner · **Maintenance**: active · **Adoption**: niche
- **Docs**: excellent · **Eval**: untested
- **Reputation**: 70
- **Domains**: reverse-engineering, ida-pro, disassembly
- **When to recommend**: IDA Pro reverse engineering requirement

### `blacktop/ipsw-skill`
- **URL**: https://github.com/blacktop/ipsw-skill
- **Source**: community · **Maintenance**: active · **Adoption**: niche
- **Docs**: good · **Eval**: untested
- **Reputation**: 62
- **Domains**: reverse-engineering, firmware, ios, binary-analysis
- **When to recommend**: Apple firmware / iOS binary analysis requirement

### `TanStack/ai`
- **URL**: https://github.com/TanStack/ai
- **Source**: partner · **Maintenance**: active · **Adoption**: popular
- **Docs**: good · **Eval**: untested
- **Reputation**: 68
- **Domains**: typescript, ai-sdk, type-safe, react
- **When to recommend**: TanStack AI SDK / type-safe TypeScript AI development

### `markus41/claude`
- **URL**: https://github.com/markus41/claude
- **Source**: community · **Maintenance**: active · **Adoption**: niche
- **Docs**: good · **Eval**: untested
- **Reputation**: 62
- **Domains**: orchestration, enterprise, multi-agent, workflow
- **When to recommend**: Enterprise multi-agent orchestration requirement
```

### Removals (4 entries)

Remove entirely from wishlist (and uninstall from Claude Code):
- `life-sciences`
- `knowledge-work-plugins`
- `impeccable`
- `token-optimizer`

### Downgrades (2 entries)

| Marketplace | From | To | Reason |
|---|---|---|---|
| `healthcare` | Review for inclusion | Exclude | 10 skills, all clinical/HIPAA — outside dev build-phase scope |
| `super-board` | Review for inclusion | Exclude | 8 skills for GitHub board automation — too narrow |

---

*Report generated from live catalog analysis of `catalog.md` (3091 lines, 1946 parsed capabilities) and marketplace metadata on disk.*
