// Regenerates timeline.json from a run's events.jsonl: bun stories/fixtures/build.ts <events.jsonl>
import { readFileSync, writeFileSync } from 'node:fs'
import { parseJsonl } from '../../shared/utils/events'
import { buildTimeline } from '../../shared/utils/timeline'

const events = parseJsonl(readFileSync(process.argv[2]!, 'utf8'))
writeFileSync(new URL('./timeline.json', import.meta.url), JSON.stringify(buildTimeline(events), null, 1))
