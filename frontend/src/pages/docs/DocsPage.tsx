/**
 * DocsPage - Documentation section matching Railway's aesthetic
 * Light theme, clean typography, hierarchical navigation
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  BookOpen,
  Workflow,
  Zap,
  Database,
  GitBranch,
  FileText,
  ChevronRight,
  ChevronDown,
  Home,
  ArrowRight,
  Search,
  Menu,
  X,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'

interface DocSection {
  id: string
  title: string
  icon: React.ReactNode
  items: DocItem[]
}

interface DocItem {
  id: string
  title: string
  content: string
}

export default function DocsPage() {
  const { section, item } = useParams()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['getting-started']))
  const [searchQuery, setSearchQuery] = useState('')
  const [docs, setDocs] = useState<DocSection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Fetch and parse markdown docs
    fetch(`${import.meta.env.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL}/api/docs`)
      .then(res => res.json())
      .then(data => {
        setDocs(data.sections || getDefaultDocs())
        setLoading(false)
      })
      .catch(() => {
        setDocs(getDefaultDocs())
        setLoading(false)
      })
  }, [])

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const currentSection = docs.find(s => s.id === section)
  const currentItem = currentSection?.items.find(i => i.id === item)

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#FAFAFA', fontFamily: 'Inter, sans-serif' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: sidebarOpen ? 280 : 0,
          borderRight: '1px solid #E5E7EB',
          background: '#FFFFFF',
          overflow: 'hidden',
          transition: 'width 200ms',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Logo */}
        <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid #E5E7EB' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 4 }}>
              <span style={{ fontSize: 18, fontWeight: 600, color: '#111827', letterSpacing: '-0.02em' }}>
                dbSherpa
              </span>
              <span style={{ fontSize: 14, fontWeight: 500, color: '#6B7280' }}>
                Studio
              </span>
            </div>
          </div>
          
          {/* Search */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid #E5E7EB',
              background: '#F9FAFB',
            }}
          >
            <Search size={14} style={{ color: '#9CA3AF' }} />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search docs..."
              style={{
                flex: 1,
                border: 'none',
                background: 'transparent',
                outline: 'none',
                fontSize: 13,
                color: '#111827',
              }}
            />
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ flex: 1, overflowY: 'auto', padding: '12px 8px' }}>
          {/* Home */}
          <button
            onClick={() => navigate('/docs')}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '8px 12px',
              borderRadius: 6,
              border: 'none',
              background: !section ? '#F3F4F6' : 'transparent',
              color: !section ? '#111827' : '#6B7280',
              fontSize: 13.5,
              fontWeight: 500,
              cursor: 'pointer',
              marginBottom: 4,
              transition: 'all 140ms',
            }}
          >
            <Home size={16} />
            <span>Overview</span>
          </button>

          {docs.map(sec => (
            <div key={sec.id} style={{ marginBottom: 4 }}>
              <button
                onClick={() => toggleSection(sec.id)}
                style={{
                  width: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: 10,
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: 'none',
                  background: 'transparent',
                  color: '#374151',
                  fontSize: 13.5,
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 140ms',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {sec.icon}
                  <span>{sec.title}</span>
                </div>
                {expandedSections.has(sec.id) ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
              </button>

              {expandedSections.has(sec.id) && (
                <div style={{ marginLeft: 12, marginTop: 4 }}>
                  {sec.items.map(itm => (
                    <button
                      key={itm.id}
                      onClick={() => navigate(`/docs/${sec.id}/${itm.id}`)}
                      style={{
                        width: '100%',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        padding: '7px 12px',
                        borderRadius: 6,
                        border: 'none',
                        background: section === sec.id && item === itm.id ? '#F3F4F6' : 'transparent',
                        color: section === sec.id && item === itm.id ? '#111827' : '#6B7280',
                        fontSize: 13,
                        fontWeight: section === sec.id && item === itm.id ? 500 : 400,
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 140ms',
                        borderLeft: section === sec.id && item === itm.id ? '2px solid #6366F1' : '2px solid transparent',
                      }}
                    >
                      <ArrowRight size={12} style={{ opacity: 0.5, flexShrink: 0 }} />
                      <span>{itm.title}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>

        {/* Footer */}
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid #E5E7EB',
            fontSize: 11.5,
            color: '#9CA3AF',
          }}
        >
          <a
            href="/dashboard"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              color: '#6366F1',
              textDecoration: 'none',
              fontWeight: 500,
            }}
          >
            ← Back to Studio
          </a>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Header */}
        <header
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '16px 32px',
            borderBottom: '1px solid #E5E7EB',
            background: '#FFFFFF',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              style={{
                width: 32,
                height: 32,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #E5E7EB',
                borderRadius: 6,
                background: 'transparent',
                cursor: 'pointer',
                color: '#6B7280',
              }}
            >
              {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
            
            {currentItem && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#6B7280' }}>
                <span>{currentSection?.title}</span>
                <ChevronRight size={14} />
                <span style={{ color: '#111827', fontWeight: 500 }}>{currentItem.title}</span>
              </div>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <a
              href="https://github.com/sunpratik1772/sherpa-new"
              target="_blank"
              rel="noopener noreferrer"
              style={{
                fontSize: 13,
                color: '#6B7280',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              GitHub
            </a>
          </div>
        </header>

        {/* Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '48px 64px' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#9CA3AF' }}>
              Loading documentation...
            </div>
          ) : !currentItem ? (
            <DocsHome docs={docs} navigate={navigate} />
          ) : (
            <article
              className="docs-content"
              style={{
                maxWidth: 800,
                margin: '0 auto',
              }}
            >
              <h1
                style={{
                  fontSize: 36,
                  fontWeight: 600,
                  color: '#111827',
                  marginBottom: 16,
                  letterSpacing: '-0.025em',
                  lineHeight: 1.2,
                }}
              >
                {currentItem.title}
              </h1>
              <ReactMarkdown
                components={{
                  h2: ({ children }) => (
                    <h2 style={{ fontSize: 24, fontWeight: 600, color: '#111827', marginTop: 32, marginBottom: 12 }}>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 style={{ fontSize: 18, fontWeight: 600, color: '#111827', marginTop: 24, marginBottom: 10 }}>
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p style={{ fontSize: 15, lineHeight: 1.7, color: '#374151', marginBottom: 16 }}>
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul style={{ fontSize: 15, lineHeight: 1.7, color: '#374151', marginBottom: 16, paddingLeft: 24 }}>
                      {children}
                    </ul>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className
                    return isInline ? (
                      <code
                        style={{
                          background: '#F3F4F6',
                          padding: '2px 6px',
                          borderRadius: 4,
                          fontSize: 13.5,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: '#DC2626',
                        }}
                      >
                        {children}
                      </code>
                    ) : (
                      <code
                        style={{
                          display: 'block',
                          background: '#1F2937',
                          color: '#F9FAFB',
                          padding: '16px 20px',
                          borderRadius: 8,
                          fontSize: 13.5,
                          fontFamily: 'JetBrains Mono, monospace',
                          overflowX: 'auto',
                          marginBottom: 16,
                        }}
                      >
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {currentItem.content}
              </ReactMarkdown>
            </article>
          )}
        </div>
      </main>
    </div>
  )
}

function DocsHome({ docs, navigate }: { docs: DocSection[]; navigate: any }) {
  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <h1
        style={{
          fontSize: 48,
          fontWeight: 600,
          color: '#111827',
          marginBottom: 16,
          letterSpacing: '-0.03em',
        }}
      >
        dbSherpa Studio Documentation
      </h1>
      <p style={{ fontSize: 18, lineHeight: 1.6, color: '#6B7280', marginBottom: 48 }}>
        Build intelligent AI workflows visually with dbSherpa Studio. Learn how to create powerful
        automations using our node-based workflow builder.
      </p>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 20,
        }}
      >
        {docs.map(sec => (
          <div
            key={sec.id}
            onClick={() => {
              if (sec.items.length > 0) {
                navigate(`/docs/${sec.id}/${sec.items[0].id}`)
              }
            }}
            style={{
              padding: 24,
              borderRadius: 12,
              border: '1px solid #E5E7EB',
              background: '#FFFFFF',
              cursor: 'pointer',
              transition: 'all 200ms',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#6366F1'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(99, 102, 241, 0.1)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#E5E7EB'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            <div style={{ marginBottom: 12, color: '#6366F1' }}>
              {sec.icon}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: '#111827', marginBottom: 8 }}>
              {sec.title}
            </h3>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: '#6B7280' }}>
              {sec.items.length} article{sec.items.length !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

function getDefaultDocs(): DocSection[] {
  return [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: <Zap size={16} />,
      items: [
        {
          id: 'introduction',
          title: 'Introduction',
          content: `# Welcome to dbSherpa Studio

dbSherpa Studio is a powerful visual workflow automation platform that lets you build intelligent AI-driven workflows without writing code.

## What is dbSherpa Studio?

dbSherpa Studio combines the power of AI with deterministic data processing to create sophisticated automation workflows. Whether you're building surveillance systems, data pipelines, or intelligent agents, dbSherpa provides the tools you need.

## Key Features

- **Visual Workflow Builder**: Drag-and-drop interface for building complex workflows
- **AI-Powered Nodes**: LLM integration for intelligent decision-making
- **Data Processing**: Built-in nodes for data collection, transformation, and analysis
- **Real-time Execution**: Run workflows on-demand or trigger them automatically
- **Template Library**: Pre-built workflows for common use cases

## Getting Started

1. Create a new workflow from the Templates page
2. Add nodes by dragging them onto the canvas
3. Connect nodes to define your workflow logic
4. Configure each node with the required parameters
5. Run your workflow and view the results

Ready to build your first workflow? Check out our [Quick Start Guide](#).`,
        },
        {
          id: 'quick-start',
          title: 'Quick Start Guide',
          content: `# Quick Start Guide

Get up and running with dbSherpa Studio in minutes.

## Step 1: Create Your First Workflow

Navigate to the Templates section and click "New workflow" to start with a blank canvas.

## Step 2: Add Nodes

From the left panel, browse available nodes:
- **Trigger Nodes**: Start your workflow (ALERT_TRIGGER, TIME_WINDOW)
- **Collector Nodes**: Fetch data (EXECUTION_DATA_COLLECTOR, MARKET_DATA_COLLECTOR)
- **Transform Nodes**: Process data (FEATURE_ENGINE, AGGREGATOR_NODE)
- **AI Nodes**: Add intelligence (LLM_PLANNER, LLM_CRITIC, LLM_EVALUATOR)
- **Output Nodes**: Generate results (REPORT_OUTPUT, SECTION_SUMMARY)

## Step 3: Connect Nodes

Click and drag from one node's output to another node's input to create connections.

## Step 4: Configure Nodes

Click on any node to open its configuration panel. Fill in required fields based on your use case.

## Step 5: Run Your Workflow

Click the "Run" button in the top toolbar to execute your workflow. View results in real-time.

## Example: Simple Data Pipeline

\`\`\`
ALERT_TRIGGER → EXECUTION_DATA_COLLECTOR → FEATURE_ENGINE → REPORT_OUTPUT
\`\`\`

This creates a basic pipeline that collects execution data, transforms it, and generates a report.`,
        },
      ],
    },
    {
      id: 'workflows',
      title: 'Workflows',
      icon: <Workflow size={16} />,
      items: [
        {
          id: 'workflow-basics',
          title: 'Workflow Basics',
          content: `# Workflow Basics

Learn the fundamentals of building workflows in dbSherpa Studio.

## What is a Workflow?

A workflow is a directed acyclic graph (DAG) of connected nodes that processes data step by step. Each node performs a specific task, and the connections define how data flows through your automation.

## Workflow Components

### Nodes
Individual processing units that perform specific tasks:
- **Trigger Nodes**: Start workflow execution
- **Data Nodes**: Collect or transform data
- **AI Nodes**: Make intelligent decisions
- **Output Nodes**: Generate artifacts and reports

### Connections
Edges that define data flow between nodes. Data flows from parent nodes to child nodes.

### Context
The shared state that passes between nodes. Each node can read from and write to the context.

## Best Practices

1. **Start with a clear goal**: Know what you want to achieve
2. **Keep it modular**: Break complex logic into smaller nodes
3. **Validate data**: Use validator nodes after critical steps
4. **Handle errors**: Add error handling nodes for robustness
5. **Test incrementally**: Run and verify each section before expanding

## Workflow Lifecycle

1. **Design**: Build your workflow visually
2. **Configure**: Set parameters for each node
3. **Validate**: Check for errors and missing connections
4. **Execute**: Run the workflow
5. **Monitor**: Track execution and results
6. **Iterate**: Refine based on outcomes`,
        },
        {
          id: 'agentic-patterns',
          title: 'Agentic Workflow Patterns',
          content: `# Agentic Workflow Patterns

Build intelligent, self-improving workflows using AI agents.

## Core Principle

\`\`\`
LLM nodes decide, critique, evaluate, or synthesize.
Helper/data nodes validate, execute, transform, aggregate, guard, and write artifacts.
\`\`\`

## Recommended Pattern

For high-value agentic workflows:

\`\`\`
ALERT_TRIGGER
→ deterministic data collection
→ LLM_PLANNER
→ PLAN_VALIDATOR
→ LLM_ACTION
→ ACTION_VALIDATOR
→ GUARDRAIL
→ TOOL_EXECUTOR
→ DATA_REDUCER
→ LLM_CRITIC
→ STATE_MANAGER
→ LLM_EVALUATOR
→ LOOP_CONTROLLER
→ LLM_SYNTHESIZER
→ REPORT_OUTPUT
\`\`\`

## Key AI Nodes

### LLM_PLANNER
Converts intent into structured plans with steps and dependencies.

### LLM_CRITIC
Evaluates execution results and provides actionable feedback.

### LLM_EVALUATOR
Determines if workflow goals are satisfied.

### LLM_SYNTHESIZER
Creates final artifacts from validated results.

## Example Use Cases

- **Evidence Analysis**: Collect data, analyze for patterns, generate reports
- **Compliance Monitoring**: Detect violations, gather evidence, create alerts
- **Data Quality**: Check completeness, validate accuracy, suggest improvements`,
        },
      ],
    },
    {
      id: 'nodes',
      title: 'Node Library',
      icon: <GitBranch size={16} />,
      items: [
        {
          id: 'node-overview',
          title: 'Node Overview',
          content: `# Node Library Overview

dbSherpa Studio provides a comprehensive library of nodes for building workflows.

## Node Categories

### Trigger Nodes
- **ALERT_TRIGGER**: Start workflow from external alerts
- **TIME_WINDOW**: Define time-based execution windows

### Data Collection Nodes
- **EXECUTION_DATA_COLLECTOR**: Collect trade execution data
- **MARKET_DATA_COLLECTOR**: Fetch market prices and ticks
- **COMMS_COLLECTOR**: Retrieve communication logs
- **ORACLE_DATA_COLLECTOR**: Query warehouse data

### Transform Nodes
- **FEATURE_ENGINE**: Calculate derived features
- **AGGREGATOR_NODE**: Perform aggregations and grouping
- **GROUP_BY**: Split data by dimensions
- **MAP**: Apply operations to each group

### AI/LLM Nodes
- **LLM_PLANNER**: Generate execution plans
- **LLM_ACTION**: Determine next actions
- **LLM_CRITIC**: Evaluate results
- **LLM_EVALUATOR**: Check goal completion
- **LLM_SYNTHESIZER**: Create final output

### Validation Nodes
- **PLAN_VALIDATOR**: Validate LLM plans
- **ACTION_VALIDATOR**: Check action validity
- **GUARDRAIL**: Enforce safety rules

### Control Flow Nodes
- **STATE_MANAGER**: Track iteration state
- **LOOP_CONTROLLER**: Manage retry logic
- **ERROR_HANDLER**: Handle failures

### Output Nodes
- **REPORT_OUTPUT**: Generate Excel reports
- **SECTION_SUMMARY**: Create section summaries
- **CONSOLIDATED_SUMMARY**: Build executive summaries`,
        },
      ],
    },
    {
      id: 'data-sources',
      title: 'Data Sources',
      icon: <Database size={16} />,
      items: [
        {
          id: 'data-sources-overview',
          title: 'Data Sources Overview',
          content: `# Data Sources

Connect to various data sources to power your workflows.

## Available Data Sources

### Trade Data
- **hs_client_order**: Client order records
- **hs_execution**: Trade execution data (must include \`trade_version:1\`)
- **hs_trades**: Consolidated trade data
- **hs_orders_and_executions**: Combined order and execution view

### Market Data
- **EBS**: EBS market prices
- **Mercury**: Mercury tick data

### Communications
- **oculus**: Message logs and keyword hits

### Reference Data
- **oracle_orders**: Reference order data
- **oracle_executions**: Reference execution data

## Data Source Rules

1. **Use exact column names** from the schema
2. **Include required filters** (e.g., \`trade_version:1\` for executions)
3. **Check semantic tags** for column usage hints
4. **Validate data quality** after collection

## Querying Data

Use collector nodes with proper configuration:

\`\`\`
{
  "source": "hs_execution",
  "filters": {
    "trade_version": 1,
    "trade_date": "2024-01-15"
  },
  "columns": ["trade_id", "symbol", "quantity", "price"]
}
\`\`\``,
        },
      ],
    },
  ]
}
