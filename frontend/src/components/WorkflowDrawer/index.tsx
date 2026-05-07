/**
 * Workflows drawer — two separate lists so saved workflows and
 * Copilot-generated / in-progress drafts don't get mixed up.
 *
 *   SAVED   — explicitly named workflows (workflows/ on backend)
 *   DRAFTS  — auto-persisted workflows (drafts/ on backend). Promote to
 *             Saved via the Save-As button in the topbar.
 */
import { useEffect, useMemo, useState } from 'react'
import {
  X as XIcon,
  Search,
  FilePlus2,
  Workflow as WorkflowIcon,
  FileJson2,
  FileClock,
  Trash2,
  Loader2,
} from 'lucide-react'
import { useWorkflowStore } from '../../store/workflowStore'
import { api, type StoredWorkflow } from '../../services/api'

type DrawerTab = 'saved' | 'drafts'

export default function WorkflowDrawer() {
  const open = useWorkflowStore((s) => s.workflowDrawerOpen)
  const setOpen = useWorkflowStore((s) => s.setWorkflowDrawerOpen)
  const sourceFilename = useWorkflowStore((s) => s.sourceFilename)
  const sourceKind = useWorkflowStore((s) => s.sourceKind)
  const loadWorkflowFromFile = useWorkflowStore((s) => s.loadWorkflowFromFile)
  const loadDraftFromFile = useWorkflowStore((s) => s.loadDraftFromFile)
  const newBlankWorkflow = useWorkflowStore((s) => s.newBlankWorkflow)

  const [tab, setTab] = useState<DrawerTab>('saved')
  const [saved, setSaved] = useState<StoredWorkflow[] | null>(null)
  const [drafts, setDrafts] = useState<StoredWorkflow[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loadingFile, setLoadingFile] = useState<string | null>(null)
  const [deletingFile, setDeletingFile] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  // Refetch both lists every time the drawer opens so freshly generated
  // drafts and newly saved workflows appear immediately.
  useEffect(() => {
    if (!open) return
    let cancelled = false
    setError(null)
    setSaved(null)
    setDrafts(null)
    Promise.all([api.listWorkflows(), api.listDrafts()])
      .then(([sr, dr]) => {
        if (cancelled) return
        setSaved(sr.workflows)
        setDrafts(dr.drafts)
      })
      .catch((e) => {
        if (!cancelled) setError((e as Error).message)
      })
    return () => {
      cancelled = true
    }
  }, [open])

  // Esc closes
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, setOpen])

  const items = tab === 'saved' ? saved : drafts
  const filtered = useMemo(() => {
    if (!items) return null
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter(
      (w) =>
        w.name?.toLowerCase().includes(q) ||
        w.description?.toLowerCase().includes(q) ||
        w.filename.toLowerCase().includes(q),
    )
  }, [items, query])

  async function handleOpen(filename: string) {
    setLoadingFile(filename)
    try {
      const dag =
        tab === 'saved'
          ? await api.getWorkflow(filename)
          : await api.getDraft(filename)
      if (tab === 'saved') loadWorkflowFromFile(filename, dag)
      else loadDraftFromFile(filename, dag)
      setOpen(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoadingFile(null)
    }
  }

  async function handleDelete(filename: string) {
    const ok = window.confirm(
      tab === 'drafts'
        ? `Delete draft "${filename}"?`
        : `Delete saved workflow "${filename}"? This cannot be undone.`,
    )
    if (!ok) return
    setDeletingFile(filename)
    try {
      if (tab === 'saved') await api.deleteWorkflow(filename)
      else await api.deleteDraft(filename)
      if (tab === 'saved') {
        setSaved((prev) => prev?.filter((w) => w.filename !== filename) ?? null)
      } else {
        setDrafts((prev) => prev?.filter((w) => w.filename !== filename) ?? null)
      }
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setDeletingFile(null)
    }
  }

  function handleNew() {
    newBlankWorkflow()
    setOpen(false)
  }

  if (!open) return null

  const savedCount = saved?.length ?? null
  const draftsCount = drafts?.length ?? null

  return (
    <>
      <div className="drawer-backdrop" onClick={() => setOpen(false)} />
      <aside
        className="drawer panel-glass"
        role="dialog"
        aria-label="Stored workflows"
        style={{
          width: 360,
          borderRight: '1px solid var(--border-strong)',
          boxShadow: '12px 0 32px -16px rgba(0,0,0,.35)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-5"
          style={{ height: 52, borderBottom: '1px solid var(--border)' }}
        >
          <div className="flex items-center gap-2">
            <span 
              className="font-mono" 
              style={{ 
                fontSize: 10.5, 
                fontWeight: 600, 
                color: 'var(--text-0)',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
              }}
            >
              Templates
            </span>
          </div>
          <button
            onClick={() => setOpen(false)}
            aria-label="Close drawer"
            className="lift flex items-center justify-center"
            style={{
              width: 28, height: 28, borderRadius: 6,
              background: 'transparent',
              color: 'var(--text-3)',
              border: '1px solid transparent',
              transition: 'all 120ms',
            }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-2)'
              ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-soft)'
              ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-0)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
              ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'transparent'
              ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-3)'
            }}
          >
            <XIcon size={15} strokeWidth={2.5} />
          </button>
        </div>

        {/* New button + Search */}
        <div className="px-4 py-4" style={{ borderBottom: '1px solid var(--border-soft)' }}>
          <button
            onClick={handleNew}
            className="flex items-center justify-center gap-2 w-full"
            data-testid="new-workflow-btn"
            style={{
              padding: '9px 14px',
              borderRadius: 7,
              background: 'var(--bg-2)',
              color: 'var(--text-0)',
              border: '1px solid var(--border-strong)',
              fontSize: 13,
              fontWeight: 530,
              letterSpacing: '-0.01em',
              cursor: 'pointer',
              fontFamily: 'inherit',
              transition: 'all 140ms cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--text-0)'
              ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--bg-0)'
              ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--text-0)'
              ;(e.currentTarget as HTMLButtonElement).style.transform = 'translateY(-1px)'
            }}
            onMouseLeave={(e) => {
              ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-2)'
              ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-0)'
              ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)'
              ;(e.currentTarget as HTMLButtonElement).style.transform = 'translateY(0)'
            }}
          >
            <FilePlus2 size={14} strokeWidth={2.5} />
            <span>New workflow</span>
          </button>

          <div
            className="flex items-center gap-2.5 mt-3 px-3"
            style={{
              height: 34,
              borderRadius: 7,
              background: 'var(--bg-2)',
              border: '1px solid var(--border)',
              transition: 'border-color 140ms, background 140ms',
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-strong)'
              e.currentTarget.style.background = 'var(--bg-1)'
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.background = 'var(--bg-2)'
            }}
          >
            <Search size={13} strokeWidth={2} style={{ color: 'var(--text-3)', flexShrink: 0 }} />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search saved"
              className="flex-1 outline-none"
              style={{
                fontSize: 12.5,
                background: 'transparent',
                color: 'var(--text-0)',
                border: 'none',
                fontWeight: 400,
                letterSpacing: '-0.003em',
              }}
              spellCheck={false}
            />
          </div>
        </div>

        {/* Tabs: Saved | Drafts */}
        <div
          className="flex items-stretch shrink-0"
          style={{
            borderBottom: '1px solid var(--border-soft)',
            height: 38,
            background: 'var(--bg-0)',
          }}
        >
          <TabButton
            label="Saved"
            icon={<FileJson2 size={12} strokeWidth={2.5} />}
            active={tab === 'saved'}
            count={savedCount}
            onClick={() => setTab('saved')}
          />
          <TabButton
            label="Drafts"
            icon={<FileClock size={12} strokeWidth={2.5} />}
            active={tab === 'drafts'}
            count={draftsCount}
            onClick={() => setTab('drafts')}
          />
        </div>

        {/* List */}
        <div className="flex-1 overflow-y-auto px-3 py-2">
          {items === null && !error && (
            <div
              className="flex items-center justify-center gap-2 py-10"
              style={{ color: 'var(--text-2)', fontSize: 12 }}
            >
              <Loader2 size={13} className="animate-spin" strokeWidth={2} />
              Loading…
            </div>
          )}

          {error && (
            <div
              className="px-3 py-2 rounded"
              style={{
                background: 'color-mix(in srgb, var(--danger) 10%, transparent)',
                color: 'var(--danger)',
                border: '1px solid color-mix(in srgb, var(--danger) 35%, transparent)',
                fontSize: 11.5,
              }}
            >
              {error}
            </div>
          )}

          {filtered && filtered.length === 0 && (
            <div
              className="text-center py-10 px-4"
              style={{ color: 'var(--text-3)', fontSize: 12, lineHeight: 1.5 }}
            >
              {query
                ? `No ${tab} match your search.`
                : tab === 'saved'
                  ? 'No saved workflows yet. Build one, then use Save-as in the topbar.'
                  : 'No drafts yet. The Copilot and manual builds drop here automatically.'}
            </div>
          )}

          {filtered?.map((w) => {
            const active =
              w.filename === sourceFilename &&
              ((tab === 'saved' && sourceKind === 'saved') ||
                (tab === 'drafts' && sourceKind === 'draft'))
            const loading = w.filename === loadingFile
            const deleting = w.filename === deletingFile
            return (
              <DrawerItem
                key={w.filename}
                item={w}
                tab={tab}
                active={active}
                loading={loading}
                deleting={deleting}
                onOpen={() => handleOpen(w.filename)}
                onDelete={() => handleDelete(w.filename)}
              />
            )
          })}
        </div>

        {/* Footer hint */}
        <div
          className="px-4 py-2.5 flex items-center justify-between"
          style={{ 
            borderTop: '1px solid var(--border-soft)', 
            fontSize: 10.5, 
            color: 'var(--text-3)',
            fontWeight: 500,
          }}
        >
          <span className="font-mono" style={{ letterSpacing: '0.01em' }}>
            {tab === 'saved'
              ? saved
                ? `${saved.length} saved`
                : '—'
              : drafts
                ? `${drafts.length} draft${drafts.length === 1 ? '' : 's'}`
                : '—'}
          </span>
          <span className="font-mono" style={{ letterSpacing: '0.08em', fontSize: 10 }}>Esc · close</span>
        </div>
      </aside>
    </>
  )
}

