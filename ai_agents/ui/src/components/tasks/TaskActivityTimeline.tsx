import { useState, useCallback } from 'react';
import { useGetTaskActivityQuery } from '../../store/api/tasksApi';
import type { TaskActivity, TaskEventType, TaskStatus, Priority } from '../../types/tasks';
import { TASK_STATUS_CONFIG, PRIORITY_CONFIG } from '../../types/tasks';
import { formatDateIST, formatDateShortIST } from '../../utils/dateUtils';

interface TaskActivityTimelineProps {
  taskId: string;
}

const EVENT_CONFIG: Record<TaskEventType, { label: string; icon: string }> = {
  created: { label: 'Created', icon: '➕' },
  updated: { label: 'Updated', icon: '✏️' },
  status_changed: { label: 'Status changed', icon: '🔄' },
  assigned: { label: 'Assigned', icon: '👤' },
  snoozed: { label: 'Snoozed', icon: '⏰' },
  completed: { label: 'Completed', icon: '✅' },
  reopened: { label: 'Reopened', icon: '🔓' },
};

/**
 * Paginated activity timeline for a task
 */
export function TaskActivityTimeline({ taskId }: TaskActivityTimelineProps) {
  const [cursor, setCursor] = useState<number | undefined>(undefined);
  const [allActivities, setAllActivities] = useState<TaskActivity[]>([]);
  
  const { data, isLoading, isFetching } = useGetTaskActivityQuery({
    taskId,
    sl_no_lt: cursor,
    limit: 20,
  });
  
  // Merge activities
  const activities = cursor 
    ? [...allActivities, ...(data?.items || [])] 
    : (data?.items || []);
  
  const hasMore = data?.next?.sl_no_lt !== null;
  
  // Handle load more
  const handleLoadMore = useCallback(() => {
    if (data?.next?.sl_no_lt) {
      setAllActivities(activities);
      setCursor(data.next.sl_no_lt);
    }
  }, [data?.next?.sl_no_lt, activities]);

  if (isLoading && !cursor) {
    return <div style={styles.loading}>Loading activity...</div>;
  }

  if (activities.length === 0) {
    return <div style={styles.empty}>No activity yet</div>;
  }

  return (
    <div style={styles.container}>
      <div style={styles.timeline}>
        {activities.map((activity, idx) => (
          <ActivityItem key={activity.id} activity={activity} isLast={idx === activities.length - 1} />
        ))}
      </div>
      
      {hasMore && (
        <button
          onClick={handleLoadMore}
          disabled={isFetching}
          style={{
            ...styles.loadMoreButton,
            opacity: isFetching ? 0.6 : 1,
          }}
        >
          {isFetching ? 'Loading...' : 'Load more activity'}
        </button>
      )}
    </div>
  );
}

interface ActivityItemProps {
  activity: TaskActivity;
  isLast: boolean;
}

