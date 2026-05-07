/**
 * Supabase-style vertical navigation sidebar.
 *
 * Three modes (toggled via the bottom radio):
 *   • expanded   — full 220px with text labels
 *   • collapsed  — 52px icon-only rail
 *   • hover      — 52px rail that expands to 220px on hover
 *
 * Each item routes the workspace: clicking "Templates" opens the
 * WorkflowDrawer, clicking "Agents" opens the Copilot panel, etc.
 * "Workflow" is the canvas and is always selected by default.
 */
import { useEffect, useState } from 'react'
import {
  LayoutGrid,
  LayoutTemplate,
  Boxes,
  Lightbulb,
  Database,
  Bot,
  Activity,
  Settings,
  ChevronsLeft,
  ChevronsRight,
  PanelLeft,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useWorkflowStore } from '../store/workflowStore'
import { useStudioSectionStore, type StudioSection } from '../store/studioSectionStore'

type NavMode = 'expanded' | 'collapsed' | 'hover'

const STORAGE_KEY = 'dbsherpa.leftnav.mode'

interface NavItem {
  id: string
  label: string
  icon: LucideIcon
  isActive: (state: NavState) => boolean
  onClick: () => void
  disabled?: boolean
}

interface NavState {
  rightPanelMode: string | null
  drawerOpen: boolean
  section: StudioSection
}

