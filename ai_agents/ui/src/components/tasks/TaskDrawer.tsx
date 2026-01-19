import { useState, useCallback } from 'react';
import Select from 'react-select';
import { useGetTaskQuery, useUpdateTaskMutation, useSearchUsersQuery } from '../../store/api/tasksApi';
import { TaskActivityTimeline } from './TaskActivityTimeline';
import type { TaskStatus, Priority, UpdateTaskRequest } from '../../types/tasks';
import { TASK_STATUS_CONFIG, TASK_TYPE_CONFIG, PRIORITY_CONFIG } from '../../types/tasks';
import { formatDateIST, utcToISTLocalInput, istLocalInputToUTC } from '../../utils/dateUtils';

interface TaskDrawerProps {
  taskId: string;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const STATUS_OPTIONS = Object.entries(TASK_STATUS_CONFIG).map(([value, config]) => ({
  value: value as TaskStatus,
  label: config.label,
}));

const PRIORITY_OPTIONS = Object.entries(PRIORITY_CONFIG).map(([value, config]) => ({
  value: parseInt(value) as Priority,
  label: config.label,
}));

/**
 * Task detail drawer (slide-out panel)
 */
export function TaskDrawer({ taskId, isOpen, onClose, onUpdate }: TaskDrawerProps) {
  const { data: taskDetail, isLoading, refetch } = useGetTaskQuery(taskId);
  const [updateTask] = useUpdateTaskMutation();
  
  // Local editing state
  const [editingField, setEditingField] = useState<string | null>(null);
  const [assigneeSearch, setAssigneeSearch] = useState('');
  
  // User search for assignee
  const { data: usersData } = useSearchUsersQuery(
    { query: assigneeSearch, limit: 10 },
    { skip: !assigneeSearch || assigneeSearch.length < 1 }
  );
  
  const task = taskDetail?.task;
  const links = taskDetail?.links || [];
  
  // Handle field update
  const handleUpdate = useCallback(async (updates: UpdateTaskRequest) => {
    try {
      await updateTask({ taskId, data: updates }).unwrap();
      refetch();
      onUpdate();
      setEditingField(null);
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  }, [taskId, updateTask, refetch, onUpdate]);
  
  // Handle snooze
  const handleSnooze = useCallback(async (hours: number) => {
    const snoozedUntil = new Date();
    snoozedUntil.setHours(snoozedUntil.getHours() + hours);
    
    await handleUpdate({
      status: 'snoozed',
      snoozed_until: snoozedUntil.toISOString(),
    });
  }, [handleUpdate]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div style={styles.backdrop} onClick={onClose} />
      
      {/* Drawer */}
      <div style={styles.drawer}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>Task Details</h2>
          <button onClick={onClose} style={styles.closeButton}>
            ✕
          </button>
        </div>
        
        {isLoading ? (
          <div style={styles.loading}>Loading...</div>
        ) : task ? (
          <div style={styles.content}>
            {/* Task Title */}
            <div style={styles.section}>
              <label style={styles.label}>Title</label>
              {editingField === 'title' ? (
                <input
                  type="text"
                  defaultValue={task.title || ''}
                  style={styles.input}
                  autoFocus
                  onBlur={(e) => handleUpdate({ title: e.target.value })}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleUpdate({ title: e.currentTarget.value });
                    if (e.key === 'Escape') setEditingField(null);
                  }}
                />
              ) : (
                <div
                  style={styles.editableValue}
                  onClick={() => setEditingField('title')}
                >
                  {task.title || `${TASK_TYPE_CONFIG[task.type]?.label || task.type} task`}
                </div>
              )}
            </div>
            
            {/* Type (read-only) */}
            <div style={styles.section}>
              <label style={styles.label}>Type</label>
              <div style={styles.value}>
                {TASK_TYPE_CONFIG[task.type]?.icon} {TASK_TYPE_CONFIG[task.type]?.label || task.type}
              </div>
            </div>
            
            {/* Status */}
            <div style={styles.section}>
              <label style={styles.label}>Status</label>
              <Select
                options={STATUS_OPTIONS}
                value={STATUS_OPTIONS.find(o => o.value === task.status)}
                onChange={(selected) => {
                  if (selected) handleUpdate({ status: selected.value });
                }}
                styles={selectStyles}
              />
            </div>
            
            {/* Priority */}
            <div style={styles.section}>
              <label style={styles.label}>Priority</label>
              <Select
                options={PRIORITY_OPTIONS}
                value={PRIORITY_OPTIONS.find(o => o.value === task.priority)}
                onChange={(selected) => {
                  if (selected) handleUpdate({ priority: selected.value });
                }}
                styles={selectStyles}
              />
            </div>
            
            {/* Assignee */}
            <div style={styles.section}>
              <label style={styles.label}>Assignee</label>
              <Select
                options={usersData?.items.map(u => ({
                  value: u.id,
                  label: u.name || u.email || u.id,
                })) || []}
                value={task.assigned_to_user_id ? {
                  value: task.assigned_to_user_id,
                  label: task.assigned_to?.name || task.assigned_to?.email || task.assigned_to_user_id,
                } : null}
                onInputChange={(value) => setAssigneeSearch(value)}
                onChange={(selected) => {
                  handleUpdate({ assigned_to_user_id: selected?.value });
                }}
                placeholder="Search for user..."
                isClearable
                styles={selectStyles}
              />
            </div>
            
            {/* Due Date */}
            <div style={styles.section}>
              <label style={styles.label}>Due Date</label>
              <input
                type="datetime-local"
                value={utcToISTLocalInput(task.due_at)}
                onChange={(e) => {
                  const date = e.target.value ? istLocalInputToUTC(e.target.value) : undefined;
                  handleUpdate({ due_at: date });
                }}
                style={styles.input}
              />
              {task.is_overdue && (
                <span style={styles.overdueLabel}>Overdue!</span>
              )}
            </div>
            
            {/* Snooze Actions */}
            {task.status !== 'done' && task.status !== 'cancelled' && (
              <div style={styles.section}>
                <label style={styles.label}>Snooze</label>
                <div style={styles.snoozeButtons}>
                  <button onClick={() => handleSnooze(1)} style={styles.snoozeButton}>1h</button>
                  <button onClick={() => handleSnooze(4)} style={styles.snoozeButton}>4h</button>
                  <button onClick={() => handleSnooze(24)} style={styles.snoozeButton}>1d</button>
                  <button onClick={() => handleSnooze(72)} style={styles.snoozeButton}>3d</button>
                </div>
              </div>
            )}
            
            {/* Description */}
            <div style={styles.section}>
              <label style={styles.label}>Description</label>
              {editingField === 'description' ? (
                <textarea
                  defaultValue={task.description || ''}
                  style={styles.textarea}
                  rows={4}
                  autoFocus
                  onBlur={(e) => handleUpdate({ description: e.target.value })}
                />
              ) : (
                <div
                  style={styles.editableValue}
                  onClick={() => setEditingField('description')}
                >
                  {task.description || 'Add a description...'}
                </div>
              )}
            </div>
            
            {/* Links */}
            <div style={styles.section}>
              <label style={styles.label}>Linked Entities</label>
              <div style={styles.links}>
                {links.map((link, idx) => (
                  <div key={idx} style={styles.linkItem}>
                    <span style={styles.linkType}>{link.entity_type}</span>
                    <span style={styles.linkId}>
                      {link.entity_name || link.entity_id.slice(0, 12) + '...'}
                    </span>
                    <span style={styles.linkReason}>({link.link_reason})</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Metadata */}
            <div style={styles.section}>
              <label style={styles.label}>Metadata</label>
              <div style={styles.meta}>
                <div>Created: {formatDateIST(task.created_at)}</div>
                <div>Updated: {formatDateIST(task.updated_at)}</div>
                {task.source && <div>Source: {task.source}</div>}
              </div>
            </div>
            
            {/* Activity Timeline */}
            <div style={styles.section}>
              <label style={styles.label}>Activity</label>
              <TaskActivityTimeline taskId={taskId} />
            </div>
          </div>
        ) : (
          <div style={styles.error}>Task not found</div>
        )}
      </div>
    </>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    zIndex: 999,
  },
  drawer: {
    position: 'fixed',
    top: 0,
    right: 0,
    bottom: 0,
    width: '480px',
    maxWidth: '100%',
    backgroundColor: 'white',
    boxShadow: '-4px 0 24px rgba(0, 0, 0, 0.15)',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '20px 24px',
    borderBottom: '1px solid #e2e8f0',
  },
  title: {
    fontSize: '18px',
    fontWeight: 600,
    color: '#1e293b',
    margin: 0,
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '20px',
    color: '#64748b',
    cursor: 'pointer',
    padding: '4px 8px',
  },
  content: {
    flex: 1,
    overflow: 'auto',
    padding: '24px',
  },
  loading: {
    padding: '48px',
    textAlign: 'center',
    color: '#64748b',
  },
  error: {
    padding: '48px',
    textAlign: 'center',
    color: '#ef4444',
  },
  section: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    fontSize: '12px',
    fontWeight: 500,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    marginBottom: '8px',
  },
  value: {
    fontSize: '14px',
    color: '#1e293b',
  },
  editableValue: {
    fontSize: '14px',
    color: '#1e293b',
    padding: '8px 12px',
    borderRadius: '6px',
    backgroundColor: '#f8fafc',
    cursor: 'pointer',
    border: '1px solid transparent',
    transition: 'border-color 0.2s',
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    fontSize: '14px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    outline: 'none',
  },
  textarea: {
    width: '100%',
    padding: '10px 12px',
    fontSize: '14px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    outline: 'none',
    resize: 'vertical',
    fontFamily: 'inherit',
  },
  overdueLabel: {
    display: 'inline-block',
    marginTop: '8px',
    fontSize: '12px',
    fontWeight: 500,
    color: '#ef4444',
  },
  snoozeButtons: {
    display: 'flex',
    gap: '8px',
  },
  snoozeButton: {
    padding: '6px 16px',
    fontSize: '13px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc',
    cursor: 'pointer',
    transition: 'all 0.2s',
  },
  links: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
  },
  linkItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
    padding: '8px 12px',
    backgroundColor: '#f8fafc',
    borderRadius: '6px',
  },
  linkType: {
    fontWeight: 500,
    color: '#1e293b',
    textTransform: 'capitalize',
  },
  linkId: {
    color: '#64748b',
    fontFamily: 'monospace',
  },
  linkReason: {
    color: '#94a3b8',
    fontSize: '11px',
  },
  meta: {
    fontSize: '12px',
    color: '#64748b',
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
};

const selectStyles = {
  control: (base: any) => ({
    ...base,
    borderColor: '#e2e8f0',
    '&:hover': { borderColor: '#cbd5e1' },
    minHeight: '38px',
  }),
};