function ActivityItem({ activity, isLast }: ActivityItemProps) {
  const config = EVENT_CONFIG[activity.event_type] || { label: activity.event_type, icon: '📝' };
  
  // Format field name for display
  const formatFieldName = (key: string): string => {
    const fieldNames: Record<string, string> = {
      status: 'Status',
      priority: 'Priority',
      assigned_to_user_id: 'Assigned to',
      due_at: 'Due date',
      snoozed_until: 'Snoozed until',
      title: 'Title',
      description: 'Description',
      completed_at: 'Completed at',
    };
    return fieldNames[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };
  
  // Format value for display
  const formatValue = (key: string, val: unknown): string => {
    if (val === null || val === undefined) return '—';
    
    // Format status
    if (key === 'status' && typeof val === 'string') {
      return TASK_STATUS_CONFIG[val as TaskStatus]?.label || val;
    }
    
    // Format priority
    if (key === 'priority' && typeof val === 'number') {
      return PRIORITY_CONFIG[val as Priority]?.label || `Priority ${val}`;
    }
    
    // Format dates
    if ((key === 'due_at' || key === 'snoozed_until' || key === 'completed_at') && typeof val === 'string') {
      return formatDateIST(val);
    }
    
    // Format user IDs (show truncated if no name available)
    if (key === 'assigned_to_user_id' && typeof val === 'string') {
      return val.slice(0, 8) + '...';
    }
    
    // Format strings (truncate if too long)
    if (typeof val === 'string') {
      if (val.length > 50) {
        return val.slice(0, 50) + '...';
      }
      return val;
    }
    
    // Format other types
    if (typeof val === 'object') {
      return JSON.stringify(val).slice(0, 50);
    }
    
    return String(val);
  };
  
  // Format diff
  const formatDiff = (diff: Record<string, unknown>) => {
    const changes: Array<{ field: string; oldVal: string; newVal: string }> = [];
    
    const before = diff.before as Record<string, unknown> | undefined;
    const after = diff.after as Record<string, unknown> | undefined;
    
    if (before && after) {
      // Get all keys from both before and after
      const allKeys = new Set([...Object.keys(before), ...Object.keys(after)]);
      
      allKeys.forEach(key => {
        const oldVal = before[key];
        const newVal = after[key];
        
        // Only show if value actually changed
        if (oldVal !== newVal) {
          changes.push({
            field: formatFieldName(key),
            oldVal: formatValue(key, oldVal),
            newVal: formatValue(key, newVal),
          });
        }
      });
    } else if (after) {
      // Created event - show initial values
      Object.entries(after).forEach(([key, value]) => {
        if (value !== null && value !== undefined && key !== 'id' && key !== 'sl_no' && key !== 'created_at' && key !== 'updated_at') {
          changes.push({
            field: formatFieldName(key),
            oldVal: '—',
            newVal: formatValue(key, value),
          });
        }
      });
    }
    
    return changes.slice(0, 10); // Show max 10 changes
  };
  
  const formattedTime = formatDateShortIST(activity.at);
  
  const changes = formatDiff(activity.diff_json);

  return (
    <div style={styles.item}>
      {/* Timeline connector */}
      <div style={styles.connector}>
        <div style={styles.dot}>{config.icon}</div>
        {!isLast && <div style={styles.line} />}
      </div>
      
      {/* Content */}
      <div style={styles.content}>
        <div style={styles.header}>
          <span style={styles.eventLabel}>{config.label}</span>
          <span style={styles.time}>{formattedTime}</span>
        </div>
        
        {activity.actor?.name && (
          <div style={styles.actor}>
            by {activity.actor.name}
          </div>
        )}
        
        {changes.length > 0 && (
          <div style={styles.changes}>
            {changes.map((change, idx) => (
              <div key={idx} style={styles.change}>
                <span style={styles.changeField}>{change.field}:</span>{' '}
                <span style={styles.changeOld}>{change.oldVal}</span>
                {' → '}
                <span style={styles.changeNew}>{change.newVal}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
  },
  loading: {
    padding: '16px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
  empty: {
    padding: '16px',
    textAlign: 'center',
    color: '#94a3b8',
    fontSize: '13px',
  },
  timeline: {
    display: 'flex',
    flexDirection: 'column',
  },
  item: {
    display: 'flex',
    gap: '12px',
  },
  connector: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    width: '24px',
  },
  dot: {
    fontSize: '12px',
    width: '24px',
    height: '24px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f1f5f9',
    borderRadius: '50%',
  },
  line: {
    flex: 1,
    width: '2px',
    backgroundColor: '#e2e8f0',
    minHeight: '20px',
  },
  content: {
    flex: 1,
    paddingBottom: '16px',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '4px',
  },
  eventLabel: {
    fontSize: '13px',
    fontWeight: 500,
    color: '#1e293b',
  },
  time: {
    fontSize: '11px',
    color: '#94a3b8',
  },
  actor: {
    fontSize: '12px',
    color: '#64748b',
    marginBottom: '8px',
  },
  changes: {
    backgroundColor: '#f8fafc',
    borderRadius: '6px',
    padding: '8px 10px',
  },
  change: {
    fontSize: '12px',
    color: '#475569',
    marginBottom: '6px',
    lineHeight: '1.5',
  },
  changeField: {
    fontWeight: 500,
    color: '#1e293b',
  },
  changeOld: {
    color: '#ef4444',
    textDecoration: 'line-through',
  },
  changeNew: {
    color: '#10b981',
    fontWeight: 500,
  },
  loadMoreButton: {
    marginTop: '12px',
    padding: '8px 16px',
    fontSize: '12px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    backgroundColor: 'white',
    color: '#475569',
    cursor: 'pointer',
    alignSelf: 'center',
  },
};
