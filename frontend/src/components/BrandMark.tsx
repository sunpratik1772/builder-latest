import type { CSSProperties } from 'react'
import { DbSherpaIcon } from './DbSherpaIcon'

type BrandMarkProps = {
  size?: number
  className?: string
  style?: CSSProperties
}

export default function BrandMark({ size = 28, className, style }: BrandMarkProps) {
  return (
    <DbSherpaIcon
      size={size}
      className={className}
      style={{ flexShrink: 0, ...style }}
    />
  )
}
