export type SessionSummary = { name: string; state: string; step: string }

export type RunSummary = {
  dir: string
  title: string
  stage: string
  step: number
  total: number
  ask: string
  video: string
  shots: number
  sessions: SessionSummary[]
}

/** A build worker (video or note session) seen live through engine events. */
export type WorkerRun = {
  agentId: string
  role: 'video' | 'note'
  run: string
  status: 'running' | 'done' | 'failed'
  startedAt: number
  endedAt?: number
  contextTokens: number
  contextMax: number
}

declare module 'claude-code' {
  interface PluginState {
    'events-release': { runs: RunSummary[]; isHidden: boolean; workers: WorkerRun[]; now: number }
  }
}
