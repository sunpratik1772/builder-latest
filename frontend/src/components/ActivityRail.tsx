/**
 * Narrow icon rail that controls the right-side work area.
 * Linear-style: a thin vertical bar with hairline indicators on the
 * active item — no purple fills, no AI-slop gradients.
 */
import { Settings2, Bot, Activity, FileOutput } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'

export default function ActivityRail() {
  const mode = useWorkflowStore((s) => s.rightPanelMode)
  const toggle = useWorkflowStore((s) => s.toggleRightPanelMode)

  return (
    <div
      className="panel-glass flex flex-col items-center py-3 gap-1 shrink-0"
      style={{
        width: 44,
        borderLeft: '1px solid var(--border)',
      }}
    >
      <RailButton
        icon={<Settings2 size={15} strokeWidth={1.7} />}
        active={mode === 'config'}
        onClick={() => toggle('config')}
        title="Inspector"
      />
      <RailButton
        icon={<Bot size={15} strokeWidth={1.7} />}
        active={mode === 'copilot'}
        onClick={() => toggle('copilot')}
        title="Copilot"
      />
      <RailButton
        icon={<Activity size={15} strokeWidth={1.7} />}
        active={mode === 'runlog'}
        onClick={() => toggle('runlog')}
        title="Run log"
      />
      <RailButton
        icon={<FileOutput size={15} strokeWidth={1.7} />}
        active={mode === 'output'}
        onClick={() => toggle('output')}
        title="Output"
      />
    </div>
  )
}

function RailButton({
  icon,
  active,
  onClick,
  title,
}: {
  icon: React.ReactNode
  active: boolean
  onClick: () => void
  title: string
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="relative flex items-center justify-center"
      style={{
        width: 32,
        height: 32,
        borderRadius: 7,
        background: active ? 'var(--bg-3)' : 'transparent',
        color: active ? 'var(--text-0)' : 'var(--text-3)',
        border: active ? '1px solid var(--border-strong)' : '1px solid transparent',
        cursor: 'pointer',
        transition:
          'background 140ms var(--ease-out), color 140ms var(--ease-out), border-color 140ms var(--ease-out)',
      }}
      onMouseEnter={(e) => {
        if (!active) (e.currentTarget as HTMLElement).style.color = 'var(--text-1)'
      }}
      onMouseLeave={(e) => {
        if (!active) (e.currentTarget as HTMLElement).style.color = 'var(--text-3)'
      }}
    >
      {icon}
      {active && (
        <span
          aria-hidden
          style={{
            position: 'absolute',
            left: -8,
            top: 6,
            bottom: 6,
            width: 2,
            borderRadius: 2,
            background: 'var(--accent)',
          }}
        />
      )}
    </button>
  )
}
