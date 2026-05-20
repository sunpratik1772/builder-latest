import { useEffect, useMemo, useState } from 'react'
import { ArcIcon, Check, Copy, FileCode2, Pencil, X } from '../../icons/arc'
import { useWorkflowStore } from '../../store/workflowStore'
import { api } from '../../services/api'
import type { Workflow } from '../../types'

type CodeFormat = 'json' | 'yaml'

export default function WorkflowCodeEditor() {
  const workflow = useWorkflowStore((s) => s.workflow)
  const setWorkflow = useWorkflowStore((s) => s.setWorkflow)
  const resetRun = useWorkflowStore((s) => s.resetRun)
  const [format, setFormat] = useState<CodeFormat>('json')
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const headerLabel = useMemo(() => (format === 'json' ? 'JSON' : 'YAML'), [format])

  useEffect(() => {
    let cancelled = false
    async function syncFromWorkflow() {
      if (!workflow) {
        if (!cancelled) {
          setContent('')
          setEditing(false)
          setError(null)
        }
        return
      }
      setLoading(true)
      setError(null)
      try {
        if (format === 'json') {
          if (!cancelled) setContent(JSON.stringify(workflow, null, 2))
        } else {
          const { content: yaml } = await api.workflowToYaml(workflow)
          if (!cancelled) setContent(yaml)
        }
      } catch (e) {
        if (!cancelled) setError((e as Error).message)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void syncFromWorkflow()
    return () => {
      cancelled = true
    }
  }, [workflow, format])

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(content)
    } catch {
      window.alert('Could not copy code to clipboard.')
    }
  }

  async function applyCodeChanges() {
    if (!workflow) return
    setSaving(true)
    setError(null)
    try {
      const nextWorkflow: Workflow =
        format === 'json'
          ? (JSON.parse(content) as Workflow)
          : (await api.workflowFromYaml(content)).workflow
      setWorkflow(nextWorkflow)
      resetRun()
      setEditing(false)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex-1 min-w-0 flex flex-col" style={{ background: 'transparent' }}>
      <div
        className="panel-glass flex items-center justify-between shrink-0"
        style={{ height: 44, borderBottom: '1px solid var(--border)', padding: '0 10px' }}
      >
        <div className="flex items-center gap-2">
          <ArcIcon icon={FileCode2} size={13} style={{ color: 'var(--text-2)' }} />
          <span className="font-mono" style={{ fontSize: 11.5, color: 'var(--text-2)' }}>
            {headerLabel} editor
          </span>
        </div>
        <div className="flex items-center gap-1">
          <FormatPill active={format === 'json'} onClick={() => setFormat('json')}>
            JSON
          </FormatPill>
          <FormatPill active={format === 'yaml'} onClick={() => setFormat('yaml')}>
            YAML
          </FormatPill>
          <IconButton title="Copy code" onClick={() => void handleCopy()} disabled={!content}>
            <ArcIcon icon={Copy} size={13} />
          </IconButton>
          {editing ? (
            <>
              <IconButton title="Save code changes" onClick={() => void applyCodeChanges()} disabled={saving}>
                <ArcIcon icon={Check} size={13} />
              </IconButton>
              <IconButton
                title="Cancel editing"
                onClick={() => {
                  setEditing(false)
                  setError(null)
                  if (workflow) {
                    if (format === 'json') setContent(JSON.stringify(workflow, null, 2))
                    else void api.workflowToYaml(workflow).then((resp) => setContent(resp.content)).catch(() => void 0)
                  }
                }}
                disabled={saving}
              >
                <X size={13} />
              </IconButton>
            </>
          ) : (
            <IconButton title="Edit code" onClick={() => setEditing(true)} disabled={!workflow || loading}>
              <ArcIcon icon={Pencil} size={13} />
            </IconButton>
          )}
        </div>
      </div>

      <div className="flex-1 min-h-0 p-3">
        <textarea
          value={loading ? 'Loading…' : content}
          onChange={(e) => setContent(e.target.value)}
          spellCheck={false}
          readOnly={!editing || loading}
          style={{
            width: '100%',
            height: '100%',
            resize: 'none',
            borderRadius: 10,
            border: '1px solid var(--border)',
            background: 'var(--bg-0)',
            color: 'var(--text-0)',
            padding: '12px 14px',
            fontSize: 12.5,
            lineHeight: 1.55,
            fontFamily: 'IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, monospace',
            opacity: loading ? 0.7 : 1,
            outline: 'none',
          }}
        />
        {error && (
          <div className="font-mono" style={{ marginTop: 8, fontSize: 11, color: 'var(--danger)' }}>
            {error}
          </div>
        )}
      </div>
    </div>
  )
}

function FormatPill({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="font-mono"
      style={{
        height: 24,
        padding: '0 8px',
        borderRadius: 6,
        border: `1px solid ${active ? 'var(--border-strong)' : 'var(--border-soft)'}`,
        background: active ? 'var(--bg-2)' : 'transparent',
        color: active ? 'var(--text-0)' : 'var(--text-2)',
        fontSize: 10.5,
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  )
}

function IconButton({
  children,
  title,
  onClick,
  disabled,
}: {
  children: React.ReactNode
  title: string
  onClick: () => void
  disabled?: boolean
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      aria-label={title}
      disabled={disabled}
      className="flex items-center justify-center"
      style={{
        width: 24,
        height: 24,
        borderRadius: 6,
        border: '1px solid transparent',
        background: 'transparent',
        color: disabled ? 'var(--text-3)' : 'var(--text-1)',
        opacity: disabled ? 0.55 : 1,
        cursor: disabled ? 'not-allowed' : 'pointer',
      }}
    >
      {children}
    </button>
  )
}
