/**
 * Slide-over content drawer used for Skills / Data Sources / Logs.
 *
 * Mirrors the behaviour of `WorkflowDrawer` (left-anchored, animated,
 * dismiss-on-backdrop) but with a generic header so each section can
 * supply its own title / subtitle and content.
 */
import type { ReactNode } from 'react'
import { X as XIcon } from 'lucide-react'

interface Props {
  open: boolean
  onClose: () => void
  title: string
  subtitle?: string
  badge?: string
  width?: number
  children: ReactNode
  toolbar?: ReactNode
}

export default function SectionDrawer({
  open,
  onClose,
  title,
  subtitle,
  badge,
  width = 720,
  children,
  toolbar,
}: Props) {
  if (!open) return null
  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <div
        className="drawer panel-glass flex flex-col"
        style={{
          width,
          maxWidth: '92vw',
          borderRight: '1px solid var(--border-strong)',
          boxShadow: '12px 0 32px -16px rgba(0,0,0,.35)',
        }}
      >
        {/* Header — mirrors WorkflowDrawer exactly: 48px tall, eyebrow,
            single accent icon if provided by the consumer via the title. */}
        <div
          className="shrink-0 flex items-center justify-between px-4"
          style={{
            height: 48,
            borderBottom: '1px solid var(--border)',
          }}
        >
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <div className="flex items-center gap-2 min-w-0">
              <span
                className="eyebrow"
                style={{ color: 'var(--text-0)' }}
              >
                {title}
              </span>
              {badge && (
                <span
                  className="num shrink-0"
                  style={{
                    fontSize: 10.5,
                    color: 'var(--text-2)',
                    background: 'var(--bg-0)',
                    border: '1px solid var(--border)',
                    padding: '1px 6px',
                    borderRadius: 999,
                  }}
                >
                  {badge}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {toolbar}
            <button
              type="button"
              onClick={onClose}
              aria-label="Close"
              className="lift flex items-center justify-center"
              style={{
                width: 26, height: 26, borderRadius: 6,
                background: 'transparent',
                color: 'var(--text-2)',
                border: '1px solid transparent',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => {
                ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'
                ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
              }}
              onMouseLeave={(e) => {
                ;(e.currentTarget as HTMLElement).style.background = 'transparent'
                ;(e.currentTarget as HTMLElement).style.color = 'var(--text-2)'
              }}
            >
              <XIcon size={14} strokeWidth={2} />
            </button>
          </div>
        </div>
        {subtitle && (
          <div
            className="shrink-0"
            style={{
              padding: '8px 16px',
              borderBottom: '1px solid var(--border-soft)',
              fontSize: 11.5,
              color: 'var(--text-2)',
              lineHeight: 1.5,
              background: 'var(--bg-0)',
            }}
          >
            {subtitle}
          </div>
        )}
        <div className="flex-1 min-h-0 overflow-y-auto">{children}</div>
      </div>
    </>
  )
}
