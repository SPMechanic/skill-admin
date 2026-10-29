# Marketplace Wishlist & Reputation Index

Curated marketplaces for installation recommendations. Each entry includes
reputation signals used by the ranking engine to score fit for a project.

## Reputation signals

| Signal | Values | Weight |
|---|---|---|
| **Source** | `anthropic` / `partner` / `community` / `personal` | 30 |
| **Maintenance** | `active` / `stale` / `archived` | 20 |
| **Adoption** | `official` / `popular` / `niche` / `experimental` | 20 |
| **Docs** | `excellent` / `good` / `minimal` / `none` | 15 |
| **Eval coverage** | `tested` / `partial` / `untested` | 15 |

Score = weighted sum (0–100). Higher = more trusted for recommendation.

---

## Tier 1 — Anthropic Official (always recommend)

### `claude-plugins-official`
- **URL**: https://github.com/anthropics/claude-plugins
- **Source**: anthropic · **Maintenance**: active · **Adoption**: official · **Docs**: excellent · **Eval**: tested
- **Reputation**: 100
- **Domains**: code review, feature dev, commits, CLAUDE.md management, security, frontend design, LSP integrations, code simplification, modernization
- **Notable plugins**: `code-review`, `feature-dev`, `commit-commands`, `claude-md-management`, `claude-security`, `frontend-design`, `code-simplifier`, `code-modernization`, `hookify`, `explanatory-output-style`

### `anthropic-agent-skills`
- **URL**: https://github.com/anthropics/skills
- **Source**: anthropic · **Maintenance**: active · **Adoption**: official · **Docs**: excellent · **Eval**: tested
- **Reputation**: 100
- **Domains**: document creation (docx/xlsx/pptx/pdf), visual design, web testing, skill authoring, MCP building, Claude API reference
- **Notable skills**: `docx`, `xlsx`, `pptx`, `pdf`, `frontend-design`, `webapp-testing`, `skill-creator`, `mcp-builder`, `claude-api`, `web-artifacts-builder`

## Tier 2 — Partner / High-Reputation Community

### `claude-code-workflows` (Seth Hobson / wshobson)
- **URL**: https://github.com/wshobson/claude-code-workflows
- **Source**: community · **Maintenance**: active · **Adoption**: popular · **Docs**: excellent · **Eval**: partial
- **Reputation**: 85
- **Domains**: workflow orchestration, TDD, debugging, git/PR automation, backend dev, code refactoring, operating/deploy, full-stack
- **Notable plugins**: `full-stack-orchestration`, `tdd-workflows`, `debugging-toolkit`, `git-pr-workflows`, `backend-development`, `code-refactoring`, `unit-testing`, `operating-kit`

### `dotnet-agent-skills` (dotnet org)
- **URL**: https://github.com/dotnet/skills
- **Source**: partner · **Maintenance**: active · **Adoption**: official (Microsoft) · **Docs**: excellent · **Eval**: tested
- **Reputation**: 90
- **Domains**: .NET development, C#, ASP.NET, Azure, Blazor, MAUI, EF Core
- **Notable plugins**: `dotnet-cli`, `dotnet-test`, `dotnet-ef`, `aspnet-core`, `blazor`, `azure-dotnet`

### `dotnet-skills` (Aaronontheweb)
- **URL**: https://github.com/Aaronontheweb/dotnet-skills
- **Source**: community · **Maintenance**: active · **Adoption**: popular (Petabridge) · **Docs**: good · **Eval**: partial
- **Reputation**: 78
- **Domains**: .NET, Akka.NET, distributed systems, event sourcing
- **Notable plugins**: `akka-net`, `dotnet-solutions`, `distributed-systems`

## Tier 3 — Well-Scoped Community

### `compound-engineering-plugin`
- **URL**: https://github.com/EveryInc/compound-engineering-plugin
- **Source**: community · **Maintenance**: active · **Adoption**: niche · **Docs**: good · **Eval**: untested
- **Reputation**: 65
- **Domains**: brainstorm, plan, debug, review, compound learnings, knowledge management
- **Notable plugins**: `compound-engineering`

### `mattpocock`
- **URL**: https://github.com/mattpocock/claude-code-skills
- **Source**: community (Matt Pocock — Total TypeScript) · **Maintenance**: active · **Adoption**: popular (TypeScript community) · **Docs**: excellent · **Eval**: partial
- **Reputation**: 75
- **Domains**: TypeScript, React, Next.js, web development, type-level programming
- **Notable skills**: `typescript-tips`, `react-patterns`, `nextjs-app`, `type-level-programming`

