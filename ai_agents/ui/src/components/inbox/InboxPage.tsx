import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LeadList } from './LeadList';
import { LeadDetail } from './LeadDetail';
import { InboxFilters } from './InboxFilters';
import type { LeadSummary, ListLeadsParams } from '../../types/inbox';
import * as inboxApi from '../../services/inboxApi';

type TabType = 'all' | 'attention' | 'sequence';

const TABS: { id: TabType; label: string }[] = [
  { id: 'all', label: 'All Leads' },
  { id: 'attention', label: 'Needs Attention' },
  { id: 'sequence', label: 'In Sequence' },
];

export const InboxPage = () => {
  const { leadId } = useParams<{ leadId?: string }>();
  const navigate = useNavigate();

  // State
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [leads, setLeads] = useState<LeadSummary[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<string | null>(leadId || null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  // Filters
  const [filters, setFilters] = useState<ListLeadsParams>({
    tab: 'all',
    sort: 'recent',
  });

  // Responsive handling
  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Sync URL with selected lead
  useEffect(() => {
    if (leadId && leadId !== selectedLeadId) {
      setSelectedLeadId(leadId);
    }
  }, [leadId]);

  // Fetch leads
  const fetchLeads = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await inboxApi.listLeads({
        ...filters,
        tab: activeTab,
      });
      setLeads(response.leads);
      setTotal(response.total);

      // Auto-select first lead if none selected (desktop only)
      if (!selectedLeadId && response.leads.length > 0 && !isMobile) {
        setSelectedLeadId(response.leads[0].leadId);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load leads');
    } finally {
      setIsLoading(false);
    }
  }, [filters, activeTab, isMobile]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  // Handle lead selection
  const handleSelectLead = (lead: LeadSummary) => {
    setSelectedLeadId(lead.leadId);
    if (isMobile) {
      navigate(`/inbox/${lead.leadId}`);
    }
  };

  // Handle back (mobile)
  const handleBack = () => {
    setSelectedLeadId(null);
    navigate('/inbox');
  };

  // Handle tab change
  const handleTabChange = (tab: TabType) => {
    setActiveTab(tab);
    setSelectedLeadId(null);
  };

  // Handle filter change
  const handleFilterChange = (newFilters: Partial<ListLeadsParams>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  // Handle lead update (refetch list)
  const handleLeadUpdate = () => {
    fetchLeads();
  };

  // Mobile: Show detail view when lead is selected
  if (isMobile && selectedLeadId) {
    return (
      <div style={{ 
        height: '100%', 
        display: 'flex', 
        flexDirection: 'column',
        background: 'var(--color-gray-50)',
      }}>
        <LeadDetail
          leadId={selectedLeadId}
          onBack={handleBack}
          onUpdate={handleLeadUpdate}
          isMobile={true}
        />
      </div>
    );
  }

  return (
    <div style={{
      height: '100%',
      display: 'flex',
      flexDirection: 'column',
      background: 'var(--color-gray-50)',
      overflow: 'hidden',
    }}>
      {/* Header */}
      <div style={{
        padding: '1.5rem 2rem 0',
        background: 'var(--color-white)',
        borderBottom: '1px solid var(--color-gray-200)',
        flexShrink: 0,
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '1.25rem',
        }}>
          <div>
            <h1 style={{
              fontSize: '1.75rem',
              fontWeight: 700,
              color: 'var(--color-gray-900)',
              margin: 0,
              marginBottom: '0.25rem',
            }}>
              Inbox
            </h1>
            <p style={{
              fontSize: '0.9375rem',
              color: 'var(--color-gray-500)',
              margin: 0,
            }}>
              Unified view of all outreach conversations
            </p>
          </div>
          <div style={{ 
            display: 'flex', 
            gap: '1rem', 
            alignItems: 'center',
          }}>
            <span style={{
              padding: '0.5rem 1rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              background: 'var(--color-gray-100)',
              color: 'var(--color-gray-700)',
              borderRadius: '8px',
            }}>
              {total} lead{total !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div style={{
          display: 'flex',
          gap: '0.5rem',
        }}>
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              style={{
                padding: '0.875rem 1.5rem',
                fontSize: '0.9375rem',
                fontWeight: 600,
                color: activeTab === tab.id ? 'var(--color-primary)' : 'var(--color-gray-500)',
                background: activeTab === tab.id ? 'var(--color-primary-lighter)' : 'transparent',
                border: 'none',
                borderBottom: activeTab === tab.id ? '3px solid var(--color-primary)' : '3px solid transparent',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                marginBottom: '-1px',
                borderRadius: '8px 8px 0 0',
              }}
            >
              {tab.label}
              {tab.id === 'attention' && leads.filter(l => (l.attentionReasons?.length || 0) > 0).length > 0 && (
                <span style={{
                  marginLeft: '0.625rem',
                  padding: '0.1875rem 0.5rem',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  background: 'var(--color-error)',
                  color: 'white',
                  borderRadius: '10px',
                }}>
                  {leads.filter(l => (l.attentionReasons?.length || 0) > 0).length}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Filters */}
      <InboxFilters
        filters={filters}
        onChange={handleFilterChange}
        activeTab={activeTab}
      />

      {/* Split Pane */}
      <div style={{
        flex: 1,
        display: 'flex',
        overflow: 'hidden',
        minHeight: 0,
      }}>
        {/* Lead List */}
        <div style={{
          width: isMobile ? '100%' : '420px',
          minWidth: isMobile ? '100%' : '380px',
          maxWidth: isMobile ? '100%' : '500px',
          borderRight: isMobile ? 'none' : '1px solid var(--color-gray-200)',
          background: 'var(--color-white)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}>
          <LeadList
            leads={leads}
            selectedLeadId={selectedLeadId}
            onSelectLead={handleSelectLead}
            isLoading={isLoading}
            error={error}
            onRetry={fetchLeads}
            activeTab={activeTab}
          />
        </div>

        {/* Lead Detail (desktop only) */}
        {!isMobile && (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            minWidth: 0,
          }}>
            {selectedLeadId ? (
              <LeadDetail
                leadId={selectedLeadId}
                onUpdate={handleLeadUpdate}
              />
            ) : (
              <div style={{
                flex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'var(--color-gray-50)',
              }}>
                <div style={{
                  textAlign: 'center',
                  color: 'var(--color-gray-400)',
                  padding: '3rem',
                }}>
                  <div style={{
                    width: '80px',
                    height: '80px',
                    margin: '0 auto 1.5rem',
                    borderRadius: '50%',
                    background: 'var(--color-gray-100)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ opacity: 0.4 }}>
                      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
                      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                    </svg>
                  </div>
                  <p style={{ 
                    fontSize: '1.125rem', 
                    fontWeight: 600,
                    color: 'var(--color-gray-600)',
                    marginBottom: '0.5rem',
                  }}>
                    Select a lead
                  </p>
                  <p style={{ 
                    fontSize: '0.9375rem',
                    color: 'var(--color-gray-400)',
                  }}>
                    Choose a lead from the list to view details and conversation history
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
