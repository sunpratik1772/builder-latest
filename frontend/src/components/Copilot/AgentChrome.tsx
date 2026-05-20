import { ArcIcon, Check, ChevronDown, ChevronRight } from '../../icons/arc'
import { SherpaMark } from '../SherpaMark'
import {
  stepKindFor,
  stepLabel,
  formatStepSeconds,
  STEP_KIND_COLOR,
  type StepKind,
} from './stepIcons'
import type { ThinkingStep } from './thinkingTypes'

export function AgentIcon({ live, size = 28 }: { live?: boolean; size?: number }) {
  const mark = Math.round(size * 0.62)
  return (
    <span
      className={`agent-icon shrink-0 ${live ? 'agent-icon--live' : ''}`}
      style={{ width: size, height: size }}
      aria-hidden
    >
      {live && <span className="agent-icon__ring" />}
      <SherpaMark size={mark} />
    </span>
  )
}

/** Orchestrator-style idle bars while waiting for first thinking step. */
export function AgentIdleWave() {
  return (
    <div className="agent-idle-wave" aria-label="Agent working" role="status">
      {[0, 1, 2, 3].map((i) => (
        <span key={i} className="agent-idle-wave__bar" />
      ))}
    </div>
  )
}

function TimelineDot({ kind, done, live }: { kind: StepKind; done: boolean; live: boolean }) {
  const color = STEP_KIND_COLOR[kind]
  if (done) {
    return (
      <span
        className="flex items-center justify-center shrink-0"
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          background: `color-mix(in srgb, ${color} 18%, var(--bg-3))`,
          border: `1px solid color-mix(in srgb, ${color} 40%, transparent)`,
          color: 'var(--success)',
        }}
      >
        <ArcIcon icon={Check} size={13} strokeWidth={2.5} />
      </span>
    )
  }
  return (
    <span
      className={`flex items-center justify-center shrink-0 ${live ? 'agent-step-icon--live' : ''}`}
      style={{
        width: 28,
        height: 28,
        borderRadius: 8,
        background: live
          ? `color-mix(in srgb, ${color} 22%, var(--bg-3))`
          : 'var(--bg-3)',
        border: `1px solid ${
          live ? `color-mix(in srgb, ${color} 50%, var(--border-soft))` : 'var(--border-soft)'
        }`,
      }}
    >
      {live && <span className="agent-step-icon__ring" aria-hidden />}
      <span
        className="cursor-timeline-dot"
        style={{ background: color }}
        aria-hidden
      />
    </span>
  )
}

interface AgentThinkingPanelProps {
  steps: ThinkingStep[]
  open: boolean
  isStreaming: boolean
  onToggle: () => void
}

export function AgentThinkingPanel({ steps, open, isStreaming, onToggle }: AgentThinkingPanelProps) {
  const totalSec = steps.reduce((sum, s) => sum + (s.durationSec ?? 0), 0)
  const activeIdx = isStreaming ? steps.findIndex((s) => !s.done) : -1
  const showIdle = isStreaming && steps.length === 0

  return (
    <div
      className={`rounded-xl overflow-hidden mb-2 ${isStreaming && showIdle ? 'agent-panel-shimmer' : ''}`}
      style={{
        background: 'var(--bg-2)',
        border: '1px solid var(--border-soft)',
        boxShadow: 'var(--cursor-elev-raised, 0 2px 12px rgba(0,0,0,0.04))',
      }}
    >
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center gap-2 px-2.5 py-2"
        style={{ background: 'transparent' }}
        title={`Workflow agent · ${steps.length} steps`}
        aria-label="Workflow agent steps"
        aria-expanded={open}
      >
        <AgentIcon live={isStreaming} size={28} />
        {isStreaming && steps.length === 0 ? (
          <AgentIdleWave />
        ) : isStreaming ? (
          <span
            className="num live-blink"
            style={{ color: 'var(--accent)', fontSize: 10, letterSpacing: '0.12em' }}
            aria-hidden
          >
            ···
          </span>
        ) : (
          <span className="num" style={{ color: 'var(--text-3)', fontSize: 10 }}>
            {totalSec > 0 ? formatStepSeconds(totalSec) : steps.length > 0 ? steps.length : '—'}
          </span>
        )}
        <span className="flex-1" />
        {open ? (
          <ArcIcon icon={ChevronDown} size={15} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
        ) : (
          <ArcIcon icon={ChevronRight} size={15} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
        )}
      </button>

      {open && steps.length > 0 && (
        <div
          className="px-2 pb-2.5 pt-1 flex flex-col gap-0.5 max-h-[220px] overflow-y-auto agent-timeline"
          style={{ borderTop: '1px solid var(--border-soft)' }}
        >
          {steps.map((step, i) => {
            const kind = stepKindFor(step.text)
            const isActive = i === activeIdx
            const dur =
              step.done && step.durationSec != null
                ? formatStepSeconds(step.durationSec)
                : isActive
                  ? '…'
                  : '—'
            const label = stepLabel(step.text)
            return (
              <div
                key={step.id}
                className="agent-step-row flex items-center gap-2 py-1 px-1 rounded-lg min-w-0"
                style={{
                  animationDelay: `${Math.min(i * 40, 200)}ms`,
                  background: isActive
                    ? 'color-mix(in srgb, var(--accent) 6%, transparent)'
                    : 'transparent',
                }}
              >
                <TimelineDot kind={kind} done={step.done} live={isActive} />
                <span
                  className="flex-1 min-w-0 truncate font-mono"
                  style={{
                    fontSize: 11,
                    lineHeight: 1.35,
                    color: step.done
                      ? 'var(--text-2)'
                      : isActive
                        ? 'var(--text-0)'
                        : 'var(--text-1)',
                  }}
                  title={step.text}
                >
                  {label}
                </span>
                <span
                  className="num shrink-0 tabular-nums"
                  style={{
                    fontSize: 10,
                    color: step.done ? 'var(--text-3)' : isActive ? 'var(--accent)' : 'var(--text-3)',
                    minWidth: 36,
                    textAlign: 'right',
                  }}
                >
                  {dur}
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
