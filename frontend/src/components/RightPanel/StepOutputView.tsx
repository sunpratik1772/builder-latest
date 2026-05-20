/**
 * Per-node output viewer — Table / Logs / JSON tabs + download for CSV/Excel exports.
 */
import { useMemo, useState } from 'react'
import { ArcIcon, Table2, Braces, FileText, AlertTriangle, Download } from '../../icons/arc'
import type { RunLogEntry } from '../../types'

type Tab = 'table' | 'logs' | 'json'

const PREVIEW_ROWS = 50

function resolveDownloadHref(url: string): string {
  if (!url) return url
  if (/^https?:\/\//i.test(url)) return url
  if (url.startsWith('/api/')) return url
  if (url.startsWith('/')) return `/api${url}`
  return `/api/${url}`
}

interface Props {
  output: RunLogEntry['output']
  error?: string | null
  nodeId?: string
}

function parseCsvText(text: string): Record<string, unknown>[] {
  const lines = text.trim().split(/\r?\n/)
  if (lines.length < 2) return []
  const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''))
  const rows: Record<string, unknown>[] = []
  for (const line of lines.slice(1)) {
    if (!line.trim()) continue
    const cells = line.match(/("([^"]|"")*"|[^,]*)/g) ?? line.split(',')
    const obj: Record<string, unknown> = {}
    headers.forEach((h, i) => {
      let v = (cells[i] ?? '').trim()
      if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1).replace(/""/g, '"')
      obj[h] = v
    })
    rows.push(obj)
  }
  return rows
}

function pickRows(output: Record<string, unknown> | undefined): unknown[] | null {
  if (!output) return null
  if (Array.isArray(output.rows) && output.rows.length > 0) return output.rows
  if (typeof output.csv === 'string' && output.csv.trim()) {
    const parsed = parseCsvText(output.csv)
    if (parsed.length) return parsed
  }
  if (output._type === 'condition') {
    const t = (output.rows_true as unknown[]) ?? []
    const f = (output.rows_false as unknown[]) ?? []
    return t.length >= f.length ? t : f
  }
  if (output._type === 'router' && output.buckets && typeof output.buckets === 'object') {
    return Object.values(output.buckets as Record<string, unknown[]>).flat()
  }
  const datasets = output.datasets as Record<string, { sample?: unknown[] }> | undefined
  if (datasets) {
    const first = Object.values(datasets)[0]
    if (first?.sample && Array.isArray(first.sample)) return first.sample
  }
  return null
}

function pickLogs(output: Record<string, unknown> | undefined): string[] | null {
  if (!output) return null
  if (Array.isArray(output.logs)) return output.logs.map(String)
  if (typeof output.message === 'string') return [output.message]
  if (typeof output.response === 'string') return [output.response]
  if (typeof output.agent_response === 'string') return [output.agent_response]
  return null
}

/** Flatten RunLogEntry.output into a single object for StepOutputView. */
export function flattenRunOutput(
  out: RunLogEntry['output'] | undefined,
  nodeId?: string,
): Record<string, unknown> | undefined {
  if (!out) return undefined
  const ctx = out.context
  if (ctx && nodeId) {
    const key = `${nodeId}_output`
    const raw = ctx[key]
    if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      return raw as Record<string, unknown>
    }
  }
  if (out.node_output && typeof out.node_output === 'object') {
    return out.node_output as Record<string, unknown>
  }
  const payload: Record<string, unknown> = { ...out }
  if (out.datasets) {
    const entries = Object.entries(out.datasets)
    if (entries.length > 0) {
      const [name, ds] = entries[0]
      payload.rows = ds.sample
      payload.rowCount = ds.rows
      payload._dataset = name
    }
  }
  return payload
}

