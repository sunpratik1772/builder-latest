/** sherpa — Arc sparkles + asterisk (replaces cube / Cursor mark). */
import { ArcIcon, Sparkles } from '../icons/arc'

export function SherpaMark({ size = 17 }: { size?: number }) {
  const star = Math.round(size * 0.88)
  return (
    <span
      className="relative inline-flex items-center justify-center shrink-0"
      style={{ width: size, height: size, color: 'var(--accent)' }}
      aria-hidden
    >
      <ArcIcon icon={Sparkles} size={star} />
      <span
        className="font-mono"
        style={{
          position: 'absolute',
          right: -1,
          top: -2,
          fontSize: Math.max(7, Math.round(size * 0.42)),
          fontWeight: 700,
          lineHeight: 1,
          color: 'var(--accent-hi, var(--accent))',
        }}
      >
        *
      </span>
    </span>
  )
}
