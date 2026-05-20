import { ArcIcon, Plus } from '../../icons/arc'
import { useWorkflowStore } from '../../store/workflowStore'

/** Shared top-left chrome offset — palette header row + canvas overlay align here. */
export const WORKFLOW_ADD_OFFSET = { top: 10, left: 10 } as const

type Props = {
  /** `icon` = square + only (default). `labeled` kept for rare call sites. */
  variant?: 'icon' | 'labeled'
  className?: string
  style?: React.CSSProperties
}

export default function NewWorkflowButton({ variant = 'icon', className, style }: Props) {
  const onNew = () => {
    window.dispatchEvent(new CustomEvent('sheep:request-new-workflow'))
    useWorkflowStore.getState().newBlankWorkflow()
  }

  const iconBtnStyle: React.CSSProperties = {
    width: 30,
    height: 30,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'var(--bg-2)',
    color: 'var(--text-2)',
    border: '1px solid var(--border-soft)',
    cursor: 'pointer',
    boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
    transition: 'background 200ms var(--ease-out), color 200ms var(--ease-out), border-color 200ms var(--ease-out)',
    ...style,
  }

  if (variant === 'icon') {
    return (
      <button
        type="button"
        onClick={onNew}
        title="New workflow"
        aria-label="New workflow"
        className={className}
        style={iconBtnStyle}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--bg-3)'
          e.currentTarget.style.color = 'var(--accent)'
          e.currentTarget.style.borderColor = 'var(--border)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'var(--bg-2)'
          e.currentTarget.style.color = 'var(--text-2)'
          e.currentTarget.style.borderColor = 'var(--border-soft)'
        }}
      >
        <ArcIcon icon={Plus} size={15} />
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={onNew}
      title="New workflow"
      aria-label="New workflow"
      className={`panel-glass flex items-center justify-center ${className ?? ''}`}
      style={{
        position: 'absolute',
        zIndex: 20,
        top: WORKFLOW_ADD_OFFSET.top,
        left: WORKFLOW_ADD_OFFSET.left,
        width: 30,
        height: 30,
        padding: 0,
        border: '1px solid var(--border-soft)',
        borderRadius: 8,
        cursor: 'pointer',
        background: 'var(--panel-glass-bg)',
        ...style,
      }}
    >
      <Plus size={15} strokeWidth={2} />
    </button>
  )
}
