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

declare module 'claude-code' {
  interface PluginState {
    'events-release': { runs: RunSummary[]; isHidden: boolean }
  }
}