export default function LeftNav() {
  const setDrawerOpen = useWorkflowStore((s) => s.setWorkflowDrawerOpen)
  const drawerOpen = useWorkflowStore((s) => s.workflowDrawerOpen)
  const setRightPanelMode = useWorkflowStore((s) => s.setRightPanelMode)
  const rightPanelMode = useWorkflowStore((s) => s.rightPanelMode)
  const section = useStudioSectionStore((s) => s.section)
  const setSection = useStudioSectionStore((s) => s.setSection)

  const [mode, setMode] = useState<NavMode>(() => {
    if (typeof window === 'undefined') return 'expanded'
    const saved = window.localStorage.getItem(STORAGE_KEY) as NavMode | null
    return saved ?? 'expanded'
  })
  const [hovered, setHovered] = useState(false)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, mode)
    }
  }, [mode])

  const showLabels = mode === 'expanded' || (mode === 'hover' && hovered)
  const widthCollapsed = 52
  const widthExpanded = 216
  const width = mode === 'expanded' || (mode === 'hover' && hovered) ? widthExpanded : widthCollapsed

  // Closing all overlays returns to the canvas/workflow view.
  const goToCanvas = () => {
    setDrawerOpen(false)
    setSection(null)
    if (rightPanelMode === 'copilot') setRightPanelMode(null)
  }

  const items: NavItem[] = [
    {
      id: 'workflow',
      label: 'Workflow',
      icon: LayoutGrid,
      isActive: (s) => !s.drawerOpen && s.rightPanelMode !== 'copilot' && s.section === null,
      onClick: goToCanvas,
    },
    {
      id: 'templates',
      label: 'Templates',
      icon: LayoutTemplate,
      isActive: (s) => s.drawerOpen,
      onClick: () => {
        setSection(null)
        setDrawerOpen(true)
      },
    },
    {
      id: 'nodes',
      label: 'Node Library',
      icon: Boxes,
      isActive: (s) => s.section === 'nodes',
      onClick: () => {
        setDrawerOpen(false)
        setSection(section === 'nodes' ? null : 'nodes')
      },
    },
    {
      id: 'skills',
      label: 'Skills',
      icon: Lightbulb,
      isActive: (s) => s.section === 'skills',
      onClick: () => {
        setDrawerOpen(false)
        setSection(section === 'skills' ? null : 'skills')
      },
    },
    {
      id: 'data',
      label: 'Data Sources',
      icon: Database,
      isActive: (s) => s.section === 'data',
      onClick: () => {
        setDrawerOpen(false)
        setSection(section === 'data' ? null : 'data')
      },
    },
    {
      id: 'run-history',
      label: 'Run History',
      icon: Activity,
      isActive: (s) => s.section === 'run-history',
      onClick: () => {
        setDrawerOpen(false)
        setSection(section === 'run-history' ? null : 'run-history')
      },
    },
  ]

  const settingsItem: NavItem = {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    isActive: (s) => s.section === 'settings',
    onClick: () => {},
    disabled: true,
  }

  const navState: NavState = { rightPanelMode, drawerOpen, section }

  return (
    <aside
      className="panel-glass shrink-0 flex flex-col relative h-full"
      style={{
        width,
        borderRight: '1px solid var(--border)',
        transition: 'width 180ms var(--ease-out)',
        zIndex: mode === 'hover' && hovered ? 35 : 25,
      }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Brand */}
      <div
        className="shrink-0 flex items-center"
        style={{
          height: 52,
          padding: showLabels ? '0 14px' : '0',
          justifyContent: showLabels ? 'flex-start' : 'center',
          borderBottom: '1px solid var(--border-soft)',
          gap: 10,
        }}
      >
        <div
          className="flex items-center justify-center shrink-0"
          style={{
            width: 26,
            height: 26,
            borderRadius: 6,
            background: 'var(--bg-3)',
            border: '1px solid var(--border-strong)',
            color: 'var(--text-0)',
          }}
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none">
            <path
              d="M11.5 4.5 C11.5 3.4 10.6 2.5 9.5 2.5 H6.5 C5.4 2.5 4.5 3.4 4.5 4.5 V5 C4.5 6.1 5.4 7 6.5 7 H9.5 C10.6 7 11.5 7.9 11.5 9 V11.5 C11.5 12.6 10.6 13.5 9.5 13.5 H6.5 C5.4 13.5 4.5 12.6 4.5 11.5"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              fill="none"
            />
          </svg>
        </div>
        {showLabels && (
          <div className="flex items-baseline gap-2 min-w-0">
            <span
              className="display truncate"
              style={{
                fontSize: 13,
                fontWeight: 540,
                color: 'var(--text-0)',
                letterSpacing: '-0.018em',
              }}
            >
              dbSherpa
            </span>
            <span
              className="font-mono shrink-0"
              style={{
                fontSize: 9.5,
                color: 'var(--text-3)',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
              }}
            >
              studio
            </span>
          </div>
        )}
      </div>

      {/* Project selector (Linear-style condensed) */}
      {showLabels && (
        <div
          className="shrink-0 px-2.5 pt-3 pb-2"
          style={{ borderBottom: '1px solid var(--border-soft)' }}
        >
          <div
            className="flex items-center gap-2"
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              background: 'var(--bg-2)',
              border: '1px solid var(--border-soft)',
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: 999,
                background: 'var(--success)',
                boxShadow: '0 0 0 2px color-mix(in srgb, var(--success) 18%, transparent)',
              }}
            />
            <span
              className="display truncate flex-1 min-w-0"
              style={{ fontSize: 12, fontWeight: 500, color: 'var(--text-0)' }}
            >
              Workspace
            </span>
            <span
              className="font-mono shrink-0"
              style={{
                fontSize: 9,
                padding: '1px 5px',
                borderRadius: 3,
                background: 'var(--bg-3)',
                border: '1px solid var(--border-soft)',
                color: 'var(--text-3)',
                letterSpacing: '0.04em',
                textTransform: 'uppercase',
              }}
            >
              prod
            </span>
          </div>
        </div>
      )}

      {/* Items */}
      <nav className="flex-1 overflow-y-auto py-2 flex flex-col gap-0.5 px-1.5">
        {items.map((it) => (
          <NavRow key={it.id} item={it} showLabels={showLabels} state={navState} />
        ))}
        <div
          style={{
            height: 1,
            background: 'var(--border-soft)',
            margin: '8px 6px',
          }}
        />
        <NavRow item={settingsItem} showLabels={showLabels} state={navState} />
      </nav>

      {/* Sidebar control */}
      <div
        className="shrink-0"
        style={{
          padding: showLabels ? '10px' : '8px 4px',
          borderTop: '1px solid var(--border-soft)',
        }}
      >
        {showLabels ? (
          <div>
            <div
              className="font-mono"
              style={{
                fontSize: 9.5,
                color: 'var(--text-3)',
                letterSpacing: '0.10em',
                textTransform: 'uppercase',
                padding: '0 4px 6px',
              }}
            >
              Sidebar control
            </div>
            <div className="flex flex-col" style={{ gap: 1 }}>
              <ModeOption value="expanded" current={mode} onClick={() => setMode('expanded')}>
                Expanded
              </ModeOption>
              <ModeOption value="collapsed" current={mode} onClick={() => setMode('collapsed')}>
                Collapsed
              </ModeOption>
              <ModeOption value="hover" current={mode} onClick={() => setMode('hover')}>
                Expand on hover
              </ModeOption>
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() =>
              setMode((m) => (m === 'collapsed' ? 'expanded' : m === 'expanded' ? 'hover' : 'collapsed'))
            }
            title={
              mode === 'collapsed'
                ? 'Expand sidebar'
                : mode === 'expanded'
                  ? 'Switch to expand-on-hover'
                  : 'Collapse sidebar'
            }
            aria-label="Toggle sidebar mode"
            className="w-full flex items-center justify-center"
            style={{
              height: 30,
              borderRadius: 6,
              background: 'transparent',
              color: 'var(--text-3)',
              border: '1px solid transparent',
              cursor: 'pointer',
              transition: 'background 140ms, color 140ms, border-color 140ms',
            }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border-soft)'
              ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLElement).style.background = 'transparent'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'transparent'
              ;(e.currentTarget as HTMLElement).style.color = 'var(--text-3)'
            }}
          >
            {mode === 'collapsed' ? (
              <ChevronsRight size={13} strokeWidth={2} />
            ) : mode === 'hover' ? (
              <PanelLeft size={13} strokeWidth={2} />
            ) : (
              <ChevronsLeft size={13} strokeWidth={2} />
            )}
          </button>
        )}
      </div>
    </aside>
  )
}