### `claude-skills-plugin-marketplace`
- **URL**: https://github.com/echoleesong/claude-skills-plugin
- **Source**: community · **Maintenance**: active · **Adoption**: popular (Chinese dev community) · **Docs**: good · **Eval**: untested
- **Reputation**: 62
- **Domains**: academic paper writing, deep research, image generation, n8n automation, skill discovery, presentations
- **Notable skills**: `deep-research`, `find-skills`, `generate-image`, `academic-paper`, `n8n-*`, `md-to-pptx`

## Tier 4 — Domain-Specific / Specialized

### `context-engineering-kit`
- **URL**: https://github.com/anthropics/context-engineering-kit *(verify)*
- **Source**: community · **Maintenance**: active · **Adoption**: niche · **Docs**: good · **Eval**: untested
- **Reputation**: 58
- **Domains**: context window management, prompt engineering, token optimization

### `super-board`
- **URL**: https://github.com/obra/super-board *(verify)*
- **Source**: community (Jesse Vincent) · **Maintenance**: active · **Adoption**: niche · **Docs**: excellent · **Eval**: untested
- **Reputation**: 68
- **Domains**: autonomous GitHub Project pipelines, visual summaries, GitHub projects → Build/QA/Review/Done

### `token-optimizer`
- **URL**: *(verify)*
- **Source**: community · **Maintenance**: unknown · **Adoption**: niche · **Docs**: minimal · **Eval**: untested
- **Reputation**: 40
- **Domains**: token usage reduction, context pruning

### `impeccable` (Paul Bakaus)
- **URL**: https://github.com/pbakaus/impeccable
- **Source**: community · **Maintenance**: active · **Adoption**: popular (90k+ stars) · **Docs**: excellent · **Eval**: partial
- **Reputation**: 90
- **Domains**: UI/UX design, frontend craft, design audits, AI-design detection
- **Notable plugins**: `impeccable` (1 skill, 24 commands, 62 detector rules)
- **When to recommend**: Any UI/UX polish, design audit, or "make this look better" task

### `knowledge-work-plugins` (Anthropic)
- **URL**: https://github.com/anthropics/knowledge-work-plugins
- **Source**: anthropic · **Maintenance**: active · **Adoption**: official (33k+ stars) · **Docs**: excellent · **Eval**: tested
- **Reputation**: 95
- **Domains**: design, accessibility, UX copy, research synthesis, product management, sales, marketing, productivity
- **Notable plugins**: `design`, `accessibility`, `ux-copy`, `research-synthesis`, `product-management`, `marketing`, `sales`, `productivity`
- **When to recommend**: Knowledge-work roles; design + accessibility + UX copy + research synthesis in one marketplace

### `figma` (Figma / Anthropic)
- **URL**: https://claude.com/marketplace/plugins/figma
- **Source**: partner · **Maintenance**: active · **Adoption**: official (167k+ installs) · **Docs**: excellent · **Eval**: tested
- **Reputation**: 96
- **Domains**: Figma integration, design tokens, component extraction, design-to-code
- **Notable plugins**: `figma` (MCP-native integration)
- **When to recommend**: Projects with Figma files that need token/component extraction or pixel-perfect code translation

### `baoyu-design`
- **URL**: https://github.com/JimLiu/baoyu-design
- **Source**: community · **Maintenance**: active · **Adoption**: popular (4.4k+ stars) · **Docs**: good · **Eval**: partial
- **Reputation**: 78
- **Domains**: UI/UX design, mockups, prototypes, decks, landing pages
- **Notable plugins**: `baoyu-design` (portable Claude Design agent skill)
- **When to recommend**: Running Claude Design locally in Claude Code/Cursor for polished artifacts

### `refero_skill`
- **URL**: https://github.com/referodesign/refero_skill
- **Source**: community (Refero) · **Maintenance**: active · **Adoption**: niche (327 stars) · **Docs**: good · **Eval**: partial
- **Reputation**: 72
- **Domains**: research-first design, UI reference, 150K+ app screens via MCP
- **Notable plugins**: `refero-design` (skill + MCP)
- **When to recommend**: Competitive research or pattern-backed design decisions

