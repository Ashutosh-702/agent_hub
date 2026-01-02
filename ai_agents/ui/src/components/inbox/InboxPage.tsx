import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { LeadList } from './LeadList';
import { LeadDetail } from './LeadDetail';
import { InboxFilters } from './InboxFilters';
import type { LeadSummary, ListLeadsParams } from '../../types/inbox';
import * as inboxApi from '../../services/inboxApi';
import './InboxPage.css';

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
      <div className="inbox-page inbox-page--mobile">
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
    <div className="inbox-page">
      {/* Header */}
      <div className="inbox-header">
        <div className="inbox-header__top">
          <div>
            <h1 className="inbox-header__title">Inbox</h1>
            <p className="inbox-header__subtitle">
              Unified view of all outreach conversations
            </p>
          </div>
          <div className="inbox-header__actions">
            <span className="inbox-header__count">
              {total} lead{total !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Tabs */}
        <div className="inbox-tabs">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`inbox-tabs__tab ${activeTab === tab.id ? 'inbox-tabs__tab--active' : ''}`}
            >
              {tab.label}
              {tab.id === 'attention' && leads.filter(l => (l.attentionReasons?.length || 0) > 0).length > 0 && (
                <span className="inbox-tabs__badge">
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

      {/* Split Pane Container */}
      <div className="inbox-split">
        {/* Lead List - Left Pane */}
        <div className="inbox-split__left">
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

        {/* Lead Detail - Right Pane */}
        {!isMobile && (
          <div className="inbox-split__right">
            {selectedLeadId ? (
              <LeadDetail
                leadId={selectedLeadId}
                onUpdate={handleLeadUpdate}
              />
            ) : (
              <div className="inbox-empty-state">
                <div className="inbox-empty-state__icon">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                    <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
                    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
                  </svg>
                </div>
                <p className="inbox-empty-state__title">Select a lead</p>
                <p className="inbox-empty-state__subtitle">
                  Choose a lead from the list to view details and conversation history
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
