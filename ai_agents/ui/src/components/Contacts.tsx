import { useState } from 'react';

// Mock data for contacts - replace with actual API data later
const mockContacts = [
  { id: '1', name: 'John Smith', email: 'john.smith@acme.com', company: 'Acme Corp', title: 'VP Engineering', status: 'verified' },
  { id: '2', name: 'Sarah Johnson', email: 'sarah.j@globaltech.io', company: 'Global Tech', title: 'CTO', status: 'verified' },
  { id: '3', name: 'Michael Chen', email: 'mchen@innovate.co', company: 'Innovate Inc', title: 'Director of Sales', status: 'pending' },
  { id: '4', name: 'Emily Davis', email: 'emily.d@nextgen.com', company: 'NextGen Systems', title: 'Head of Product', status: 'verified' },
  { id: '5', name: 'Robert Wilson', email: 'rwilson@dataflow.ai', company: 'DataFlow Analytics', title: 'CEO', status: 'pending' },
];

const statusColors: Record<string, { bg: string; text: string }> = {
  verified: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  pending: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  invalid: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444' },
};

export const Contacts = () => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredContacts = mockContacts.filter(contact =>
    contact.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
    contact.company.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="contacts-container">
      <div className="contacts-card">
        {/* Header */}
        <div className="contacts-header">
          <div>
            <h1 className="contacts-title">Contacts</h1>
            <p className="contacts-subtitle">View and manage contact information</p>
          </div>
          <div className="contacts-search-box">
            <input
              type="text"
              className="contacts-search-input"
              placeholder="Search contacts..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Contacts Table */}
        <div className="contacts-table-wrapper">
          <table className="contacts-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Company</th>
                <th>Title</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredContacts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="empty-state">
                    <div className="empty-state-content">
                      <span className="empty-icon">👤</span>
                      <p>No contacts found</p>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredContacts.map((contact) => (
                  <tr key={contact.id}>
                    <td className="contact-name">{contact.name}</td>
                    <td className="contact-email">{contact.email}</td>
                    <td>{contact.company}</td>
                    <td>{contact.title}</td>
                    <td>
                      <span
                        className="status-badge"
                        style={{
                          backgroundColor: statusColors[contact.status]?.bg,
                          color: statusColors[contact.status]?.text,
                        }}
                      >
                        {contact.status}
                      </span>
                    </td>
                    <td>
                      <button className="action-btn" title="View Details">
                        👁️
                      </button>
                      <button className="action-btn" title="Edit">
                        ✏️
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

