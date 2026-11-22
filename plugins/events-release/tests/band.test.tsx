import { expect, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'

import { clock, phaseBar, runOf, sessionLine, workerRole } from '../hooks/register'

const NOW = Date.parse('2026-11-22T12:00:00Z')
const ROOT = '/home/t/events-release-runs'

const status = (over: Record<string, unknown>) =>
  JSON.stringify({
    title: 'Coupon codes',
    slug: 'coupon-codes',
    updated: '2026-11-22T11:58:00+00:00',
    stage: 'capture',
    ask: '',
    video: 'yes',
    shots: 4,
    stages: { handoff: { state: 'todo' } },
    sessions: { video: { state: 'todo', step: '' }, note: { state: 'todo', step: '' } },
    ...over,
  })

const BAND = {
  plugin: 'events-release',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isCollapsed: false, isWorking: false, maxRows: 10, bodyColumns: 120, scroll: { offset: 0, bodyRows: 10 }, view: {} },
} as const

/** Answers the engine calls the mod makes, with a fake runs folder. */
const fakeFs = (on: Parameters<TestBody>[1], files: Record<string, string>) => {
  on('env.get', (_, e) => ({ value: e.name === 'HOME' ? '/home/t' : undefined }))
  on('clock.now', () => ({ value: NOW }))
  on('clock.every', () => ({ value: undefined }))
  on('command.register', () => ({ value: { command: 'release-progress' } }))
  on('ui.toast', () => ({ value: undefined }))
  on('fs.exists', (_, e) => ({ value: e.path === ROOT || e.path in files }))
  on('fs.list', () => ({
    value: Object.keys(files).map(f => ({ name: f.split('/').slice(-2)[0] ?? '', kind: 'dir', size: 0, mtimeMs: 0, isLink: false })),
  }))
  on('fs.read', (_, e) => ({ value: files[e.path] ?? '' }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
}

test('an active run shows its stage, sessions and what the author must do', async ($, on) => {
  fakeFs(on, {
    [`${ROOT}/2026-11-22-coupon-codes/status.json`]: status({
      stage: 'build',
      ask: 'Approve shots + story (checkpoint A)',
      sessions: { video: { state: 'doing', step: 'voice' }, note: { state: 'done', step: '' } },
    }),
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...BAND, surface })
    expect((await ui.find({ type: 'Text', text: 'Coupon codes' }))?.text).toBe('Coupon codes')
    if (surface === 'desktop') {
      expect(await ui.find({ type: 'Svg' })).toBeTruthy() // bars + labels drawn together
    } else {
      expect(await ui.find({ type: 'Text', text: /Prepare/ })).toBeTruthy()
      expect(await ui.find({ type: 'Text', text: /Ship/ })).toBeTruthy()
    }
    expect((await ui.find({ type: 'Text', text: /^Video/ }))?.text).toBe('Video working · voice')
    expect((await ui.find({ type: 'Text', text: /^Note/ }))?.text).toBe('Note done')
    expect(await ui.find({ type: 'Text', text: 'Your turn' })).toBeTruthy()
    expect((await ui.find({ type: 'Text', text: /Approve shots/ }))?.text).toBe('Approve shots + story (checkpoint A)')
    await ui.unmount()
  }
})

test('finished and stale runs leave the band to the engine', async ($, on) => {
  fakeFs(on, {
    [`${ROOT}/2026-11-01-old/status.json`]: status({ updated: '2026-11-01T10:00:00+00:00' }),
    [`${ROOT}/2026-11-22-done/status.json`]: status({ stage: 'done', stages: { handoff: { state: 'done' } } }),
  })
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>engine</Text>
  })
  await $.session.start({ cwd: '/', surface: 'terminal', isInteractive: true })

  const ui = await $.ui.mount({ ...BAND, surface: 'terminal' })
  expect((await ui.find({ type: 'Text' }))?.text).toBe('engine')
  await ui.unmount()
})

