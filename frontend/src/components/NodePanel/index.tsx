/**
 * Left-side node palette — Supabase-style with 3 view modes:
 *   • expanded  (default 220px) — full list with section labels
 *   • icon      (52px)         — icon-only rail with tooltip on hover
 *   • hidden    (0px)          — panel fully collapsed; reopened from
 *                                a floating edge handle on the canvas
 *
 * Mode is local component state — Zustand-persisted width is reused
 * but only matters in the expanded mode.
 */
import { useMemo, useRef, useState, type DragEvent } from 'react'
import { Check, RefreshCw, Search, ChevronDown, Plus, Sidebar, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { getNodeDisplayName, UNKNOWN_NODE_UI, useNodeRegistryStore, type NodeType } from '../../nodes'
import { useWorkflowStore } from '../../store/workflowStore'
import { PALETTE_DND_MIME } from '../WorkflowCanvas'
import ResizeHandle from '../ResizeHandle'

type Category = {
  key: string
  label: string
  color: string
  types: NodeType[]
}

type PaletteMode = 'expanded' | 'icon' | 'hidden'

const NEXT_MODE: Record<PaletteMode, PaletteMode> = {
  expanded: 'icon',
  icon: 'hidden',
  hidden: 'expanded',
}

const MODE_ICON: Record<PaletteMode, typeof Sidebar> = {
  expanded: PanelLeftClose,
  icon: PanelLeftOpen,
  hidden: Sidebar,
}

const MODE_TITLE: Record<PaletteMode, string> = {
  expanded: 'Switch to icon-only',
  icon: 'Hide palette',
  hidden: 'Show palette',
}

export default function NodePanel() {
  const paletteWidth = useWorkflowStore((s) => s.paletteWidth)
  const setPaletteWidth = useWorkflowStore((s) => s.setPaletteWidth)
  const rootRef = useRef<HTMLDivElement>(null)
  const [query, setQuery] = useState('')
  const [collapsed, setCollapsed] = useState<Record<string, boolean>>({})
  const [mode, setMode] = useState<PaletteMode>('expanded')
  const nodeTypes = useNodeRegistryStore((s) => s.nodeTypes)
  const nodeUI = useNodeRegistryStore((s) => s.nodeUI)
  const paletteSections = useNodeRegistryStore((s) => s.paletteSections)
  const manifestError = useNodeRegistryStore((s) => s.error)
  const refreshNodeRegistry = useNodeRegistryStore((s) => s.refreshFromBackend)
  const registryLoading = useNodeRegistryStore((s) => s.loading)
  const lastLoadedAt = useNodeRegistryStore((s) => s.lastLoadedAt)
  const [syncFlash, setSyncFlash] = useState(false)

  async function handleRefreshNodes() {
    try {
      await refreshNodeRegistry()
      setSyncFlash(true)
      window.setTimeout(() => setSyncFlash(false), 1400)
    } catch {
      // Store keeps the previous manifest and exposes manifestError.
    }
  }

  const categories = useMemo((): Category[] => {
    return paletteSections
      .map((sec) => ({
        key: sec.id,
        label: sec.label,
        color: sec.color,
        types: [...nodeTypes]
          .filter((t) => nodeUI[t]?.paletteGroup === sec.id)
          .sort((a, b) => (nodeUI[a]?.paletteOrder ?? 0) - (nodeUI[b]?.paletteOrder ?? 0)),
      }))
      .filter((c) => c.types.length > 0)
  }, [nodeTypes, nodeUI, paletteSections])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return categories
    return categories
      .map((c) => ({
        ...c,
        types: c.types.filter(
          (t) =>
            t.toLowerCase().includes(q) ||
            getNodeDisplayName(t).toLowerCase().includes(q) ||
            (nodeUI[t]?.description ?? '').toLowerCase().includes(q),
        ),
      }))
      .filter((c) => c.types.length > 0)
  }, [categories, nodeUI, query])

  // Hidden mode renders only a tiny floating reopen handle on the canvas edge.
  if (mode === 'hidden') {
    return (
      <button
        type="button"
        onClick={() => setMode('expanded')}
        title="Show palette"
        aria-label="Show palette"
        className="shrink-0"
        style={{
          width: 14,
          height: '100%',
          background: 'var(--bg-1)',
          borderRight: '1px solid var(--border)',
          color: 'var(--text-3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          padding: 0,
        }}
        onMouseEnter={(e) => {
          ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'
          ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
        }}
        onMouseLeave={(e) => {
          ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-1)'
          ;(e.currentTarget as HTMLElement).style.color = 'var(--text-3)'
        }}
      >
        <Sidebar size={11} strokeWidth={2} />
      </button>
    )
  }

  const isIcon = mode === 'icon'
  const width = isIcon ? 52 : paletteWidth
  const ModeIcon = MODE_ICON[mode]

  return (
    <div
      ref={rootRef}
      className="panel-glass flex flex-col h-full overflow-hidden relative shrink-0"
      style={{ width, borderRight: '1px solid var(--border)' }}
    >
      {/* Header */}
      <div
        className={`shrink-0 ${isIcon ? 'px-2 pt-3 pb-2' : 'px-3 pt-3 pb-2'}`}
        style={{ borderBottom: '1px solid var(--border-soft)' }}
      >
        <div className={`flex items-center ${isIcon ? 'flex-col gap-1' : 'gap-2'}`}>
          {!isIcon && (
            <>
              <span
                className="display"
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  letterSpacing: '0.14em',
                  textTransform: 'uppercase',
                  color: 'var(--text-2)',
                }}
              >
                Palette
              </span>
              <span
                className="font-mono"
                style={{
                  fontSize: 10,
                  color: 'var(--text-3)',
                  padding: '1px 6px',
                  borderRadius: 4,
                  background: 'var(--bg-3)',
                  border: '1px solid var(--border-soft)',
                }}
              >
                {nodeTypes.length}
              </span>
              <div className="flex-1" />
            </>
          )}
          <button
            onClick={() => setMode(NEXT_MODE[mode])}
            title={MODE_TITLE[mode]}
            aria-label={MODE_TITLE[mode]}
            className="flex items-center justify-center"
            style={{
              width: 22,
              height: 22,
              borderRadius: 5,
              background: 'transparent',
              color: 'var(--text-2)',
              border: '1px solid transparent',
              cursor: 'pointer',
              transition: 'background 140ms, color 140ms, border-color 140ms',
            }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLElement).style.color = 'var(--text-0)'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLElement).style.color = 'var(--text-2)'
              ;(e.currentTarget as HTMLElement).style.borderColor = 'transparent'
            }}
          >
            <ModeIcon size={12} strokeWidth={2} />
          </button>
          {!isIcon && (
            <button
              onClick={() => {
                void handleRefreshNodes()
              }}
              disabled={registryLoading}
              title={
                manifestError
                  ? 'Refresh node catalog failed; retry'
                  : lastLoadedAt
                    ? 'Node catalog synced. Refresh.'
                    : 'Refresh node catalog'
              }
              aria-label="Refresh node catalog"
              className="flex items-center justify-center"
              style={{
                width: 22,
                height: 22,
                borderRadius: 5,
                background: syncFlash
                  ? 'color-mix(in srgb, var(--success) 14%, transparent)'
                  : 'transparent',
                color: manifestError
                  ? 'var(--danger)'
                  : syncFlash
                    ? 'var(--success)'
                    : 'var(--text-2)',
                border: '1px solid transparent',
                cursor: registryLoading ? 'wait' : 'pointer',
                transition: 'background 180ms, color 180ms, border-color 180ms',
              }}
              onMouseEnter={(e) => {
                if (!syncFlash && !manifestError) (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'
              }}
              onMouseLeave={(e) => {
                if (!syncFlash && !manifestError) (e.currentTarget as HTMLElement).style.borderColor = 'transparent'
              }}
            >
              {syncFlash ? (
                <Check size={12} strokeWidth={2.4} />
              ) : (
                <RefreshCw
                  size={12}
                  strokeWidth={2}
                  className={registryLoading ? 'animate-spin' : undefined}
                />
              )}
            </button>
          )}
        </div>
        {!isIcon && manifestError && (
          <div className="mt-2" style={{ fontSize: 10, color: 'var(--text-3)' }}>
            Using generated node catalog.
          </div>
        )}
      </div>

      {/* Search (expanded only) */}
      {!isIcon && (
        <div className="px-3 pt-3 pb-2 shrink-0">
          <div
            className="flex items-center gap-2"
            style={{
              height: 30,
              padding: '0 10px',
              borderRadius: 6,
              background: 'var(--bg-2)',
              border: '1px solid var(--border-soft)',
              transition: 'border-color 140ms',
            }}
          >
            <Search size={12} strokeWidth={2} style={{ color: 'var(--text-3)' }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search nodes…"
              className="flex-1 bg-transparent outline-none min-w-0"
              style={{ fontSize: 12, color: 'var(--text-0)' }}
            />
            {!query && (
              <span
                className="font-mono shrink-0"
                style={{
                  fontSize: 9.5,
                  color: 'var(--text-3)',
                  padding: '1px 5px',
                  borderRadius: 3,
                  background: 'var(--bg-3)',
                  border: '1px solid var(--border-soft)',
                  letterSpacing: '0.02em',
                }}
              >
                ⌘K
              </span>
            )}
          </div>
        </div>
      )}

      {/* Sections */}
      <div className={`flex-1 overflow-y-auto ${isIcon ? 'pt-2 pb-2' : 'pb-2'}`}>
        {isIcon
          ? (
            // Icon-only rail: flat list of node icons with section dividers.
            <div className="flex flex-col gap-0.5 items-center">
              {filtered.map((cat, idx) => (
                <div key={cat.key} className="flex flex-col items-center w-full">
                  {idx > 0 && (
                    <div
                      style={{
                        width: 22,
                        height: 1,
                        background: 'var(--border-soft)',
                        margin: '8px 0',
                      }}
                    />
                  )}
                  <span
                    aria-hidden
                    style={{
                      width: 4,
                      height: 4,
                      borderRadius: 999,
                      background: cat.color,
                      opacity: 0.85,
                      marginBottom: 4,
                    }}
                  />
                  {cat.types.map((type) => (
                    <NodeIconCard key={type} type={type} accent={cat.color} />
                  ))}
                </div>
              ))}
            </div>
          )
          : (
            filtered.map((cat) => {
              const isCollapsed = collapsed[cat.key] ?? false
              return (
                <div key={cat.key} style={{ paddingTop: 4 }}>
                  <button
                    type="button"
                    onClick={() => setCollapsed((s) => ({ ...s, [cat.key]: !isCollapsed }))}
                    className="flex items-center w-full"
                    style={{
                      padding: '6px 12px',
                      background: 'transparent',
                      border: 'none',
                      cursor: 'pointer',
                      gap: 8,
                      fontFamily: 'inherit',
                    }}
                    aria-expanded={!isCollapsed}
                  >
                    <ChevronDown
                      size={11}
                      strokeWidth={2.2}
                      style={{
                        color: 'var(--text-3)',
                        transition: 'transform 160ms var(--ease-out)',
                        transform: isCollapsed ? 'rotate(-90deg)' : 'rotate(0deg)',
                      }}
                    />
                    <span
                      className="display"
                      style={{
                        fontSize: 11,
                        fontWeight: 500,
                        letterSpacing: '0.06em',
                        textTransform: 'uppercase',
                        color: 'var(--text-2)',
                      }}
                    >
                      {cat.label}
                    </span>
                    <span
                      className="font-mono"
                      style={{
                        fontSize: 10,
                        color: 'var(--text-3)',
                        padding: '0 5px',
                        borderRadius: 3,
                        background: 'var(--bg-3)',
                        border: '1px solid var(--border-soft)',
                      }}
                    >
                      {cat.types.length}
                    </span>
                    <div className="flex-1" />
                    <Plus size={11} strokeWidth={2} style={{ color: 'var(--text-3)', opacity: 0.5 }} />
                  </button>
                  {!isCollapsed && (
                    <div className="px-2 pb-2" style={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {cat.types.map((type) => (
                        <NodeCard key={type} type={type} accent={cat.color} />
                      ))}
                    </div>
                  )}
                </div>
              )
            })
          )}
      </div>

      {/* Footer (hidden in icon mode) */}
      {!isIcon && (
        <div
          className="px-3 py-2.5 shrink-0"
          style={{ borderTop: '1px solid var(--border-soft)' }}
        >
          <div
            className="font-mono"
            style={{ fontSize: 9.5, color: 'var(--text-3)', lineHeight: 1.6, letterSpacing: '0.02em' }}
          >
            drag · double-click to add
          </div>
        </div>
      )}

      {!isIcon && (
        <ResizeHandle
          edge="right"
          ariaLabel="Resize node palette"
          onResize={(clientX) => {
            const left = rootRef.current?.getBoundingClientRect().left ?? 0
            setPaletteWidth(clientX - left)
          }}
        />
      )}
    </div>
  )
}

function NodeCard({ type, accent }: { type: NodeType; accent: string }) {
  const meta = useNodeRegistryStore((s) => s.nodeUI[type] ?? UNKNOWN_NODE_UI)
  const Icon = meta.Icon
  const addNode = useWorkflowStore((s) => s.addNode)
  const title = getNodeDisplayName(type)

  return (
    <div
      draggable
      onDragStart={(e: DragEvent<HTMLDivElement>) => {
        e.dataTransfer.setData(PALETTE_DND_MIME, type)
        e.dataTransfer.setData('text/plain', type)
        e.dataTransfer.effectAllowed = 'copyMove'
      }}
      onDoubleClick={() => addNode(type, { x: 200, y: 200 })}
      title={`${title} · ${meta.description ?? type}`}
      className="flex items-center gap-2.5 cursor-grab active:cursor-grabbing"
      style={{
        padding: '6px 9px',
        borderRadius: 5,
        background: 'transparent',
        border: '1px solid transparent',
        transition: 'border-color 120ms, background 120ms',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.background = 'var(--bg-2)'
        ;(e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border-soft)'
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLDivElement).style.background = 'transparent'
        ;(e.currentTarget as HTMLDivElement).style.borderColor = 'transparent'
      }}
    >
      {/* Tiny color dot — Supabase-style section identifier */}
      <span
        className="shrink-0"
        style={{
          width: 4,
          height: 4,
          borderRadius: 999,
          background: accent,
          opacity: 0.85,
        }}
      />
      <span
        className="items-center justify-center shrink-0"
        style={{
          color: 'var(--text-1)',
          display: 'inline-flex',
          width: 18,
          height: 18,
        }}
      >
        <Icon size={13} strokeWidth={1.85} />
      </span>
      <div
        className="flex-1 min-w-0 truncate"
        style={{
          fontSize: 12,
          fontWeight: 460,
          color: 'var(--text-0)',
          lineHeight: 1.25,
          letterSpacing: '-0.005em',
        }}
      >
        {title}
      </div>
    </div>
  )
}

