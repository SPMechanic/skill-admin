export const meta = {
  name: 'skill-admin.marketplace-scout',
  description: 'Search external skill marketplaces, score candidates, and present a ranked recommendation with an install gate',
  phases: [
    { title: 'Search', detail: 'parallel search across skills.sh, GitHub, skillsdirectory.com' },
    { title: 'Score and filter', detail: 'deduplicate and rank candidates by source reputation, specificity, and public grade' },
    { title: 'Present with HITL gate', detail: 'user-facing summary and explicit y/n install question' },
  ],
}

const SEARCH_RESULT_SCHEMA = {
  type: 'object',
  properties: {
    source: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          url: { type: 'string' },
          description: { type: 'string' },
          public_grade: { type: 'string' },
        },
        required: ['name', 'url', 'description'],
      },
    },
  },
  required: ['source', 'candidates'],
}

const SCORED_SCHEMA = {
  type: 'object',
  properties: {
    ranked: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          source: { type: 'string' },
          url: { type: 'string' },
          score: { type: 'number' },
          reason: { type: 'string' },
          install_command: { type: 'string' },
        },
        required: ['name', 'source', 'url', 'score', 'reason', 'install_command'],
      },
    },
  },
  required: ['ranked'],
}

const PRESENT_SCHEMA = {
  type: 'object',
  properties: {
    prompt_text: { type: 'string' },
    recommended: { type: 'string' },
    candidates: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          source: { type: 'string' },
          score: { type: 'number' },
        },
        required: ['name', 'source', 'score'],
      },
    },
  },
  required: ['prompt_text', 'recommended', 'candidates'],
}

const query = (args && args.query) ? args.query : ''
if (!query) {
  throw new Error('marketplace-scout requires args.query')
}

phase('Search')
log(`Searching external marketplaces for: ${query}`)
const sources = ['skills.sh', 'GitHub', 'skillsdirectory.com']
const results = await parallel(
  sources.map((src) => () =>
    agent(
      `Search ${src} for Claude Code skills or plugins matching the query "${query}". Return candidate skills with name, URL, description, and any public grade/stars you can find.`,
      { phase: 'Search', schema: SEARCH_RESULT_SCHEMA }
    )
  )
)

const cleanResults = results.filter(Boolean)
if (cleanResults.length === 0) {
  log('No external results found')
  return { results: [], ranked: [], prompt_text: 'No external skills found.', recommended: '', candidates: [] }
}

phase('Score and filter')
log('Deduplicating and scoring candidates')
const scored = await agent(
  `Combine and score these candidate skills from multiple sources. Deduplicate by name. Score by source reputation, specificity to the query, recency, and any public grade/stars. Return the top 5 ranked candidates.\n\nResults:\n${JSON.stringify(cleanResults, null, 2)}`,
  { phase: 'Score and filter', schema: SCORED_SCHEMA }
)

phase('Present with HITL gate')
log('Preparing user-facing recommendation')
const present = await agent(
  `Produce a user-facing summary of the top ranked external skills with a single recommended choice and an explicit y/n install question. Be concise.\n\nRanked candidates:\n${JSON.stringify(scored, null, 2)}`,
  { phase: 'Present with HITL gate', schema: PRESENT_SCHEMA }
)

return { results: cleanResults, ranked: scored.ranked, prompt_text: present.prompt_text, recommended: present.recommended, candidates: present.candidates }