function TabButton({
  label,
  icon,
  active,
  count,
  onClick,
}: {
  label: string
  icon: React.ReactNode
  active: boolean
  count: number | null
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className="flex-1 flex items-center justify-center gap-1.5"
      style={{
        background: active ? 'var(--bg-1)' : 'transparent',
        color: active ? 'var(--text-0)' : 'var(--text-2)',
        borderBottom: active ? '2px solid var(--accent)' : '2px solid transparent',
        fontSize: 11,
        fontWeight: 580,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        borderRight: '1px solid var(--border-soft)',
        cursor: 'pointer',
        fontFamily: 'inherit',
        transition: 'all 140ms',
      }}
      onMouseEnter={(e) => {
        if (!active) {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-0)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-2)'
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-2)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
        }
      }}
    >
      {icon}
      <span>{label}</span>
      {count != null && (
        <span
          className="font-mono"
          style={{
            fontSize: 10,
            color: active ? 'var(--text-1)' : 'var(--text-3)',
            background: active ? 'var(--bg-3)' : 'var(--bg-2)',
            border: `1px solid ${active ? 'var(--border)' : 'var(--border-soft)'}`,
            padding: '1px 6px',
            borderRadius: 999,
            letterSpacing: '0.02em',
            fontWeight: 500,
          }}
        >
          {count}
        </span>
      )}
    </button>
  )
}

