/**
 * Copilot panel — the LLM-driven workflow author / editor.
 *
 * Three modes:
 *   • Generate — type intent, get a brand-new validated workflow.
 *   • Edit     — describe a change to the current canvas, copilot
 *                returns a patched DAG. The diff is previewed before
 *                applying.
 *   • Explain  — ask questions about the current workflow.
 *
 * Streaming: copilot.streamGenerate / streamEdit yield SSE events
 * (planning → tool_call → patch → done). This component renders them
 * progressively so the user sees the agent's reasoning instead of
 * staring at a spinner. Events are typed in `types/index.ts` —
 * unrecognised event kinds are ignored, not crashed on, so the
 * backend can add new event types without breaking old clients.
 */
import { useState, useRef, useEffect } from 'react'
import ResizeHandle from '../ResizeHandle'
import {
  ArcIcon,
  ArrowUp,
  GitMerge,
  Hammer,
  MessageSquare,
  Wrench,
  X as XIcon,
} from '../../icons/arc'
import ThinkingBlock from './ThinkingBlock'
import { SherpaMark } from '../SherpaMark'
import type { ThinkingStep } from './thinkingTypes'
import { AgentIdleWave } from './AgentChrome'
import { useWorkflowStore } from '../../store/workflowStore'
import { api } from '../../services/api'
import type { CopilotGuardrailsPayload } from '../../services/api'
import type {
  CopilotMessage,
  CopilotStreamEvent,
  CopilotErrorHint,
  Workflow,
  RunLogEntry,
  ValidationIssue,
} from '../../types'

function normalizeTextareaHeight(el: HTMLTextAreaElement | null): void {
  if (!el) return
  el.style.height = 'auto'
  // Keep the input compact but allow a few lines before scrolling.
  const next = Math.min(160, Math.max(44, el.scrollHeight))
  el.style.height = `${next}px`
}

function shouldEditExistingWorkflow(prompt: string): boolean {
  const text = prompt.toLowerCase()
  if (/\b(create|generate|build|make|new)\b/.test(text)) return false
  return /\b(fix|repair|edit|update|change|modify|add|remove|delete|replace|this|current|existing|canvas)\b/.test(text)
}

function SherpaAvatar({ size = 24 }: { size?: number }) {
  return <SherpaMark size={size} />
}

function finalizeThinkingStep(prev: ThinkingStep[], now = Date.now()): ThinkingStep[] {
  if (prev.length === 0) return prev
  const last = prev[prev.length - 1]
  if (last.done) return prev
  const copy = [...prev]
  copy[copy.length - 1] = {
    ...last,
    done: true,
    durationSec: Math.max(0.05, (now - last.startedAt) / 1000),
  }
  return copy
}

function appendThinkingStep(prev: ThinkingStep[], text: string): ThinkingStep[] {
  const now = Date.now()
  return [
    ...finalizeThinkingStep(prev, now),
    { id: `s-${now}-${prev.length}`, text, done: false, startedAt: now },
  ]
}

function closeAllThinkingSteps(prev: ThinkingStep[]): ThinkingStep[] {
  return finalizeThinkingStep(prev).map((s) => ({ ...s, done: true }))
}

function useThinkingQueue() {
  const chainRef = useRef(Promise.resolve())
  const enqueue = (fn: () => void, delayMs = 280) => {
    chainRef.current = chainRef.current.then(
      () =>
        new Promise<void>((resolve) => {
          fn()
          window.setTimeout(resolve, delayMs)
        }),
    )
  }
  const reset = () => {
    chainRef.current = Promise.resolve()
  }
  return { enqueue, reset }
}


/**
 * Roll up every error the UI is currently showing into the
 * `CopilotErrorHint[]` shape the backend's edit-mode prompt expects.
 * Sources, in priority order:
 *   1. Pre-flight validator issues (if any) — deterministic, structured.
 *   2. Per-node runtime errors from the last run (from runLog).
 *   3. Generic runError (used for network / non-structured failures).
 *
 * De-duplication is keyed on (node_id, message). Capped at 20 hints so
 * a pathological run doesn't blow the prompt context.
 */