### `claude2figma`
- **URL**: https://github.com/senlindesign/claude2figma
- **Source**: community · **Maintenance**: active · **Adoption**: niche (174 stars) · **Docs**: good · **Eval**: partial
- **Reputation**: 70
- **Domains**: Figma design-system compliance, token binding, component instances
- **Notable plugins**: `claude2figma` (4 skills, 3-step preflight)
- **When to recommend**: Enforcing design-system rules when writing to Figma

### `claude-design-skill`
- **URL**: https://github.com/jiji262/claude-design-skill
- **Source**: community · **Maintenance**: active · **Adoption**: niche (212 stars) · **Docs**: excellent · **Eval**: partial
- **Reputation**: 70
- **Domains**: HTML artifacts, landing pages, decks, prototypes, posters
- **Notable plugins**: `claude-design` (portable skill based on Claude.ai Design prompt)
- **When to recommend**: Need the Claude.ai Design system prompt as a portable Claude Code skill

### `LibreUIUX-Claude-Code`
- **URL**: https://github.com/Ormus-Solutions/LibreUIUX-Claude-Code
- **Source**: community · **Maintenance**: active · **Adoption**: niche (121 stars) · **Docs**: good · **Eval**: untested
- **Reputation**: 68
- **Domains**: UI/UX system, accessibility, frontend workflows, shadcn/ui, Tailwind
- **Notable plugins**: 71 plugins, 93 agents, 76 commands, 74 skills
- **When to recommend**: Broad UI/UX development with many prebuilt agents and commands

### `design-tokens`
- **URL**: https://github.com/gregorymm/design-tokens
- **Source**: community · **Maintenance**: active · **Adoption**: experimental (3 stars) · **Docs**: excellent · **Eval**: untested
- **Reputation**: 58
- **Domains**: Figma token extraction, W3C DTCG, CTI/Style Dictionary, token write-back
- **Notable plugins**: `design-tokens` (MCP + generated Figma plugin)
- **When to recommend**: Building a token pipeline from Figma variables to code

### `skema-skill`
- **URL**: https://github.com/Bil0000/skema-skill
- **Source**: community · **Maintenance**: active · **Adoption**: experimental (1 star) · **Docs**: good · **Eval**: untested
- **Reputation**: 55
- **Domains**: design system generation, brief → components → prototype → handoff
- **Notable plugins**: `skema` (single design skill)
- **When to recommend**: Quick end-to-end design system from a brief

### `claude-figma-kit`
- **URL**: https://github.com/tuannafed/claude-figma-kit
- **Source**: community · **Maintenance**: active · **Adoption**: experimental (0 stars) · **Docs**: good · **Eval**: untested
- **Reputation**: 52
- **Domains**: Figma design system generation, UI/UX pro-max engine
- **Notable plugins**: `claude-figma-kit` (slash commands + agents)
- **When to recommend**: Generating a complete Figma design system from a product description

---

## Not Yet Installed — Recommended for Specific Needs

### Security & Reverse Engineering

| Marketplace | URL | Reputation | Domains | When to recommend |
|---|---|---|---|---|
| `claude-security` (already in official) | — | 100 | Security scanning, secrets, supply chain | General security tasks |
| `rea` | https://github.com/morluto/rea | 75 | Reverse engineering, binary analysis, decompiler, MCP-native | RE tasks, binary analysis, firmware |
| `cyberkaida/reverse-engineering-assistant` | https://github.com/cyberkaida/reverse-engineering-assistant | 65 | Ghidra, disassembly, decompilation | RE projects |
| `HexRaysSA/ida-claude-plugins` | https://github.com/HexRaysSA/ida-claude-plugins | 70 | IDA Pro integration, binary diffing | IDA Pro workflows |
| `blacktop/ipsw-skill` | https://github.com/blacktop/ipsw-skill | 62 | iOS firmware analysis, IPSW parsing | iOS RE |
| `Eyadkelleh/awesome-claude-skills-security` | https://github.com/Eyadkelleh/awesome-claude-skills-security | 72 | Pentest, CTF, security tools | Pentest/CTF |
| `pstack-claude` | https://github.com/pstack/claude *(verify)* | 55 | Security research, pentest, binary analysis | RE/security projects |
| `ecc` | *(verify)* | 50 | Security, exploit dev, CTF | CTF/pentest only |
| `rampstack` | *(verify)* | 50 | Security tooling, automation | Security automation |