function DrawerItem({
  item: w,
  tab,
  active,
  loading,
  deleting,
  onOpen,
  onDelete,
}: {
  item: StoredWorkflow
  tab: DrawerTab
  active: boolean
  loading: boolean
  deleting: boolean
  onOpen: () => void
  onDelete: () => void
}) {
  const Icon = tab === 'saved' ? FileJson2 : FileClock
  return (
    <div
      className="relative flex items-start gap-3 px-3 py-3 rounded-lg mb-1.5"
      data-testid={`workflow-item-${w.filename}`}
      style={{
        background: active ? 'var(--bg-2)' : 'transparent',
        border: active ? '1px solid var(--border-strong)' : '1px solid transparent',
        cursor: loading ? 'progress' : 'pointer',
        transition: 'all 140ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
      onClick={loading || deleting ? undefined : onOpen}
      onMouseEnter={(e) => {
        if (!active && !loading && !deleting) {
          ;(e.currentTarget as HTMLDivElement).style.background = 'var(--bg-2)'
          ;(e.currentTarget as HTMLDivElement).style.borderColor = 'var(--border)'
          ;(e.currentTarget as HTMLDivElement).style.transform = 'translateX(2px)'
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          ;(e.currentTarget as HTMLDivElement).style.background = 'transparent'
          ;(e.currentTarget as HTMLDivElement).style.borderColor = 'transparent'
          ;(e.currentTarget as HTMLDivElement).style.transform = 'translateX(0)'
        }
      }}
    >
      <Icon
        size={14}
        strokeWidth={2}
        style={{ marginTop: 2, color: active ? 'var(--text-0)' : 'var(--text-3)', flexShrink: 0 }}
      />

      <div className="flex-1 min-w-0">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <div
            className="truncate"
            style={{
              fontSize: 13,
              fontWeight: 530,
              color: 'var(--text-0)',
              letterSpacing: '-0.01em',
              lineHeight: 1.3,
            }}
          >
            {w.name || w.filename}
          </div>
          <span
            className="num shrink-0"
            style={{
              fontSize: 10,
              color: 'var(--text-3)',
              letterSpacing: '0.01em',
              fontWeight: 500,
            }}
          >
            {w.node_count}n
          </span>
        </div>
        {w.description && (
          <div
            style={{
              marginTop: 3,
              fontSize: 11.5,
              color: 'var(--text-2)',
              lineHeight: 1.5,
              letterSpacing: '-0.003em',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {w.description}
          </div>
        )}
        <div className="flex items-center justify-between" style={{ marginTop: 6 }}>
          <span
            className="font-mono truncate"
            style={{
              fontSize: 10,
              color: 'var(--text-3)',
              letterSpacing: '0.01em',
              flex: 1,
              minWidth: 0,
            }}
          >
            {w.filename}
          </span>
          {w.modified_ms != null && (
            <span
              className="font-mono shrink-0 ml-3"
              style={{ fontSize: 10, color: 'var(--text-3)', fontWeight: 500 }}
            >
              {relativeTime(w.modified_ms)}
            </span>
          )}
        </div>
      </div>

      <button
        onClick={(e) => {
          e.stopPropagation()
          onDelete()
        }}
        disabled={loading || deleting}
        aria-label="Delete"
        title="Delete"
        className="flex items-center justify-center rounded"
        style={{
          width: 24, height: 24,
          background: 'transparent',
          color: 'var(--text-3)',
          border: '1px solid transparent',
          opacity: 0,
          cursor: loading || deleting ? 'wait' : 'pointer',
          transition: 'all 140ms',
          flexShrink: 0,
        }}
        onMouseEnter={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--danger)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'color-mix(in srgb, var(--danger) 10%, transparent)'
          ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'color-mix(in srgb, var(--danger) 30%, transparent)'
          ;(e.currentTarget as HTMLButtonElement).style.opacity = '1'
        }}
        onMouseLeave={(e) => {
          ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-3)'
          ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
          ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'transparent'
          ;(e.currentTarget as HTMLButtonElement).style.opacity = '0'
        }}
        onMouseOver={(e) => {
          const parent = e.currentTarget.parentElement
          if (parent) {
            ;(e.currentTarget as HTMLButtonElement).style.opacity = '1'
          }
        }}
      >
        {deleting ? (
          <Loader2 size={12} strokeWidth={2.5} className="animate-spin" />
        ) : (
          <Trash2 size={12} strokeWidth={2.5} />
        )}
      </button>

      {loading && (
        <Loader2
          size={13}
          strokeWidth={2.5}
          className="animate-spin shrink-0"
          style={{ color: 'var(--accent)', marginTop: 2 }}
        />
      )}
    </div>
  )
}

function relativeTime(epochMs: number): string {
  const delta = Date.now() - epochMs
  if (delta < 60_000) return 'just now'
  if (delta < 3_600_000) return `${Math.floor(delta / 60_000)}m ago`
  if (delta < 86_400_000) return `${Math.floor(delta / 3_600_000)}h ago`
  const d = new Date(epochMs)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}