function collectErrorHints(
  validationIssues: ValidationIssue[] | null,
  runLog: RunLogEntry[],
  runError: string | null,
): CopilotErrorHint[] {
  const hints: CopilotErrorHint[] = []
  const seen = new Set<string>()

  const push = (h: CopilotErrorHint) => {
    const key = `${h.node_id ?? ''}::${h.message}`
    if (seen.has(key)) return
    seen.add(key)
    hints.push(h)
  }

  for (const issue of validationIssues ?? []) {
    push({
      kind: 'validation',
      code: issue.code,
      node_id: issue.node_id ?? undefined,
      severity: issue.severity,
      message: issue.message,
    })
  }

  for (const entry of runLog) {
    if (entry.status !== 'error' || !entry.error) continue
    push({
      kind: 'runtime',
      node_id: entry.node_id,
      severity: 'error',
      // Include the node type in the message so the LLM doesn't have
      // to cross-reference it against the attached DAG to diagnose.
      message: entry.node_type
        ? `${entry.node_type} (${entry.node_id}): ${entry.error}`
        : `${entry.node_id}: ${entry.error}`,
    })
  }

  if (runError && !validationIssues?.length) {
    // Only include the generic runError if the structured validator
    // path didn't already cover the failure — otherwise we'd double-
    // report the same underlying issue.
    push({ kind: 'runtime', severity: 'error', message: runError })
  }

  return hints.slice(0, 20)
}

/**
 * Linear-style 4-point sparkle. Two crossed diamonds rendered as a
 * single SVG so it scales crisply at any size and never carries the
 * "AI slop" gradient look of stock star icons.
 */
function AiGlyph({ size = 14 }: { size?: number }) {
  return <SherpaMark size={size} />
}

const EXAMPLE_PROMPTS = [
  'Build a workflow that pulls trade data, scores anomalies, and writes a report',
  'Add a validation step before the report generation',
  'Show me what each node in the canvas does and how they connect',
  'Refactor the workflow to add a critic loop with 2 iterations',
]

const ASK_PROMPTS = [
  'What nodes are available and what does each one do?',
  'Which data sources can I query and what columns do they expose?',
  'Explain how the SIGNAL_CALCULATOR node works',
  'What skills are loaded and when does the agent use them?',
]

function MessageBubble({ msg }: { msg: CopilotMessage }) {
  const isUser = msg.role === 'user'
  const isJson = !isUser && msg.content.trim().startsWith('{')
  const time = msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })

  // Tight, row-style messages — small radius, monospace timestamp eyebrow,
  // matching the EntryRow / param row visual language used elsewhere in the
  // right panel.
  return (
    <div className="mb-3">
      <div
        className="font-mono mb-1 flex items-center gap-1.5"
        style={{ fontSize: 9.5, letterSpacing: '0.18em', textTransform: 'uppercase', color: 'var(--text-3)' }}
      >
        {isUser ? (
          <span style={{ color: 'var(--info)' }}>You</span>
        ) : (
          <>
            <AiGlyph size={9} />
            <span style={{ color: 'var(--accent)' }}>sherpa</span>
          </>
        )}
        <span style={{ color: 'var(--text-3)' }}>· {time}</span>
      </div>
      <div
        className="rounded-md"
        style={{
          fontSize: 12,
          padding: '8px 10px',
          background: isUser
            ? 'color-mix(in srgb, var(--info) 8%, var(--bg-2))'
            : 'var(--bg-2)',
          color: 'var(--text-0)',
          border: `1px solid ${isUser
            ? 'color-mix(in srgb, var(--info) 25%, transparent)'
            : 'var(--border-soft)'}`,
          lineHeight: 1.55,
        }}
      >
        {isJson ? (
          <pre
            className="num overflow-x-auto whitespace-pre-wrap break-all"
            style={{ fontSize: 10.5, color: 'var(--success)', maxHeight: 260, overflowY: 'auto' }}
          >
            {msg.content}
          </pre>
        ) : (
          <p className="whitespace-pre-wrap">{msg.content}</p>
        )}
      </div>
    </div>
  )
}

