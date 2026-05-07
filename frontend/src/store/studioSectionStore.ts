/**
 * Tracks which "section" of the studio is currently open.
 * The LeftNav writes here, the App renders the matching drawer.
 *
 * `null` means the canvas/workflow view is on top.
 */
import { create } from 'zustand'

export type StudioSection = null | 'skills' | 'data' | 'run-history' | 'nodes' | 'settings'

interface State {
  section: StudioSection
  setSection: (s: StudioSection) => void
  toggleSection: (s: Exclude<StudioSection, null>) => void
}

export const useStudioSectionStore = create<State>((set, get) => ({
  section: null,
  setSection: (section) => set({ section }),
  toggleSection: (s) => set({ section: get().section === s ? null : s }),
}))