test('a run without video never shows a video chip', async ($, on) => {
  fakeFs(on, {
    [`${ROOT}/2026-11-22-coupon-codes/status.json`]: status({ video: 'no', stage: 'qa' }),
  })
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect(await ui.find({ type: 'Svg' })).toBeTruthy()
  expect(await ui.find({ type: 'Text', text: /^Video/ })).toBeFalsy()
  expect((await ui.find({ type: 'Text', text: /image/ }))?.text).toBe('4 images')
  await ui.unmount()
})


test('the phase bar colours done, current and remaining segments', async () => {
  const svg = phaseBar(3)
  expect((svg.match(/<rect/g) ?? []).length).toBe(5)
  expect((svg.match(/#7cc576/g) ?? []).length).toBe(6) // 3 done bars + 3 labels
  expect((svg.match(/#c9704f/g) ?? []).length).toBe(2) // current bar + its label
  // each label starts exactly where its bar starts
  const bars = [...svg.matchAll(/<rect x="([\d.]+)"/g)].map(m => m[1])
  const labels = [...svg.matchAll(/<text x="([\d.]+)"/g)].map(m => m[1])
  expect(labels).toEqual(bars)
  expect(svg).toContain('>Review</text>')
})


test('worker prompts are recognised and tied to their run', () => {
  const prompt = 'Read /kit/workers/video-session.md and follow it.\nKIT=/kit\nRUN=/Users/x/events-release-runs/2026-11-22-coupon-codes'
  expect(workerRole(prompt)).toBe('video')
  expect(workerRole('Read /kit/workers/note-session.md')).toBe('note')
  expect(workerRole('Explore the repo')).toBe(null)
  expect(runOf(prompt)).toBe('2026-11-22-coupon-codes')
  expect(runOf('RUN=/a/b/2026-11-22-x/ next')).toBe('2026-11-22-x')
  expect(clock(75_000)).toBe('1:15')
})

test('the status line merges the run file with the live worker', () => {
  const base = { agentId: 'a1', role: 'video' as const, run: 'r', startedAt: 0, contextTokens: 82_000, contextMax: 200_000 }
  const doing = { name: 'video', state: 'doing', step: 'voice' }
  expect(sessionLine(doing, { ...base, status: 'running' }, 192_000)).toEqual({ text: 'Video working · voice · 3:12 · 41% context', state: 'doing' })
  // the worker started before it wrote its first status: still shown as working
  expect(sessionLine({ name: 'video', state: 'todo', step: '' }, { ...base, status: 'running' }, 5_000).state).toBe('doing')
  // a worker that died before finishing shows as stopped, in red
  expect(sessionLine(doing, { ...base, status: 'failed', endedAt: 60_000 }, 90_000)).toEqual({ text: 'Video stopped · voice · 1:00', state: 'blocked' })
  // done is done, whatever the worker's own turn said
  expect(sessionLine({ name: 'note', state: 'done', step: '' }, { ...base, role: 'note', status: 'done', endedAt: 110_000 }, 200_000).text).toBe('Note done · 1:50')
})

test('a spawned build worker shows live in the band', async ($, on) => {
  fakeFs(on, {
    [`${ROOT}/2026-11-22-coupon-codes/status.json`]: status({ stage: 'build', sessions: { video: { state: 'todo', step: '' }, note: { state: 'todo', step: '' } } }),
  })
  on('agent.spawn', () => ({ model: 'claude-opus-5-5', agentId: 'agent-video-1' }))
  await $.session.start({ cwd: '/', surface: 'desktop', isInteractive: true })
  await $.agent.spawn({
    tool_use_id: 't1',
    prompt: `Read /kit/workers/video-session.md and follow it.\nKIT=/kit\nRUN=${ROOT}/2026-11-22-coupon-codes`,
    description: 'Video worker',
    subagentType: 'general-purpose',
    parentModel: 'claude-opus-5-5',
  } as Parameters<typeof $.agent.spawn>[0])

  const ui = await $.ui.mount({ ...BAND, surface: 'desktop' })
  expect((await ui.find({ type: 'Text', text: /^Video/ }))?.text).toMatch(/^Video working · 0:00/)
  expect((await ui.find({ type: 'Text', text: /^Note/ }))?.text).toBe('Note waiting')
  await ui.unmount()
})