function NavRow({
  item,
  showLabels,
  state,
}: {
  item: NavItem
  showLabels: boolean
  state: NavState
}) {
  const Icon = item.icon
  const active = item.isActive(state)
  return (
    <button
      type="button"
      onClick={item.onClick}
      disabled={item.disabled}
      title={item.disabled ? `${item.label} (coming soon)` : item.label}
      className="flex items-center w-full"
      style={{
        gap: 10,
        padding: showLabels ? '6px 10px' : '0',
        height: 32,
        borderRadius: 6,
        background: active ? 'var(--bg-3)' : 'transparent',
        border: active ? '1px solid var(--border-strong)' : '1px solid transparent',
        color: item.disabled ? 'var(--text-3)' : active ? 'var(--text-0)' : 'var(--text-1)',
        cursor: item.disabled ? 'not-allowed' : 'pointer',
        opacity: item.disabled ? 0.55 : 1,
        fontFamily: 'inherit',
        textAlign: 'left',
        justifyContent: showLabels ? 'flex-start' : 'center',
        transition:
          'background 120ms, color 120ms, border-color 120ms',
      }}
      onMouseEnter={(e) => {
        if (item.disabled || active) return
        ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'
        ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
      }}
      onMouseLeave={(e) => {
        if (item.disabled || active) return
        ;(e.currentTarget as HTMLElement).style.background = 'transparent'
        ;(e.currentTarget as HTMLElement).style.color = 'var(--text-1)'
      }}
    >
      <Icon size={15} strokeWidth={1.85} className="shrink-0" />
      {showLabels && (
        <span
          className="display truncate"
          style={{
            fontSize: 12.5,
            fontWeight: active ? 530 : 460,
            letterSpacing: '-0.005em',
          }}
        >
          {item.label}
        </span>
      )}
    </button>
  )
}

function ModeOption({
  value,
  current,
  onClick,
  children,
}: {
  value: NavMode
  current: NavMode
  onClick: () => void
  children: React.ReactNode
}) {
  const active = value === current
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex items-center w-full"
      style={{
        gap: 8,
        padding: '5px 8px',
        borderRadius: 5,
        background: active ? 'var(--bg-2)' : 'transparent',
        border: '1px solid transparent',
        color: active ? 'var(--text-0)' : 'var(--text-2)',
        cursor: 'pointer',
        fontFamily: 'inherit',
        textAlign: 'left',
        fontSize: 12,
        fontWeight: active ? 500 : 440,
        letterSpacing: '-0.005em',
        transition: 'background 120ms, color 120ms',
      }}
      onMouseEnter={(e) => {
        if (active) return
        ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
      }}
      onMouseLeave={(e) => {
        if (active) return
        ;(e.currentTarget as HTMLElement).style.color = 'var(--text-2)'
      }}
    >
      <span
        aria-hidden
        style={{
          width: 12,
          height: 12,
          borderRadius: 999,
          border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border-strong)'}`,
          background: 'transparent',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        {active && (
          <span
            style={{
              width: 5,
              height: 5,
              borderRadius: 999,
              background: 'var(--accent)',
            }}
          />
        )}
      </span>
      <span>{children}</span>
    </button>
  )
}
