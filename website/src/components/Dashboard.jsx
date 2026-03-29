import { useState } from 'react'

const MOCK_CONVERSATIONS = [
  {
    id: 'REQ-001',
    category: 'Housing',
    language: 'English',
    date: '2026-03-28',
    status: 'active',
    summary: 'Inquiry about rental assistance programs available in Richmond.',
    email: '[REDACTED]',
    phone: '[REDACTED]'
  },
  {
    id: 'REQ-002',
    category: 'Food Assistance',
    language: 'Spanish',
    date: '2026-03-27',
    status: 'completed',
    summary: 'Questions regarding SNAP benefits and local food pantries.',
    email: '[REDACTED]',
    phone: '[REDACTED]'
  },
  {
    id: 'REQ-003',
    category: 'Immigration Support',
    language: 'English',
    date: '2026-03-27',
    status: 'handed-off',
    summary: 'Request for legal resources and immigrant services referrals.',
    email: '[REDACTED]',
    phone: '[REDACTED]'
  },
  {
    id: 'REQ-004',
    category: 'Healthcare',
    language: 'Spanish',
    date: '2026-03-26',
    status: 'active',
    summary: 'Inquiry about Medicaid enrollment assistance.',
    email: '[REDACTED]',
    phone: '[REDACTED]'
  },
  {
    id: 'REQ-005',
    category: 'Emergency Preparedness',
    language: 'English',
    date: '2026-03-26',
    status: 'completed',
    summary: 'Questions about freezing weather safety and shelter locations.',
    email: '[REDACTED]',
    phone: '[REDACTED]'
  }
]

export default function Dashboard() {
  const [filterCategory, setFilterCategory] = useState('All')
  const [filterLanguage, setFilterLanguage] = useState('All')
  const [expandedRow, setExpandedRow] = useState(null)

  const filtered = MOCK_CONVERSATIONS.filter(conv => {
    const categoryMatch = filterCategory === 'All' || conv.category === filterCategory
    const langMatch = filterLanguage === 'All' || conv.language === filterLanguage
    return categoryMatch && langMatch
  })

  const stats = {
    total: MOCK_CONVERSATIONS.length,
    active: MOCK_CONVERSATIONS.filter(c => c.status === 'active').length,
    completed: MOCK_CONVERSATIONS.filter(c => c.status === 'completed').length,
    handedOff: MOCK_CONVERSATIONS.filter(c => c.status === 'handed-off').length
  }

  const getStatusBadge = (status) => {
    const badges = {
      'active': 'status-active',
      'completed': 'status-completed',
      'handed-off': 'status-assigned'
    }
    const labels = {
      'active': 'ACTIVE',
      'completed': 'COMPLETED',
      'handed-off': 'HANDED OFF'
    }
    return <span className={`status-badge ${badges[status]}`}>{labels[status]}</span>
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Service Requests Dashboard</h1>
        <div className="dashboard-controls">
          <select
            className="filter-select"
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
          >
            <option>All Categories</option>
            <option>Housing</option>
            <option>Food Assistance</option>
            <option>Immigration Support</option>
            <option>Healthcare</option>
            <option>Emergency Preparedness</option>
          </select>
          <select
            className="filter-select"
            value={filterLanguage}
            onChange={(e) => setFilterLanguage(e.target.value)}
          >
            <option>All Languages</option>
            <option>English</option>
            <option>Spanish</option>
          </select>
        </div>
      </div>

      <div className="dashboard-stats">
        <div className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Requests</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.active}</div>
          <div className="stat-label">Active</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.completed}</div>
          <div className="stat-label">Completed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.handedOff}</div>
          <div className="stat-label">Handed Off</div>
        </div>
      </div>

      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Request ID</th>
              <th>Category</th>
              <th>Language</th>
              <th>Date</th>
              <th>Status</th>
              <th>Summary</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(conv => (
              <tr key={conv.id} onClick={() => setExpandedRow(expandedRow === conv.id ? null : conv.id)}>
                <td><strong>{conv.id}</strong></td>
                <td>{conv.category}</td>
                <td>{conv.language}</td>
                <td>{conv.date}</td>
                <td>{getStatusBadge(conv.status)}</td>
                <td>{conv.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filtered.length === 0 && (
        <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
          No requests found matching the selected filters.
        </div>
      )}
    </div>
  )
}