export default function StepOutputView({ output, error, nodeId }: Props) {
  const flat = useMemo(() => flattenRunOutput(output, nodeId), [output, nodeId])
  const rows = useMemo(() => pickRows(flat), [flat])
  const logs = useMemo(() => pickLogs(flat), [flat])
  const downloadUrl =
    typeof flat?.download_url === 'string' ? resolveDownloadHref(flat.download_url) : null
  const downloadName =
    typeof flat?.filename === 'string'
      ? flat.filename
      : downloadUrl
        ? decodeURIComponent(downloadUrl.split('/').pop() || 'download')
        : 'download'

  const initialTab: Tab =
    error ? 'json' : rows && rows.length > 0 ? 'table' : logs && logs.length > 0 ? 'logs' : 'json'
  const [tab, setTab] = useState<Tab>(initialTab)

  const tabs: { id: Tab; label: string; icon: typeof Table2; available: boolean; count?: number }[] = [
    { id: 'table', label: 'Table', icon: Table2, available: !!(rows && rows.length > 0), count: rows?.length },
    { id: 'logs', label: 'Logs', icon: FileText, available: !!(logs && logs.length > 0), count: logs?.length },
    { id: 'json', label: 'JSON', icon: Braces, available: true },
  ]

  if (!flat && !error) {
    return <div style={{ fontSize: 11, color: 'var(--text-3)' }}>No output recorded.</div>
  }

  return (
    <div
      className="rounded-md overflow-hidden"
      style={{ border: '1px solid var(--border)', background: 'var(--bg-0)' }}
    >
      {downloadUrl ? (
        <a
          href={downloadUrl}
          download={downloadName}
          target="_blank"
          rel="noopener"
          className="flex items-center justify-center gap-2 mx-2 mt-2 rounded-md"
          style={{
            padding: '8px 12px',
            fontSize: 12,
            fontWeight: 600,
            background: 'linear-gradient(180deg, var(--info) 0%, color-mix(in srgb, var(--info) 70%, black) 100%)',
            color: '#fff',
            border: '1px solid color-mix(in srgb, var(--info) 50%, transparent)',
          }}
        >
          <ArcIcon icon={Download} size={14} strokeWidth={2.2} />
          <span>Download {downloadName}</span>
        </a>
      ) : null}

      {error && (
        <div
          className="flex items-start gap-2 px-3 py-2 font-mono"
          style={{
            fontSize: 10,
            background: 'color-mix(in srgb, var(--danger) 10%, transparent)',
            color: 'var(--danger)',
            borderBottom: '1px solid var(--border-soft)',
          }}
        >
          <ArcIcon icon={AlertTriangle} size={12} className="shrink-0 mt-0.5" />
          <span className="break-words">{error}</span>
        </div>
      )}

      <div className="flex items-center gap-0.5 px-1.5 pt-1.5" style={{ background: 'var(--bg-2)' }}>
        {tabs.filter((t) => t.available).map((t) => {
          const active = tab === t.id
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className="flex items-center gap-1.5 px-2 py-1 font-mono rounded-t transition-colors"
              style={{
                fontSize: 10,
                background: active ? 'var(--bg-0)' : 'transparent',
                color: active ? 'var(--text-0)' : 'var(--text-3)',
                border: active ? '1px solid var(--border-soft)' : '1px solid transparent',
                borderBottom: active ? '1px solid var(--bg-0)' : 'none',
              }}
            >
              <ArcIcon icon={t.icon} size={10} />
              {t.label}
              {typeof t.count === 'number' && (
                <span style={{ color: 'var(--text-3)', fontSize: 9 }}>· {t.count}</span>
              )}
            </button>
          )
        })}
      </div>

      <div className="overflow-auto" style={{ maxHeight: 'min(420px, 50vh)' }}>
        {tab === 'table' && rows && rows.length > 0 && <RowsTable rows={rows} />}
        {tab === 'table' && (!rows || rows.length === 0) && (
          <div className="p-3" style={{ fontSize: 11, color: 'var(--text-3)' }}>
            No table rows. {downloadUrl ? 'Use the download button above for the export file.' : 'Check the JSON tab.'}
          </div>
        )}
        {tab === 'logs' && logs && (
          <pre
            className="font-mono p-2.5 whitespace-pre-wrap break-words"
            style={{ fontSize: 10, color: 'var(--text-0)' }}
          >
            {logs.join('\n')}
          </pre>
        )}
        {tab === 'json' && (
          <pre
            className="font-mono p-2.5 whitespace-pre-wrap break-words"
            style={{ fontSize: 10, color: 'var(--text-0)' }}
          >
            {JSON.stringify(flat ?? {}, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}

function RowsTable({ rows }: { rows: unknown[] }) {
  const preview = rows.slice(0, PREVIEW_ROWS)
  const columns = useMemo(() => {
    const seen = new Set<string>()
    for (const r of preview) {
      if (r && typeof r === 'object' && !Array.isArray(r)) {
        for (const k of Object.keys(r as object)) seen.add(k)
      }
    }
    return Array.from(seen).slice(0, 16)
  }, [preview])

  if (columns.length === 0) {
    return (
      <table className="w-full font-mono" style={{ fontSize: 10 }}>
        <tbody>
          {preview.map((v, i) => (
            <tr key={i} style={{ borderBottom: '1px solid var(--border-soft)' }}>
              <td className="px-2.5 py-1 text-right tabular-nums" style={{ color: 'var(--text-3)', width: 28 }}>
                {i + 1}
              </td>
              <td className="px-2.5 py-1" style={{ color: 'var(--text-0)' }}>
                {formatCell(v)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    )
  }

  return (
    <div>
      <table className="w-full font-mono border-separate border-spacing-0" style={{ fontSize: 10 }}>
        <thead>
          <tr>
            <th
              className="sticky top-0 z-10 px-2 py-1.5 text-right tabular-nums"
              style={{
                width: 28,
                color: 'var(--text-3)',
                background: 'var(--bg-2)',
                borderBottom: '1px solid var(--border)',
              }}
            >
              #
            </th>
            {columns.map((col) => (
              <th
                key={col}
                className="sticky top-0 z-10 px-2 py-1.5 text-left whitespace-nowrap"
                style={{
                  color: 'var(--text-2)',
                  fontWeight: 600,
                  background: 'var(--bg-2)',
                  borderBottom: '1px solid var(--border)',
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {preview.map((row, i) => (
            <tr key={i}>
              <td
                className="px-2 py-1 text-right tabular-nums"
                style={{ color: 'var(--text-3)', borderBottom: '1px solid var(--border-soft)' }}
              >
                {i + 1}
              </td>
              {columns.map((col) => {
                const cell = formatCell((row as Record<string, unknown>)?.[col])
                return (
                  <td
                    key={col}
                    title={cell}
                    className="px-2 py-1 truncate"
                    style={{
                      color: 'var(--text-0)',
                      maxWidth: 220,
                      borderBottom: '1px solid var(--border-soft)',
                    }}
                  >
                    {cell}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > PREVIEW_ROWS && (
        <div
          className="px-2.5 py-1.5 font-mono text-center"
          style={{
            fontSize: 9,
            color: 'var(--text-3)',
            borderTop: '1px solid var(--border-soft)',
          }}
        >
          Showing {PREVIEW_ROWS} of {rows.length} rows
        </div>
      )}
    </div>
  )
}

function formatCell(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'object') return JSON.stringify(v)
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}