function TypingDots() {
  return (
    <div
      className="flex items-center gap-2 px-3 py-2 rounded-xl"
      style={{ background: 'var(--bg-2)', border: '1px solid var(--border-soft)' }}
      role="status"
      aria-label="sherpa is typing"
    >
      <AgentIdleWave />
    </div>
  )
}

function GuardrailsCard({ guardrails, error }: { guardrails: CopilotGuardrailsPayload | null; error: string | null }) {
  const caps = guardrails?.capabilities
  const skillNames = guardrails?.skills.map((s) => s.name).slice(0, 4).join(', ')
  return (
    <div
      style={{
        padding: '12px 14px',
        borderRadius: 10,
        background: 'var(--bg-2)',
        border: '1px solid var(--border)',
      }}
    >
      <div className="font-mono mb-2" style={{ fontSize: 10, color: 'var(--text-3)', letterSpacing: '0.18em', textTransform: 'uppercase' }}>
        ACTIVE GUARDRAILS
      </div>
      {guardrails ? (
        <div style={{ fontSize: 12.5, color: 'var(--text-1)', lineHeight: 1.55 }}>
          <p>
            sherpa is constrained to{' '}
            <span style={{ color: 'var(--text-0)', fontWeight: 600 }}>{guardrails.nodes.length} live nodes</span>,{' '}
            <span style={{ color: 'var(--text-0)', fontWeight: 600 }}>{guardrails.data_sources.length} data catalogs</span>, and{' '}
            <span style={{ color: 'var(--text-0)', fontWeight: 600 }}>{guardrails.skills.length} skills</span>.
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <span className="num px-2 py-1 rounded" style={{ background: 'var(--bg-3)', color: caps?.upload_script_enabled ? 'var(--warning)' : 'var(--success)', border: '1px solid var(--border-soft)', fontSize: 10.5 }}>
              upload_script {caps?.upload_script_enabled ? 'on' : 'off'}
            </span>
            <span className="num px-2 py-1 rounded" style={{ background: 'var(--bg-3)', color: 'var(--text-2)', border: '1px solid var(--border-soft)', fontSize: 10.5 }}>
              signal modes: {caps?.allowed_signal_modes.join(', ')}
            </span>
          </div>
          {skillNames && (
            <p className="mt-2" style={{ color: 'var(--text-2)' }}>
              Skills in prompt: {skillNames}{guardrails.skills.length > 4 ? '...' : ''}
            </p>
          )}
        </div>
      ) : (
        <p style={{ fontSize: 12.5, color: error ? 'var(--danger)' : 'var(--text-2)', lineHeight: 1.55 }}>
          {error ?? 'Loading node, source, skill, and host capability guardrails...'}
        </p>
      )}
    </div>
  )
}