function NodeIconCard({ type, accent }: { type: NodeType; accent: string }) {
  const meta = useNodeRegistryStore((s) => s.nodeUI[type] ?? UNKNOWN_NODE_UI)
  const Icon = meta.Icon
  const addNode = useWorkflowStore((s) => s.addNode)
  const title = getNodeDisplayName(type)
  return (
    <button
      type="button"
      draggable
      onDragStart={(e) => {
        e.dataTransfer.setData(PALETTE_DND_MIME, type)
        e.dataTransfer.setData('text/plain', type)
        e.dataTransfer.effectAllowed = 'copyMove'
      }}
      onDoubleClick={() => addNode(type, { x: 200, y: 200 })}
      title={title}
      aria-label={title}
      className="flex items-center justify-center cursor-grab active:cursor-grabbing"
      style={{
        width: 32,
        height: 32,
        margin: '1px 0',
        borderRadius: 6,
        background: 'transparent',
        border: '1px solid transparent',
        color: 'var(--text-1)',
        transition: 'background 120ms, color 120ms, border-color 120ms',
      }}
      onMouseEnter={(e) => {
        ;(e.currentTarget as HTMLElement).style.background = 'var(--bg-2)'
        ;(e.currentTarget as HTMLElement).style.borderColor = 'var(--border-soft)'
        ;(e.currentTarget as HTMLElement).style.color = accent
      }}
      onMouseLeave={(e) => {
        ;(e.currentTarget as HTMLElement).style.background = 'transparent'
        ;(e.currentTarget as HTMLElement).style.borderColor = 'transparent'
        ;(e.currentTarget as HTMLElement).style.color = 'var(--text-1)'
      }}
    >
      <Icon size={14} strokeWidth={1.85} />
    </button>
  )
}
