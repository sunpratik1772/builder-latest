/**
 * Top-level layout. Five regions, all driven by the workflow store:
 *
 *   ┌────────────────────────────────────────────────────────────────┐
 *   │ LeftNav │ Topbar                                               │
 *   │         ├──────────────────────────────────────────────────────┤
 *   │         │ NodePanel │ WorkflowCanvas │ Activity │ RightPanel  │
 *   │         ├──────────────────────────────────────────────────────┤
 *   │         │ BottomOutputPanel (when Output mode — resizable)     │
 *   └────────────────────────────────────────────────────────────────┘
 */
import { useEffect } from 'react'
import WorkflowCanvas from './components/WorkflowCanvas'
import NodePanel from './components/NodePanel'
import RightPanel from './components/RightPanel'
import Topbar from './components/Topbar'
import WorkflowDrawer from './components/WorkflowDrawer'
import ActivityRail from './components/ActivityRail'
import LeftNav from './components/LeftNav'
import WorkflowCodeEditor from './components/WorkflowCodeEditor'
import BottomOutputPanel from './components/BottomOutputPanel'
import { SkillsDrawer, DataSourcesDrawer, RunHistoryDrawer, NodesDrawer } from './components/SectionDrawers'
import { useApplyTheme } from './store/themeStore'
import { useDraftAutosave } from './store/useDraftAutosave'
import { useNodeRegistryStore } from './store/nodeRegistryStore'
import { useStudioSectionStore } from './store/studioSectionStore'
import { useWorkflowStore } from './store/workflowStore'

export default function App() {
  useApplyTheme()
  useDraftAutosave()
  const section = useStudioSectionStore((s) => s.section)
  const setSection = useStudioSectionStore((s) => s.setSection)
  const workspaceView = useWorkflowStore((s) => s.workspaceView)
  const rightPanelMode = useWorkflowStore((s) => s.rightPanelMode)
  const showOutputFooter = rightPanelMode === 'output'

  useEffect(() => {
    const store = useNodeRegistryStore.getState()
    void store.refreshFromBackend({ force: true })
    const intervalId = window.setInterval(() => {
      void useNodeRegistryStore.getState().refreshFromBackend({ silent: true })
    }, 15000)
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        void useNodeRegistryStore.getState().refreshFromBackend({ silent: true })
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => {
      window.clearInterval(intervalId)
      document.removeEventListener('visibilitychange', onVisibility)
    }
  }, [])

  return (
    <div className="relative h-screen overflow-hidden text-[var(--text-0)]">
      <div className="studio-backdrop" aria-hidden>
        <div className="studio-backdrop__wash" />
      </div>
      <div className="relative z-10 flex h-full">
        <LeftNav />
        <div className="flex flex-col flex-1 min-w-0">
          <Topbar />
          <div className="flex flex-col flex-1 min-h-0 overflow-hidden relative">
            <div className="flex flex-1 overflow-hidden relative min-h-0">
              <NodePanel />
              {workspaceView === 'canvas' ? <WorkflowCanvas /> : <WorkflowCodeEditor />}
              <ActivityRail />
              {rightPanelMode !== 'output' ? <RightPanel /> : null}
              <WorkflowDrawer />
              <SkillsDrawer open={section === 'skills'} onClose={() => setSection(null)} />
              <DataSourcesDrawer open={section === 'data'} onClose={() => setSection(null)} />
              <RunHistoryDrawer open={section === 'run-history'} onClose={() => setSection(null)} />
              <NodesDrawer open={section === 'nodes'} onClose={() => setSection(null)} />
            </div>
            {showOutputFooter ? <BottomOutputPanel /> : null}
          </div>
        </div>
      </div>
    </div>
  )
}
