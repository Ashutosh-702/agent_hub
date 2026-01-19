import { useMemo } from 'react';
import type { Task } from '../../types/tasks';
import { TASK_STATUS_CONFIG, TASK_TYPE_CONFIG, PRIORITY_CONFIG } from '../../types/tasks';
import { formatDateOnlyIST } from '../../utils/dateUtils';

interface TasksTableProps {
  tasks: Task[];
  isLoading: boolean;
  isFetchingMore: boolean;
  hasMore: boolean;
  onLoadMore: () => void;
  onTaskClick: (task: Task) => void;
}

/**
 * Tasks table with load more pagination
 */
export function TasksTable({
  tasks,
  isLoading,
  isFetchingMore,
  hasMore,
  onLoadMore,
  onTaskClick,
}: TasksTableProps) {
  if (isLoading) {
    return (
      <div style={styles.loadingContainer}>
        <div style={styles.spinner} />
        <p>Loading tasks...</p>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div style={styles.emptyState}>
        <div style={styles.emptyIcon}>✓</div>
        <h3 style={styles.emptyTitle}>No tasks found</h3>
        <p style={styles.emptyText}>
          Create a task or adjust your filters to see results.
        </p>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.th}>Task</th>
            <th style={styles.th}>Type</th>
            <th style={styles.th}>Status</th>
            <th style={styles.th}>Priority</th>
            <th style={styles.th}>Due</th>
            <th style={styles.th}>Assignee</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((task) => (
            <TaskRow key={task.id} task={task} onClick={() => onTaskClick(task)} />
          ))}
        </tbody>
      </table>
      
      {/* Load More */}
      {hasMore && (
        <div style={styles.loadMoreContainer}>
          <button
            onClick={onLoadMore}
            disabled={isFetchingMore}
            style={{
              ...styles.loadMoreButton,
              opacity: isFetchingMore ? 0.6 : 1,
            }}
          >
            {isFetchingMore ? 'Loading...' : 'Load more tasks'}
          </button>
        </div>
      )}
    </div>
  );
}

interface TaskRowProps {
  task: Task;
  onClick: () => void;
}

function TaskRow({ task, onClick }: TaskRowProps) {
  const statusConfig = TASK_STATUS_CONFIG[task.status];
  const typeConfig = TASK_TYPE_CONFIG[task.type] || TASK_TYPE_CONFIG.custom;
  const priorityConfig = PRIORITY_CONFIG[task.priority];
  
  const formattedDue = useMemo(() => {
    if (!task.effective_due_at) return '—';
    const date = new Date(task.effective_due_at);
    const now = new Date();
    const diffMs = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return `${Math.abs(diffDays)}d overdue`;
    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Tomorrow';
    if (diffDays < 7) return `${diffDays} days`;
    return formatDateOnlyIST(task.effective_due_at);
  }, [task.effective_due_at]);

  return (
    <tr
      onClick={onClick}
      style={styles.tr}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#f8fafc';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      <td style={styles.td}>
        <div style={styles.taskTitle}>
          {task.title || `${typeConfig.label} task`}
        </div>
        <div style={styles.taskMeta}>
          {task.primary_entity_type}: {task.primary_entity?.name || task.primary_entity_id.slice(0, 8) + '...'}
        </div>
      </td>
      <td style={styles.td}>
        <span style={styles.typeLabel}>
          {typeConfig.icon} {typeConfig.label}
        </span>
      </td>
      <td style={styles.td}>
        <span
          style={{
            ...styles.statusBadge,
            backgroundColor: `${statusConfig.color}15`,
            color: statusConfig.color,
          }}
        >
          {statusConfig.label}
        </span>
      </td>
      <td style={styles.td}>
        <span
          style={{
            ...styles.priorityDot,
            backgroundColor: priorityConfig.color,
          }}
          title={priorityConfig.label}
        />
      </td>
      <td style={{
        ...styles.td,
        color: task.is_overdue ? '#ef4444' : '#64748b',
        fontWeight: task.is_overdue ? 500 : 400,
      }}>
        {formattedDue}
      </td>
      <td style={styles.td}>
        {task.assigned_to_user_id ? (
          <span style={styles.assignee}>
            {task.assigned_to?.name || task.assigned_to?.email || task.assigned_to_user_id.slice(0, 8) + '...'}
          </span>
        ) : (
          <span style={styles.unassigned}>Unassigned</span>
        )}
      </td>
    </tr>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
    overflow: 'hidden',
  },
  loadingContainer: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '48px',
    color: '#64748b',
  },
  spinner: {
    width: '32px',
    height: '32px',
    border: '3px solid #e2e8f0',
    borderTopColor: '#6366f1',
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    marginBottom: '16px',
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '64px',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  },
  emptyIcon: {
    fontSize: '48px',
    marginBottom: '16px',
    color: '#4ade80',
  },
  emptyTitle: {
    fontSize: '18px',
    fontWeight: 500,
    color: '#1e293b',
    margin: '0 0 8px',
  },
  emptyText: {
    fontSize: '14px',
    color: '#64748b',
    margin: 0,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '12px 16px',
    fontSize: '12px',
    fontWeight: 500,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc',
  },
  tr: {
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  td: {
    padding: '16px',
    borderBottom: '1px solid #f1f5f9',
    fontSize: '14px',
    color: '#334155',
  },
  taskTitle: {
    fontWeight: 500,
    color: '#1e293b',
    marginBottom: '4px',
  },
  taskMeta: {
    fontSize: '12px',
    color: '#94a3b8',
  },
  typeLabel: {
    fontSize: '13px',
    color: '#64748b',
  },
  statusBadge: {
    padding: '4px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 500,
  },
  priorityDot: {
    display: 'inline-block',
    width: '10px',
    height: '10px',
    borderRadius: '50%',
  },
  assignee: {
    fontSize: '13px',
    color: '#475569',
  },
  unassigned: {
    fontSize: '13px',
    color: '#94a3b8',
    fontStyle: 'italic',
  },
  loadMoreContainer: {
    display: 'flex',
    justifyContent: 'center',
    padding: '20px',
    borderTop: '1px solid #f1f5f9',
  },
  loadMoreButton: {
    backgroundColor: '#f8fafc',
    color: '#475569',
    border: '1px solid #e2e8f0',
    borderRadius: '8px',
    padding: '10px 24px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
};