> **Gap filled**: `rea` (v6.8.0, MIT, MCP-native) covers binary RE via
> CLI + MCP server. For Ghidra/IDA-specific work, the cyberkaida and
> HexRaysSA plugins remain the best options.

### Low-Level / Systems

| Marketplace | URL | Reputation | Domains | When to recommend |
|---|---|---|---|---|
| `rampstack` | *(verify)* | 50 | Systems programming, Rust, C | Systems projects |
| `pstack-claude` | *(verify)* | 55 | Low-level, binary analysis | RE/firmware |
| `dotnet-agent-skills` | https://github.com/dotnet/skills | 90 | C#, .NET, ASP.NET | .NET systems |

> **Gap**: No dedicated marketplace for C/C++/Rust kernel/embedded work.
> Recommend `code-review` + `architect` agent as best-available.

### UI/UX Design

| Marketplace | URL | Reputation | Domains | When to recommend |
|---|---|---|---|---|
| `frontend-design` (official) | — | 100 | Visual design, UI direction | All design tasks |
| `knowledge-work-plugins` (official) | https://github.com/anthropics/knowledge-work-plugins | 95 | Design, accessibility, UX copy, research synthesis | Knowledge-work design tasks |
| `figma` (official plugin) | https://claude.com/marketplace/plugins/figma | 96 | Figma integration, design tokens, code translation | Figma-connected projects |
| `impeccable` | https://github.com/pbakaus/impeccable | 90 | UI/UX craft, polish, audits | UX refinement |
| `brand-guidelines` (official) | — | 100 | Brand identity, consistency | Brand work |
| `web-artifacts-builder` (official) | — | 100 | Complex UI artifacts | React/Tailwind/shadcn |
| `anthropic-agent-skills` | https://github.com/anthropics/skills | 100 | canvas-design, frontend-design, web-artifacts-builder | General design + artifacts |
| `baoyu-design` | https://github.com/JimLiu/baoyu-design | 78 | Local Claude Design engine, mockups, prototypes | Polished UI mockups, decks |
| `claude-design-skill` | https://github.com/jiji262/claude-design-skill | 70 | HTML artifacts, decks, landing pages | Portable design skill |
| `refero_skill` | https://github.com/referodesign/refero_skill | 72 | Research-first design, 150K screens via MCP | Research-backed design |
| `claude2figma` | https://github.com/senlindesign/claude2figma | 70 | Design-system compliance in Figma | Figma + design system |
| `LibreUIUX-Claude-Code` | https://github.com/Ormus-Solutions/LibreUIUX-Claude-Code | 68 | UI/UX system, accessibility, frontend | Broad UI/UX workflows |
| `design-system-plugin` | https://github.com/brettallred/design-system-plugin | 62 | Design system, brand, UI subagents | Design system builds |
| `design-tokens` | https://github.com/gregorymm/design-tokens | 58 | Figma token extraction (DTCG/CTI) | Token pipelines |
| `skema-skill` | https://github.com/Bil0000/skema-skill | 55 | Single design skill, brief → system → handoff | Quick design systems |
| `claude-figma-kit` | https://github.com/tuannafed/claude-figma-kit | 52 | Figma design system generation | Figma from product description |
| `hallmark` | https://github.com/Nutlope/hallmark | 85 | Anti-AI-slop UI craft, design review, polish | Catching AI-generated slop before shipping |
| `ui-ux-pro-max-skill` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill | 65 | UI/UX pro-max design patterns | Augmenting UI/UX design workflows |
| `kami` | https://github.com/tw93/kami | 72 | Document layout, PDF/PNG/PPTX export | Exporting polished documents from code |

---

## Adding a New Marketplace to the Wishlist

Append a new entry using this format:

```markdown
### `<marketplace-name>`
- **URL**: <github-url>
- **Source**: anthropic / partner / community / personal
- **Maintenance**: active / stale / archived
- **Adoption**: official / popular / niche / experimental
- **Docs**: excellent / good / minimal / none
- **Eval**: tested / partial / untested
- **Reputation**: <0-100 score>
- **Domains**: <comma-separated>
- **Notable plugins**: <list>
- **When to recommend**: <trigger condition>
```

The ranking engine reads this file when recommending installations.