export default function Copilot() {
  const { copilotMessages, addCopilotMessage, clearCopilotMessages, setWorkflow } = useWorkflowStore()
  const copilotWidth = useWorkflowStore((s) => s.copilotWidth)
  const setCopilotWidth = useWorkflowStore((s) => s.setCopilotWidth)
  // Auto-attach context for edit-mode on every send. We subscribe to
  // these in the component so the values are always current — the
  // store is a single source of truth for the canvas state.
  const currentWorkflow = useWorkflowStore((s) => s.workflow)
  const runLog = useWorkflowStore((s) => s.runLog)
  const validationIssues = useWorkflowStore((s) => s.validationIssues)
  const runError = useWorkflowStore((s) => s.runError)
  const selectedNodeId = useWorkflowStore((s) => s.selectedNodeId)
  const copilotDraft = useWorkflowStore((s) => s.copilotDraft)
  const setCopilotDraft = useWorkflowStore((s) => s.setCopilotDraft)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [useGenerate, setUseGenerate] = useState(true)
  const [criticIter, setCriticIter] = useState(3)
  const [thinkingSteps, setThinkingSteps] = useState<ThinkingStep[]>([])
  const [thinkingOpen, setThinkingOpen] = useState(true)
  const [streamText, setStreamText] = useState('')
  const [workflowCreated, setWorkflowCreated] = useState<{ name: string; nodeCount: number } | null>(null)
  const [streamError, setStreamError] = useState<string | null>(null)
  const { enqueue, reset: resetThinkingQueue } = useThinkingQueue()
  const [guardrails, setGuardrails] = useState<CopilotGuardrailsPayload | null>(null)
  const [guardrailError, setGuardrailError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const rootRef = useRef<HTMLDivElement>(null)
  const streamTextRef = useRef('')

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [copilotMessages, isLoading, thinkingSteps, streamText])

  useEffect(() => {
    normalizeTextareaHeight(inputRef.current)
  }, [input])

  useEffect(() => {
    let active = true
    api.getCopilotGuardrails()
      .then((payload) => {
        if (!active) return
        setGuardrails(payload)
        setGuardrailError(null)
      })
      .catch((err: Error) => {
        if (!active) return
        setGuardrailError(err.message || 'Unable to load guardrails')
      })
    return () => { active = false }
  }, [])

  // "Fix with Copilot" CTAs elsewhere in the app set copilotDraft; we
  // adopt it into our local textarea state and clear the store slot so
  // it only fires once. Also focus the textarea so the user can either
  // hit Enter or tweak the prefilled text before sending.
  useEffect(() => {
    if (copilotDraft && copilotDraft !== input) {
      setInput(copilotDraft)
      setCopilotDraft(null)
      // Defer focus until after React re-renders the textarea with
      // the new value.
      requestAnimationFrame(() => inputRef.current?.focus())
    }
    // Intentional: only react to copilotDraft changes, not local input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [copilotDraft])

  function handleStreamEvent(ev: CopilotStreamEvent) {
    switch (ev.type) {
      case 'thinking':
        enqueue(() => {
          setThinkingSteps((prev) => appendThinkingStep(prev, ev.step))
        })
        break
      case 'text_start':
        enqueue(() => {
          setThinkingSteps((prev) => closeAllThinkingSteps(prev))
        }, 0)
        break
      case 'text_chunk': {
        const next = streamTextRef.current + ev.chunk
        streamTextRef.current = next
        setStreamText(next)
        break
      }
      case 'workflow_created':
        enqueue(() => {
          setThinkingSteps((prev) => closeAllThinkingSteps(prev))
          setThinkingOpen(false)
          setWorkflowCreated({ name: ev.name, nodeCount: ev.nodeCount })
          if (ev.workflow) {
            useWorkflowStore.getState().resetRun()
            setWorkflow(ev.workflow)
          }
        }, 0)
        break
      case 'done':
        enqueue(() => {
          setThinkingSteps((prev) => closeAllThinkingSteps(prev))
          setThinkingOpen(false)
        }, 0)
        break
      case 'error':
        setStreamError(ev.message)
        setThinkingOpen(false)
        break
      default:
        break
    }
  }

  async function send() {
    const msg = input.trim()
    if (!msg || isLoading) return
    setInput('')

    const userMsg: CopilotMessage = { role: 'user', content: msg, timestamp: new Date() }
    addCopilotMessage(userMsg)
    setIsLoading(true)
    setThinkingSteps([])
    setStreamText('')
    streamTextRef.current = ''
    setWorkflowCreated(null)
    setStreamError(null)
    setThinkingOpen(true)
    resetThinkingQueue()

    // Build context only for explicit edit/fix requests. Plain "create /
    // generate / build" prompts are greenfield and replace whatever is on
    // the canvas when the final validated workflow arrives.
    const editExisting = Boolean(currentWorkflow && shouldEditExistingWorkflow(msg))
    const ctxWorkflow = editExisting ? currentWorkflow : null
    const errorHints = ctxWorkflow
      ? collectErrorHints(validationIssues, runLog, runError)
      : null

    try {
      let replyText: string
      if (useGenerate) {
        let gotWorkflow = false
        let createdName = ''
        let createdNodes = 0

        await api.copilotGenerateStream(
          msg,
          criticIter,
          (ev) => {
            handleStreamEvent(ev)
            if (ev.type === 'workflow_created' && ev.workflow) {
              gotWorkflow = true
              createdName = ev.name
              createdNodes = ev.nodeCount
            }
          },
          undefined,
          ctxWorkflow,
          errorHints,
          ctxWorkflow ? selectedNodeId : null,
        )

        if (streamTextRef.current.trim()) {
          replyText = streamTextRef.current.trim()
        } else if (gotWorkflow) {
          replyText = `Built **${createdName}** (${createdNodes} nodes). Loaded on the canvas.`
        } else if (streamError) {
          replyText = `Generation failed: ${streamError}`
        } else {
          replyText = 'Generation finished without a workflow.'
        }
      } else {
        // Ask mode — stream the reply chunk-by-chunk so the bubble
        // fills in as the model responds. Seed the assistant message
        // empty up front, then append each chunk as it arrives.
        addCopilotMessage({ role: 'assistant', content: '', timestamp: new Date() })
        let final = ''
        await api.copilotChatStream(msg, (ev) => {
          if (ev.type === 'chunk') {
            useWorkflowStore.getState().appendToLastAssistantMessage(ev.text)
            final += ev.text
          } else if (ev.type === 'error') {
            useWorkflowStore.getState().appendToLastAssistantMessage(
              (final ? '\n\n' : '') + `Error: ${ev.error}`,
            )
          }
        })
        // We've already pushed the assistant bubble; skip the
        // post-hoc addCopilotMessage path below.
        setIsLoading(false)
        return
      }

      addCopilotMessage({ role: 'assistant', content: replyText, timestamp: new Date() })
    } catch (e) {
      addCopilotMessage({
        role: 'assistant',
        content: `Error: ${(e as Error).message}\n\nMake sure the backend is running (check /api/health and GEMINI_API_KEY in backend/.env).`,
        timestamp: new Date(),
      })
    } finally {
      setIsLoading(false)
      if (useGenerate) {
        setThinkingSteps([])
        setStreamText('')
        streamTextRef.current = ''
        setWorkflowCreated(null)
        setStreamError(null)
      }
    }
  }

  return (
    <div
      ref={rootRef}
      className="panel-glass flex flex-col relative shrink-0"
      style={{
        width: copilotWidth,
        borderLeft: '1px solid var(--border)',
        height: '100%',
      }}
    >
      {/* Drag the left edge to resize the copilot (VSCode-style). */}
      <ResizeHandle
        edge="left"
        ariaLabel="Resize copilot panel"
        onResize={(clientX) => {
          const right = rootRef.current?.getBoundingClientRect().right ?? window.innerWidth
          setCopilotWidth(right - clientX)
        }}
      />
      {/* Header — sleek single row: icon + title + close + mode toggle. */}
      <div className="px-4 py-2.5 shrink-0" style={{ borderBottom: '1px solid var(--border-soft)' }}>
        <div className="flex items-center gap-2">
          <button
            type="button"
            title="sherpa"
            aria-label="sherpa"
            className="flex items-center justify-center"
            style={{
              width: 28,
              height: 28,
              borderRadius: 7,
              background: 'var(--bg-3)',
              border: '1px solid var(--border-soft)',
              color: 'var(--accent)',
              cursor: 'default',
            }}
          >
            <SherpaMark size={16} />
          </button>
          <span
            className="display truncate"
            style={{
              fontSize: 13.5,
              fontWeight: 530,
              color: 'var(--text-0)',
              letterSpacing: '-0.02em',
            }}
          >
            sherpa
          </span>
          <span
            className="font-mono"
            style={{
              fontSize: 9.5,
              color: 'var(--text-3)',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
            }}
          >
            AGENT
          </span>
          <div className="flex-1" />
          {/* Mode toggle: Build (workflow generation) vs Ask (Q&A about the platform) */}
          <div
            className="flex items-center"
            style={{
              padding: 2,
              borderRadius: 7,
              background: 'var(--bg-2)',
              border: '1px solid var(--border-soft)',
            }}
          >
            <IconModePill
              active={useGenerate}
              onClick={() => setUseGenerate(true)}
              testId="copilot-mode-build"
              title={currentWorkflow ? 'Edit workflow' : 'Build workflow'}
              icon={<ArcIcon icon={Hammer} size={12} />}
            />
            <IconModePill
              active={!useGenerate}
              onClick={() => setUseGenerate(false)}
              testId="copilot-mode-ask"
              title="Ask"
              icon={<ArcIcon icon={MessageSquare} size={12} />}
            />
          </div>
          <button
            onClick={() => useWorkflowStore.getState().setRightPanelMode(null)}
            aria-label="Close panel"
            data-testid="copilot-close-btn"
            className="flex items-center justify-center"
            style={{
              width: 22, height: 22, borderRadius: 5,
              background: 'transparent', color: 'var(--text-3)',
              border: '1px solid transparent',
              cursor: 'pointer',
            }}
            onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'var(--border)'; (e.currentTarget as HTMLElement).style.color = 'var(--text-0)' }}
            onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = 'transparent'; (e.currentTarget as HTMLElement).style.color = 'var(--text-3)' }}
          >
            <ArcIcon icon={XIcon} size={11} />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {copilotMessages.length === 0 && (
          <div className="space-y-3">
            {/* Compact greeting line */}
            <div
              className="flex items-start gap-2.5"
              style={{ marginBottom: 6 }}
            >
              <div
                className="shrink-0 flex items-center justify-center"
                style={{
                  width: 22, height: 22, borderRadius: 6,
                  background: 'var(--bg-3)',
                  border: '1px solid var(--border-soft)',
                }}
              >
                <AiGlyph size={11} />
              </div>
              <div
                style={{
                  fontSize: 12.5,
                  color: 'var(--text-1)',
                  lineHeight: 1.5,
                  letterSpacing: '-0.005em',
                  paddingTop: 2,
                }}
              >
                {useGenerate
                  ? 'Describe a workflow — I\'ll build it.'
                  : 'Ask anything about the current workflow.'}
              </div>
            </div>

            {useGenerate && (
              <div>
                <div
                  className="font-mono px-1"
                  style={{
                    fontSize: 9.5,
                    color: 'var(--text-3)',
                    letterSpacing: '0.10em',
                    textTransform: 'uppercase',
                    marginTop: 14,
                    marginBottom: 6,
                  }}
                >
                  Try
                </div>
                <div className="flex flex-col" style={{ gap: 4 }}>
                  {EXAMPLE_PROMPTS.slice(0, 4).map((p, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(p)}
                      data-testid={`copilot-example-build-${i}`}
                      className="w-full text-left transition-colors flex items-start gap-2"
                      style={{
                        fontSize: 12,
                        padding: '7px 9px',
                        borderRadius: 6,
                        background: 'transparent',
                        color: 'var(--text-2)',
                        border: '1px solid var(--border-soft)',
                        lineHeight: 1.45,
                        letterSpacing: '-0.005em',
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-0)'
                        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)'
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-2)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-2)'
                        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-soft)'
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                      }}
                    >
                      <span style={{ color: 'var(--text-3)', lineHeight: 1.45 }}>›</span>
                      <span className="flex-1">{p}</span>
                    </button>
                  ))}
                </div>
                {guardrails && (
                  <div
                    className="font-mono"
                    style={{
                      fontSize: 9.5,
                      color: 'var(--text-3)',
                      letterSpacing: '0.02em',
                      marginTop: 12,
                      paddingLeft: 4,
                    }}
                  >
                    {guardrails.nodes.length} nodes · {guardrails.data_sources.length} sources · {guardrails.skills.length} skills
                  </div>
                )}
              </div>
            )}

            {!useGenerate && (
              <div>
                <div
                  className="font-mono px-1"
                  style={{
                    fontSize: 9.5,
                    color: 'var(--text-3)',
                    letterSpacing: '0.10em',
                    textTransform: 'uppercase',
                    marginTop: 14,
                    marginBottom: 6,
                  }}
                >
                  Ask
                </div>
                <div className="flex flex-col" style={{ gap: 4 }}>
                  {ASK_PROMPTS.map((p, i) => (
                    <button
                      key={i}
                      onClick={() => setInput(p)}
                      data-testid={`copilot-example-ask-${i}`}
                      className="w-full text-left transition-colors flex items-start gap-2"
                      style={{
                        fontSize: 12,
                        padding: '7px 9px',
                        borderRadius: 6,
                        background: 'transparent',
                        color: 'var(--text-2)',
                        border: '1px solid var(--border-soft)',
                        lineHeight: 1.45,
                        letterSpacing: '-0.005em',
                      }}
                      onMouseEnter={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-0)'
                        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)'
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'var(--bg-2)'
                      }}
                      onMouseLeave={(e) => {
                        ;(e.currentTarget as HTMLButtonElement).style.color = 'var(--text-2)'
                        ;(e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-soft)'
                        ;(e.currentTarget as HTMLButtonElement).style.background = 'transparent'
                      }}
                    >
                      <span style={{ color: 'var(--text-3)', lineHeight: 1.45 }}>›</span>
                      <span className="flex-1">{p}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {copilotMessages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {(isLoading || thinkingSteps.length > 0 || streamText || workflowCreated) && useGenerate && (
          <div className="mb-3 flex flex-col gap-2 pl-0.5">
            {(thinkingSteps.length > 0 || isLoading) && (
                  <ThinkingBlock
                    steps={thinkingSteps}
                    open={thinkingOpen}
                    isStreaming={isLoading}
                    onToggle={() => setThinkingOpen((o) => !o)}
                  />
                )}
                {streamText && (
                  <div
                    className="rounded-md px-3 py-2"
                    style={{
                      fontSize: 12,
                      lineHeight: 1.55,
                      background: 'var(--bg-2)',
                      border: '1px solid var(--border-soft)',
                      color: 'var(--text-0)',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {streamText}
                    {isLoading && (
                      <span
                        className="inline-block w-0.5 h-3.5 ml-0.5 align-middle animate-pulse"
                        style={{ background: 'var(--accent)' }}
                      />
                    )}
                  </div>
                )}
                {workflowCreated && (
                  <button
                    type="button"
                    title={`${workflowCreated.name} · ${workflowCreated.nodeCount} nodes`}
                    className="flex items-center justify-center"
                    style={{
                      width: 30,
                      height: 30,
                      borderRadius: 8,
                      background: 'color-mix(in srgb, var(--accent) 12%, transparent)',
                      border: '1px solid color-mix(in srgb, var(--accent) 30%, transparent)',
                      color: 'var(--accent)',
                    }}
                  >
                    <ArcIcon icon={GitMerge} size={15} />
                  </button>
                )}
                {streamError && (
                  <div style={{ fontSize: 12, color: 'var(--danger)' }}>{streamError}</div>
                )}
          </div>
        )}
        {isLoading && !useGenerate && (
          <div className="mb-3 pl-0.5">
            <TypingDots />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-3 border-t shrink-0" style={{ borderColor: 'var(--border)' }}>
        {/* Context indicator — a loaded workflow is available for explicit
            edit/fix prompts, but greenfield create/generate prompts replace it. */}
        {currentWorkflow && (() => {
          const hints = collectErrorHints(validationIssues, runLog, runError)
          const selected = selectedNodeId
            ? currentWorkflow.nodes.find((n) => n.id === selectedNodeId)
            : null
          const chipBg = hints.length
            ? 'color-mix(in srgb, var(--danger) 12%, transparent)'
            : 'color-mix(in srgb, var(--accent) 10%, transparent)'
          const chipBorder = hints.length
            ? 'color-mix(in srgb, var(--danger) 35%, transparent)'
            : 'color-mix(in srgb, var(--accent) 30%, transparent)'
          const chipColor = hints.length ? 'var(--danger)' : 'var(--accent)'
          const willEdit = shouldEditExistingWorkflow(input)
          const parts: string[] = [
            willEdit
              ? `Editing "${currentWorkflow.name}"`
              : `Generate will replace "${currentWorkflow.name}"`,
          ]
          if (hints.length) {
            parts.push(`${hints.length} error${hints.length === 1 ? '' : 's'}`)
          } else {
            parts.push(`${currentWorkflow.nodes.length} node${currentWorkflow.nodes.length === 1 ? '' : 's'}`)
          }
          if (selected) {
            parts.push(`"this" = ${selected.id} (${selected.type})`)
          }
          const label = parts.join(' · ')
          const title = hints.length
            ? hints.map((h) => `${(h.kind || 'error').toUpperCase()}${h.node_id ? ' @' + h.node_id : ''}: ${h.message}`).join('\n')
            : willEdit && selected
              ? `This edit prompt will attach the current canvas. Deictic references like "this" / "here" resolve to ${selected.id} (${selected.type}).`
              : willEdit
                ? 'This prompt will attach the current canvas so sherpa can make a targeted edit.'
                : 'Create/generate prompts start from a fresh workflow and replace the loaded canvas only after validation succeeds.'
          return (
            <div
              className="flex items-center gap-1.5 mb-2 px-2 py-1 rounded-md"
              style={{
                fontSize: 10.5,
                background: chipBg,
                border: `1px solid ${chipBorder}`,
                color: chipColor,
              }}
              title={title}
            >
              <ArcIcon icon={Wrench} size={10} strokeWidth={2.2} />
              <span className="num truncate" style={{ flex: 1, minWidth: 0 }}>{label}</span>
            </div>
          )
        })()}
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value)
              normalizeTextareaHeight(e.target)
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
            }}
            placeholder={
              !useGenerate
                ? 'Ask anything about nodes, data sources, or skills…'
                : currentWorkflow
                  ? 'Describe a fix or edit (the canvas workflow is attached)…'
                  : 'Describe a workflow…'
            }
            rows={1}
            data-testid="copilot-input"
            className="flex-1 rounded-lg px-3 py-2 resize-none outline-none transition-colors"
            style={{
              fontSize: 12,
              background: 'var(--bg-2)',
              color: 'var(--text-0)',
              border: '1px solid var(--border)',
              lineHeight: 1.5,
              minHeight: 44,
              maxHeight: 160,
            }}
            onFocus={(e) => { (e.target as HTMLTextAreaElement).style.border = '1px solid color-mix(in srgb, var(--accent) 50%, transparent)' }}
            onBlur={(e) => { (e.target as HTMLTextAreaElement).style.border = '1px solid var(--border)' }}
          />
          <button
            onClick={send}
            disabled={isLoading || !input.trim()}
            data-testid="copilot-send-btn"
            className="px-3 py-2 rounded-lg self-end flex items-center justify-center lift"
            style={{
              background: isLoading || !input.trim() ? 'var(--bg-3)' : 'var(--bg-2)',
              color: isLoading || !input.trim() ? 'var(--text-3)' : 'var(--accent)',
              cursor: isLoading || !input.trim() ? 'not-allowed' : 'pointer',
              minWidth: 40, minHeight: 36,
              border: isLoading || !input.trim()
                ? '1px solid var(--border)'
                : '1px solid color-mix(in srgb, var(--accent) 45%, var(--border))',
            }}
            aria-label="Send"
          >
            {isLoading
              ? <span className="num">…</span>
              : <ArcIcon icon={ArrowUp} size={14} strokeWidth={2.5} />}
          </button>
        </div>
        <p className="num mt-2" style={{ fontSize: 10, color: 'var(--text-3)', letterSpacing: '0.02em' }}>
          ⏎ send · ⇧⏎ newline
        </p>
      </div>
    </div>
  )
}

function SegTab({ active, onClick, icon, children }: { active: boolean; onClick: () => void; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1.5"
      style={{
        height: 30,
        padding: '0 12px',
        borderRadius: 7,
        fontSize: 12,
        fontWeight: 500,
        background: active ? 'var(--text-0)' : 'transparent',
        color: active ? 'var(--bg-0)' : 'var(--text-2)',
        border: active ? 'none' : '1px solid var(--border)',
        cursor: 'pointer',
      }}
    >
      {icon}
      <span>{children}</span>
    </button>
  )
}

function IconModePill({
  active,
  onClick,
  icon,
  title,
  testId,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  title: string
  testId?: string
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      title={title}
      aria-label={title}
      className="flex items-center justify-center"
      style={{
        width: 26,
        height: 26,
        borderRadius: 5,
        background: active ? 'var(--bg-0)' : 'transparent',
        color: active ? 'var(--accent)' : 'var(--text-3)',
        border: active ? '1px solid var(--border-strong)' : '1px solid transparent',
        cursor: 'pointer',
        transition: 'background 120ms, color 120ms, border-color 120ms',
      }}
    >
      {icon}
    </button>
  )
}
