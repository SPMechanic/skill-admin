export const meta = {
  name: 'skill-admin.bootstrap-project',
  description: 'Orchestrate project context extraction, installed-skill recommendation, and routing plan',
  phases: [
    { title: 'Extract context', detail: 'project-atlas style scan of the current repo' },
    { title: 'Recommend skills', detail: 'marketplace-optimizer style ranking against installed catalog' },
    { title: 'Resolve plan', detail: 'plugin-router style conflict resolution and next steps' },
  ],
}

const PROJECT_CONTEXT_SCHEMA = {
  type: 'object',
  properties: {
    project_type: { type: 'string' },
    languages: { type: 'array', items: { type: 'string' } },
    frameworks: { type: 'array', items: { type: 'string' } },
    key_files: { type: 'array', items: { type: 'string' } },
    entry_points: { type: 'array', items: { type: 'string' } },
    testing_setup: { type: 'string' },
    deployment_target: { type: 'string' },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
  },
  required: ['project_type', 'languages', 'frameworks', 'key_files', 'confidence'],
}

const SKILL_RECOMMENDATIONS_SCHEMA = {
  type: 'object',
  properties: {
    recommendations: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          skill_name: { type: 'string' },
          reason: { type: 'string' },
          install_if_missing: { type: 'boolean' },
        },
        required: ['skill_name', 'reason', 'install_if_missing'],
      },
    },
    coverage_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['recommendations', 'coverage_gaps'],
}

const ROUTING_PLAN_SCHEMA = {
  type: 'object',
  properties: {
    primary_skill: { type: 'string' },
    aliases: { type: 'array', items: { type: 'string' } },
    announcement_reason: { type: 'string' },
    hitl_prompt: { type: 'string' },
    next_steps: { type: 'array', items: { type: 'string' } },
  },
  required: ['primary_skill', 'announcement_reason', 'next_steps'],
}

phase('Extract context')
log('Reading project-atlas instructions and scanning the current project')
const context = await agent(
  'Act as project-atlas. Read skills/project-atlas/SKILL.md, then explore the current project and produce a structured context map. Focus on languages, frameworks, key files, entry points, test setup, deployment target, and overall confidence.',
  { phase: 'Extract context', schema: PROJECT_CONTEXT_SCHEMA }
)
if (!context) {
  throw new Error('bootstrap-project failed at phase "Extract context": agent returned null')
}

phase('Recommend skills')
log('Ranking installed skills against the project context')
const recs = await agent(
  `Act as marketplace-optimizer. Read skills/marketplace-optimizer/SKILL.md and skills/plugin-router/references/catalog-index.md. Given the project context below, recommend the best installed skills and flag coverage gaps. Do not install anything.\n\nProject context:\n${JSON.stringify(context, null, 2)}`,
  { phase: 'Recommend skills', schema: SKILL_RECOMMENDATIONS_SCHEMA }
)
if (!recs) {
  throw new Error('bootstrap-project failed at phase "Recommend skills": agent returned null')
}

phase('Resolve plan')
log('Applying plugin-router conflict-resolution rules')
const plan = await agent(
  `Act as plugin-router. Read skills/plugin-router/SKILL.md. Given the project context and skill recommendations below, choose the single primary skill/agent to handle the user's bootstrap request, list any aliases with a one-line "prefer X when …" clause, state the announcement reason (one of: exact-table-match, keyword-fallback, catalog-gap-fallback, user-specified), and produce a concise next-step plan. If multiple skills conflict, resolve using the dedup preference order.\n\nProject context:\n${JSON.stringify(context, null, 2)}\n\nRecommendations:\n${JSON.stringify(recs, null, 2)}`,
  { phase: 'Resolve plan', schema: ROUTING_PLAN_SCHEMA }
)
if (!plan) {
  throw new Error('bootstrap-project failed at phase "Resolve plan": agent returned null')
}

return { context, recs, plan }
