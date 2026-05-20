/** dbSherpa product mark — inline stub (replaces Cursor logo). */
export function DbSherpaIcon({
  size = 24,
  className,
  style,
}: {
  size?: number
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
      aria-hidden
    >
      <rect width="32" height="32" rx="7" fill="var(--accent)" />
      <path
        d="M8 21.5L16 9l8 12.5H8z"
        fill="var(--linear-accent-on, #fff)"
        fillOpacity="0.95"
      />
      <path
        d="M11.5 18.5h9"
        stroke="color-mix(in srgb, var(--linear-accent-on, #fff) 65%, transparent)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}
