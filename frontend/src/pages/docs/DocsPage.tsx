/**
 * DocsPage - Documentation matching dbSherpa's warm color scheme
 */
import { useState, useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import {
  BookOpen,
  Lightbulb,
  Zap,
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
  icon: string
  items: DocItem[]
}

interface DocItem {
  id: string
  title: string
  content: string
}

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL || ''

export default function DocsPage() {
  const { section, item } = useParams()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['skills', 'getting-started']))
  const [searchQuery, setSearchQuery] = useState('')
  const [docs, setDocs] = useState<DocSection[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/docs`)
      .then(res => res.json())
      .then(data => {
        setDocs(data.sections || [])
        setLoading(false)
      })
      .catch(err => {
        console.error('Failed to load docs:', err)
        setDocs([])
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

  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'lightbulb': return <Lightbulb size={16} />
      case 'zap': return <Zap size={16} />
      default: return <BookOpen size={16} />
    }
  }

  const currentSection = docs.find(s => s.id === section)
  const currentItem = currentSection?.items.find(i => i.id === item)

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0a0908', fontFamily: 'Inter, sans-serif' }}>
      {/* Sidebar */}
      <aside
        style={{
          width: sidebarOpen ? 280 : 0,
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          background: '#121212',
          overflow: 'hidden',
          transition: 'width 200ms',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Logo */}
        <div style={{ padding: '20px 20px 16px', borderBottom: '1px solid rgba(255, 255, 255, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 16 }}>
            <span style={{ fontSize: 18, fontWeight: 600, color: '#F5F3EF', letterSpacing: '-0.02em' }}>
              dbSherpa
            </span>
            <span style={{ fontSize: 14, fontWeight: 500, color: '#9D8C7C' }}>
              Studio
            </span>
          </div>
          
          {/* Search */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid rgba(255, 255, 255, 0.08)',
              background: '#1a1a1a',
            }}
          >
            <Search size={14} style={{ color: '#6B5D4F', flexShrink: 0 }} />
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
                color: '#F5F3EF',
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
              background: !section ? 'rgba(210, 125, 70, 0.15)' : 'transparent',
              color: !section ? '#E89C6B' : '#9D8C7C',
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
                  color: '#B5A594',
                  fontSize: 13.5,
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all 140ms',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  {getIcon(sec.icon)}
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
                        background: section === sec.id && item === itm.id ? 'rgba(210, 125, 70, 0.15)' : 'transparent',
                        color: section === sec.id && item === itm.id ? '#E89C6B' : '#9D8C7C',
                        fontSize: 13,
                        fontWeight: section === sec.id && item === itm.id ? 500 : 400,
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 140ms',
                        borderLeft: section === sec.id && item === itm.id ? '2px solid #D27D46' : '2px solid transparent',
                      }}
                      onMouseEnter={(e) => {
                        if (!(section === sec.id && item === itm.id)) {
                          e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'
                        }
                      }}
                      onMouseLeave={(e) => {
                        if (!(section === sec.id && item === itm.id)) {
                          e.currentTarget.style.background = 'transparent'
                        }
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
            borderTop: '1px solid rgba(255, 255, 255, 0.08)',
            fontSize: 11.5,
            color: '#6B5D4F',
          }}
        >
          <button
            onClick={() => navigate('/dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              color: '#D27D46',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontWeight: 500,
              fontSize: 11.5,
              padding: 0,
              fontFamily: 'inherit',
            }}
          >
            ← Back to Studio
          </button>
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
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            background: '#121212',
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
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: 6,
                background: 'transparent',
                cursor: 'pointer',
                color: '#9D8C7C',
              }}
            >
              {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
            </button>
            
            {currentItem && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#9D8C7C' }}>
                <span>{currentSection?.title}</span>
                <ChevronRight size={14} />
                <span style={{ color: '#F5F3EF', fontWeight: 500 }}>{currentItem.title}</span>
              </div>
            )}
          </div>
        </header>

        {/* Content Area */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '48px 64px', background: '#0a0908' }}>
          {loading ? (
            <div style={{ textAlign: 'center', padding: '48px', color: '#6B5D4F' }}>
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
                  color: '#F5F3EF',
                  marginBottom: 16,
                  letterSpacing: '-0.025em',
                  lineHeight: 1.2,
                }}
              >
                {currentItem.title}
              </h1>
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <h1 style={{ fontSize: 32, fontWeight: 600, color: '#F5F3EF', marginTop: 32, marginBottom: 16, letterSpacing: '-0.02em' }}>
                      {children}
                    </h1>
                  ),
                  h2: ({ children }) => (
                    <h2 style={{ fontSize: 24, fontWeight: 600, color: '#E8DFD8', marginTop: 32, marginBottom: 12 }}>
                      {children}
                    </h2>
                  ),
                  h3: ({ children }) => (
                    <h3 style={{ fontSize: 18, fontWeight: 600, color: '#E8DFD8', marginTop: 24, marginBottom: 10 }}>
                      {children}
                    </h3>
                  ),
                  p: ({ children }) => (
                    <p style={{ fontSize: 15, lineHeight: 1.7, color: '#B5A594', marginBottom: 16 }}>
                      {children}
                    </p>
                  ),
                  ul: ({ children }) => (
                    <ul style={{ fontSize: 15, lineHeight: 1.7, color: '#B5A594', marginBottom: 16, paddingLeft: 24 }}>
                      {children}
                    </ul>
                  ),
                  li: ({ children }) => (
                    <li style={{ marginBottom: 8 }}>
                      {children}
                    </li>
                  ),
                  code: ({ children, className }) => {
                    const isInline = !className
                    return isInline ? (
                      <code
                        style={{
                          background: 'rgba(210, 125, 70, 0.15)',
                          padding: '2px 6px',
                          borderRadius: 4,
                          fontSize: 13.5,
                          fontFamily: 'JetBrains Mono, monospace',
                          color: '#E89C6B',
                        }}
                      >
                        {children}
                      </code>
                    ) : (
                      <code
                        style={{
                          display: 'block',
                          background: '#1a1a1a',
                          color: '#E8DFD8',
                          padding: '16px 20px',
                          borderRadius: 8,
                          fontSize: 13.5,
                          fontFamily: 'JetBrains Mono, monospace',
                          overflowX: 'auto',
                          marginBottom: 16,
                          border: '1px solid rgba(255, 255, 255, 0.08)',
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
  const getIcon = (iconName: string) => {
    switch (iconName) {
      case 'lightbulb': return <Lightbulb size={20} />
      case 'zap': return <Zap size={20} />
      default: return <BookOpen size={20} />
    }
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }}>
      <h1
        style={{
          fontSize: 48,
          fontWeight: 600,
          color: '#F5F3EF',
          marginBottom: 16,
          letterSpacing: '-0.03em',
        }}
      >
        dbSherpa Studio Documentation
      </h1>
      <p style={{ fontSize: 18, lineHeight: 1.6, color: '#9D8C7C', marginBottom: 48 }}>
        Build intelligent AI workflows visually. Learn how to create powerful
        surveillance and data automation workflows using our node-based builder.
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
              border: '1px solid rgba(255, 255, 255, 0.08)',
              background: '#121212',
              cursor: 'pointer',
              transition: 'all 200ms',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#D27D46'
              e.currentTarget.style.background = 'rgba(210, 125, 70, 0.08)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)'
              e.currentTarget.style.background = '#121212'
            }}
          >
            <div style={{ marginBottom: 12, color: '#D27D46' }}>
              {getIcon(sec.icon)}
            </div>
            <h3 style={{ fontSize: 18, fontWeight: 600, color: '#F5F3EF', marginBottom: 8 }}>
              {sec.title}
            </h3>
            <p style={{ fontSize: 14, lineHeight: 1.6, color: '#9D8C7C' }}>
              {sec.items.length} article{sec.items.length !== 1 ? 's' : ''}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
