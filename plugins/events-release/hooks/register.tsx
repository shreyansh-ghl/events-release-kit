import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { RunSummary, SessionSummary } from '../types'

/**
 * Events release kit progress: reads ~/events-release-runs/<run>/status.json (written by the kit's run.py)
 * every few seconds and shows the active runs in a band above the prompt.
 */
const runs = atom({ plugin: 'events-release', key: 'runs' } as const, [] as RunSummary[])
const isHidden = atom({ plugin: 'events-release', key: 'isHidden' } as const, false)

const STAGES: [string, string][] = [
  ['preflight', 'Preflight'],
  ['read', 'Reading ClickUp + PRs'],
  ['interview', 'Interview'],
  ['northstar', 'Northstar check'],
  ['capture', 'Capture'],
  ['checkpoint_a', 'Checkpoint A'],
  ['build', 'Build'],
  ['qa', 'QA'],
  ['checkpoint_b', 'Checkpoint B'],
  ['post', 'Post'],
  ['handoff', 'Handoff'],
]
const POLL_MS = 4000
const FRESH_MS = 12 * 60 * 60 * 1000 // runs untouched for 12 h are treated as abandoned
const MAX_RUNS = 2
/** Dot colour per session state (theme keys, so light and dark themes both work). */
const DOT: Record<string, string> = { todo: 'subtle', doing: 'suggestion', done: 'success', blocked: 'error', skipped: 'subtle' }
/** Colours from the approved design (version B): bar fill and label per state. */
const BAR = { done: '#7cc576', current: '#c9704f', todo: 'rgba(136,135,128,0.35)' }
const LABEL = { done: '#7cc576', current: '#c9704f', todo: '#8f8d86' }

/**
 * The five-segment phase bar with each label drawn under its own segment, as one SVG so they always line up.
 * It scales to the band's width: at ~1100 px the bars are 9 px tall and the labels 13 px.
 */
export const phaseBar = (current: number): string => {
  const w = 1100
  const gap = 12
  const barH = 9
  const seg = (w - gap * (PHASES.length - 1)) / PHASES.length
  const parts = PHASES.map(([name], p) => {
    const state = p < current ? 'done' : p === current ? 'current' : 'todo'
    const x = (p * (seg + gap)).toFixed(1)
    const weight = p === current ? 600 : 400
    return (
      `<rect x="${x}" y="0" width="${seg.toFixed(1)}" height="${barH}" rx="${barH / 2}" fill="${BAR[state]}"/>` +
      `<text x="${x}" y="${barH + 22}" fill="${LABEL[state]}" font-size="14" font-weight="${weight}" ` +
      `font-family="-apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif">${name}</text>`
    )
  }).join('')
  const h = barH + 28
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">${parts}</svg>`
}

/** Amber tint behind "Your turn" (desktop/mobile; translucent so it suits light and dark themes). */
const ASK_TINT = '#e3a33829'
/** The 11 kit stages grouped into the 5 phases the band shows. */
const PHASES: [string, string[]][] = [
  ['Prepare', ['preflight', 'read', 'interview', 'northstar']],
  ['Capture', ['capture', 'checkpoint_a']],
  ['Build', ['build', 'qa']],
  ['Review', ['checkpoint_b']],
  ['Ship', ['post', 'handoff']],
]
const STATE_LABEL: Record<string, string> = { todo: 'waiting', doing: 'working', done: 'done', blocked: 'blocked', skipped: 'skipped' }

type Status = {
  title?: string
  slug?: string
  updated?: string
  stage?: string
  ask?: string
  video?: string
  shots?: number
  stages?: Record<string, { state?: string }>
  sessions?: Record<string, { state?: string; step?: string }>
}

/** One run's status.json → what the band shows; null when the run is finished or stale. */
export const summarize = (dir: string, s: Status, now: number): RunSummary | null => {
  const updated = Date.parse(s.updated ?? '')
  const finished = s.stage === 'done' || s.stages?.handoff?.state === 'done'
  if (finished || Number.isNaN(updated) || now - updated > FRESH_MS) {
    return null
  }
  const index = STAGES.findIndex(([key]) => key === s.stage)
  const sessions: SessionSummary[] = Object.entries(s.sessions ?? {})
    .filter(([name]) => name !== 'video' || s.video !== 'no')
    .map(([name, v]) => ({ name, state: v.state ?? 'todo', step: v.step ?? '' }))
  return {
    dir,
    title: s.title || s.slug || dir,
    stage: STAGES[index]?.[1] ?? s.stage ?? '?',
    step: index + 1,
    total: STAGES.length,
    ask: s.ask ?? '',
    video: s.video ?? 'yes',
    shots: s.shots ?? 0,
    sessions,
  }
}

/** Last ask per run, so the toast fires once per new ask (resets on reload; the band itself stays). */
let lastAsks: Record<string, string> = {}

