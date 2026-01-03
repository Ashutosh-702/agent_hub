import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader, StatusBadge } from '../shared';

interface Meeting {
  id: string;
  meeting_id: string;
  meeting_name?: string;
  company_domain?: string;
  status: 'scheduled' | 'prep' | 'live' | 'completed';
  scheduled_at?: string;
  ended_at?: string;
  product_ids: string[];
}

// Mock meetings for testing
const MOCK_MEETINGS: Meeting[] = [
  {
    id: 'm1',
    meeting_id: 'meeting-uuid-1',
    meeting_name: 'Discovery Call - Acme Retail',
    company_domain: 'acme-retail.com',
    status: 'completed',
    ended_at: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    product_ids: ['Fynd OMS', 'Fynd WMS'],
  },
  {
    id: 'm2',
    meeting_id: 'meeting-uuid-2',
    meeting_name: 'Product Demo - TechStart Inc',
    company_domain: 'techstart.io',
    status: 'completed',
    ended_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    product_ids: ['Fynd Platform'],
  },
  {
    id: 'm3',
    meeting_id: 'meeting-uuid-3',
    meeting_name: 'Follow-up - Fashion Hub',
    company_domain: 'fashionhub.in',
    status: 'scheduled',
    scheduled_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    product_ids: ['Fynd Storefront', 'PixelBin'],
  },
];

interface MeetingHistoryProps {
  limit?: number;
  showFilters?: boolean;
}

export const MeetingHistory = ({ limit, showFilters = true }: MeetingHistoryProps) => {
  const navigate = useNavigate();
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  
  useEffect(() => {
    // Try to fetch from API, fall back to mock data
    fetch('/api/v1/meetings')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.data.meetings?.length > 0) {
          setMeetings(data.data.meetings);
        } else {
          setMeetings(MOCK_MEETINGS);
        }
      })
      .catch(() => {
        setMeetings(MOCK_MEETINGS);
      })
      .finally(() => setIsLoading(false));
  }, []);
  
  const filteredMeetings = meetings
    .filter(m => filter === 'all' || m.status === filter)
    .slice(0, limit);
  
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  const getStatusType = (status: string): 'info' | 'warning' | 'success' | 'default' => {
    const typeMap: Record<string, 'info' | 'warning' | 'success' | 'default'> = {
      scheduled: 'info',
      prep: 'info',
      live: 'warning',
      completed: 'success',
    };
    return typeMap[status] || 'default';
  };
  
  const handleMeetingClick = (meeting: Meeting) => {
    switch (meeting.status) {
      case 'completed':
        navigate(`/client-calls/reflections/${meeting.id}`);
        break;
      case 'scheduled':
      case 'prep':
        navigate(`/client-calls/battlecard/${meeting.id}`);
        break;
      case 'live':
        navigate(`/client-calls/live/${meeting.meeting_id}`);
        break;
      default:
        navigate(`/client-calls/reflections/${meeting.id}`);
    }
  };
  
  if (isLoading) {
    return <Loader size="small" text="Loading meetings..." />;
  }
  
  return (
    <div>
      {/* Filter Tabs */}
      {showFilters && (
        <div className="confidence-selector" style={{ marginBottom: '1rem' }}>
          {['all', 'scheduled', 'completed'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`confidence-btn ${filter === f ? 'selected' : ''}`}
              style={{ textTransform: 'capitalize' }}
            >
              {f}
            </button>
          ))}
        </div>
      )}
      
      {filteredMeetings.length === 0 ? (
        <div className="insights-empty">
          <div className="insights-empty-icon">📅</div>
          <p>No meetings found</p>
        </div>
      ) : (
        <div className="reflections-list" style={{ gap: '0.75rem' }}>
          {filteredMeetings.map((meeting) => (
            <div
              key={meeting.id}
              className="reflection-meeting-card"
              onClick={() => handleMeetingClick(meeting)}
              style={{ padding: '1rem' }}
            >
              <div className="reflection-card-header" style={{ marginBottom: 0 }}>
                <div>
                  <h3 className="reflection-card-title" style={{ fontSize: 'var(--text-base)' }}>
                    {meeting.meeting_name || meeting.company_domain || 'Untitled Meeting'}
                  </h3>
                  <p className="reflection-card-date">
                    {meeting.status === 'completed' 
                      ? formatDate(meeting.ended_at)
                      : formatDate(meeting.scheduled_at)
                    }
                    {meeting.product_ids.length > 0 && ` • ${meeting.product_ids.slice(0, 2).join(', ')}`}
                    {meeting.product_ids.length > 2 && ` +${meeting.product_ids.length - 2}`}
                  </p>
                </div>
                <StatusBadge status={meeting.status} type={getStatusType(meeting.status)} />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
