/**
 * AUTO-GENERATED — do not edit by hand.
 * Run `python backend/scripts/gen_artifacts.py` to regenerate.
 * Maps NodeSpec `ui.icon` strings to Lucide components (tree-shaken).
 */
import type { LucideIcon } from 'lucide-react'
import {
  ArrowLeftRight,
  Box,
  CandlestickChart,
  Clock,
  Crosshair,
  Database,
  FileSpreadsheet,
  FileStack,
  Gavel,
  Highlighter,
  ListFilter,
  ListOrdered,
  MessageSquareText,
  NotebookText,
  Repeat,
  Signal,
  Siren,
  SlidersHorizontal,
  Split,
  createArcIcon,
} from '../icons/arc'

export const LUCIDE_ICON_MAP: Record<string, LucideIcon> = {
  ArrowLeftRight: createArcIcon(ArrowLeftRight),
  Box: createArcIcon(Box),
  CandlestickChart: createArcIcon(CandlestickChart),
  Clock: createArcIcon(Clock),
  Crosshair: createArcIcon(Crosshair),
  Database: createArcIcon(Database),
  FileSpreadsheet: createArcIcon(FileSpreadsheet),
  FileStack: createArcIcon(FileStack),
  Gavel: createArcIcon(Gavel),
  Highlighter: createArcIcon(Highlighter),
  ListFilter: createArcIcon(ListFilter),
  ListOrdered: createArcIcon(ListOrdered),
  MessageSquareText: createArcIcon(MessageSquareText),
  NotebookText: createArcIcon(NotebookText),
  Repeat: createArcIcon(Repeat),
  Signal: createArcIcon(Signal),
  Siren: createArcIcon(Siren),
  SlidersHorizontal: createArcIcon(SlidersHorizontal),
  Split: createArcIcon(Split),
}

export function resolveLucideIcon(name: string | undefined): LucideIcon {
  if (!name) return Box
  return LUCIDE_ICON_MAP[name] ?? Box
}