/** Reads every run's status.json, keeps the fresh unfinished ones, toasts new asks, stores the summaries. */
async function refresh($: EngineInterface): Promise<void> {
  const home = await $.env.get('HOME')
  const root = (await $.env.get('EVENTS_RELEASE_RUNS')) || `${home}/events-release-runs`
  if (!(await $.fs.exists(root))) {
    await update($, runs, () => [])
    return
  }
  const now = await $.clock.now()
  const found: { summary: RunSummary; updated: number }[] = []
  for (const entry of await $.fs.list(root)) {
    if (entry.kind !== 'dir') {
      continue
    }
    const file = `${root}/${entry.name}/status.json`
    if (!(await $.fs.exists(file))) {
      continue
    }
    let status: Status
    try {
      status = JSON.parse(await $.fs.read(file)) as Status
    } catch (err) {
      // run.py writes atomically, so a bad file is a real problem: say so once in the log and skip it
      $.ui.log(`events-release: cannot read ${file}: ${String(err)}`)
      continue
    }
    const summary = summarize(entry.name, status, now)
    if (summary) {
      found.push({ summary, updated: Date.parse(status.updated ?? '') })
    }
  }
  const next = found
    .sort((a, b) => b.updated - a.updated)
    .slice(0, MAX_RUNS)
    .map(f => f.summary)

  // tell the author once when a run starts waiting on them
  for (const run of next) {
    if (run.ask && lastAsks[run.dir] !== run.ask) {
      $.ui.toast(`Events release · ${run.title}: ${run.ask}`)
    }
  }
  lastAsks = Object.fromEntries(next.map(r => [r.dir, r.ask]))

  const before = await read($, runs)
  if (JSON.stringify(before) !== JSON.stringify(next)) {
    await update($, runs, () => next)
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'release-progress', description: 'Show the Events release progress band again' })
    const result = await next(e)
    await refresh($)
    $.clock.every(POLL_MS, () => refresh($))
    return result
  })

  on('command.run', { command: 'release-progress' }, async $ => {
    await update($, isHidden, () => false)
    await refresh($)
    const list = await read($, runs)
    return { text: list.length ? 'Events release band shown.' : 'No active Events release run.' }
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, runs)
    if (e.props.hasSurvey || list.length === 0 || (await read($, isHidden))) {
      return next(e)
    }
    const els = $.ui.resolve(e)
    const { Box, Button, Progress, Text } = els
    // desktop, VS Code and phones draw Svg; the terminal's table has it but draws nothing, so it gets Progress bars
    const Svg = e.surface !== 'terminal' && 'Svg' in els ? els.Svg : undefined
    const hide = () => update($, isHidden, () => true)
    const filled = e.surface === 'desktop' || e.surface === 'mobile' // terminals get an outline instead of a tint

    return (
      <Box flexDirection="column" gap={1}>
        {list.map((run, i) => {
          const key = STAGES[run.step - 1]?.[0] ?? ''
          const current = PHASES.findIndex(([, keys]) => keys.includes(key))
          const building = run.sessions.some(s => s.state !== 'todo')
          return (
            <Box key={run.dir} flexDirection="column" gap="sm">
              <Box justifyContent="space-between" alignItems="center">
                <Box gap={1} alignItems="center">
                  <Text size="caption" weight="semibold" color="claude">
                    EVENTS RELEASE
                  </Text>
                  <Text weight="semibold">{run.title}</Text>
                </Box>
                {i === 0 ? <Button key="hide" label="Hide" plain dimColor onPress={hide} /> : null}
              </Box>

              {Svg ? (
                <Svg source={phaseBar(current)} alt={`Phase ${current + 1} of ${PHASES.length}: ${PHASES[current]?.[0] ?? ''}`} />
              ) : (
                <Box gap={1}>
                  {PHASES.map(([name], p) => (
                    <Box key={name} flexGrow={1} width={0}>
                      <Progress label={name} value={p <= current ? 1 : 0} max={1} color={p < current ? 'success' : p === current ? 'claude' : 'subtle'} />
                    </Box>
                  ))}
                </Box>
              )}

              {building || run.shots ? (
                <Box gap="md" flexWrap="wrap" alignItems="center">
                  {building
                    ? run.sessions.map(s => (
                        <Box key={s.name} gap="xs" alignItems="center">
                          <Text size="footnote" color={DOT[s.state] ?? 'subtle'}>
                            ●
                          </Text>
                          <Text size="footnote" dimColor>
                            {s.name === 'video' ? 'Video' : 'Note'} {STATE_LABEL[s.state] ?? s.state}
                            {s.state === 'doing' && s.step ? ` · ${s.step}` : ''}
                          </Text>
                        </Box>
                      ))
                    : null}
                  {run.shots ? (
                    <Text size="footnote" dimColor>
                      {run.shots} image{run.shots === 1 ? '' : 's'}
                    </Text>
                  ) : null}
                </Box>
              ) : null}

              {run.ask ? (
                <Box
                  gap="sm"
                  paddingX="md"
                  paddingY="sm"
                  borderStyle="round"
                  {...(filled ? { backgroundColor: ASK_TINT, borderColor: ASK_TINT } : { borderColor: 'warning' })}
                >
                  <Text color="warning" weight="semibold">
                    Your turn
                  </Text>
                  <Text>{run.ask}</Text>
                </Box>
              ) : null}
            </Box>
          )
        })}
      </Box>
    )
  })
}
