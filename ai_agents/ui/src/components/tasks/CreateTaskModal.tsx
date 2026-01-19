import { useState, useCallback } from 'react';
import Select from 'react-select';
import {
  useCreateTaskMutation,
  useSearchUsersQuery,
  useSearchEntitiesQuery,
} from '../../store/api/tasksApi';
import type { EntityType, Priority, CreateTaskRequest } from '../../types/tasks';
import { TASK_TYPE_CONFIG, PRIORITY_CONFIG } from '../../types/tasks';
import { istLocalInputToUTC } from '../../utils/dateUtils';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
  // Optional: pre-fill entity
  defaultEntityType?: EntityType;
  defaultEntityId?: string;
}

const ENTITY_TYPE_OPTIONS = [
  { value: 'contact' as EntityType, label: 'Contact' },
  { value: 'company' as EntityType, label: 'Company' },
  { value: 'deal' as EntityType, label: 'Deal' },
];

const TASK_TYPE_OPTIONS = Object.entries(TASK_TYPE_CONFIG).map(([value, config]) => ({
  value,
  label: `${config.icon} ${config.label}`,
}));

const PRIORITY_OPTIONS = Object.entries(PRIORITY_CONFIG).map(([value, config]) => ({
  value: parseInt(value) as Priority,
  label: config.label,
}));

/**
 * Modal for creating a new task
 */
export function CreateTaskModal({
  isOpen,
  onClose,
  onCreated,
  defaultEntityType,
  defaultEntityId,
}: CreateTaskModalProps) {
  // Form state
  const [entityType, setEntityType] = useState<EntityType | null>(defaultEntityType || null);
  const [entityId, setEntityId] = useState<string | null>(defaultEntityId || null);
  const [entityName, setEntityName] = useState<string | null>(null); // Store selected entity name
  const [taskType, setTaskType] = useState<string>('call');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<Priority>(3);
  const [dueAt, setDueAt] = useState('');
  const [assigneeId, setAssigneeId] = useState<string | null>(null);
  const [assigneeName, setAssigneeName] = useState<string | null>(null); // Store selected assignee name
  
  // Search queries
  const [entitySearch, setEntitySearch] = useState('');
  const [assigneeSearch, setAssigneeSearch] = useState('');
  
  // API hooks
  const [createTask, { isLoading }] = useCreateTaskMutation();
  
  const { data: entitiesData } = useSearchEntitiesQuery(
    { entity_type: entityType!, query: entitySearch, limit: 10 },
    { skip: !entityType || !entitySearch || entitySearch.length < 1 }
  );
  
  const { data: usersData } = useSearchUsersQuery(
    { query: assigneeSearch, limit: 10 },
    { skip: !assigneeSearch || assigneeSearch.length < 1 }
  );
  
  // Handle form submit
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!entityType || !entityId) {
      return;
    }
    
    const request: CreateTaskRequest = {
      primary_entity_type: entityType,
      primary_entity_id: entityId,
      type: taskType,
      title: title || undefined,
      description: description || undefined,
      priority,
      due_at: dueAt ? istLocalInputToUTC(dueAt) : undefined,
      assigned_to_user_id: assigneeId || undefined,
    };
    
    try {
      await createTask(request).unwrap();
      onCreated();
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  }, [entityType, entityId, taskType, title, description, priority, dueAt, assigneeId, createTask, onCreated]);
  
  // Reset form
  const handleClose = useCallback(() => {
    setEntityType(defaultEntityType || null);
    setEntityId(defaultEntityId || null);
    setEntityName(null);
    setTaskType('call');
    setTitle('');
    setDescription('');
    setPriority(3);
    setDueAt('');
    setAssigneeId(null);
    setAssigneeName(null);
    onClose();
  }, [defaultEntityType, defaultEntityId, onClose]);

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div style={styles.backdrop} onClick={handleClose} />
      
      {/* Modal */}
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>Create Task</h2>
          <button onClick={handleClose} style={styles.closeButton}>
            ✕
          </button>
        </div>
        
        <form onSubmit={handleSubmit} style={styles.form}>
          {/* Entity Type */}
          <div style={styles.field}>
            <label style={styles.label}>Link to *</label>
            <Select
              options={ENTITY_TYPE_OPTIONS}
              value={ENTITY_TYPE_OPTIONS.find(o => o.value === entityType)}
              onChange={(selected) => {
                setEntityType(selected?.value || null);
                setEntityId(null);
                setEntitySearch('');
              }}
              placeholder="Select entity type..."
              styles={selectStyles}
            />
          </div>
          
          {/* Entity Search */}
          {entityType && (
            <div style={styles.field}>
              <label style={styles.label}>Select {entityType} *</label>
              <Select
                options={entitiesData?.items.map(e => ({
                  value: e.id,
                  label: e.name + (e.email ? ` (${e.email})` : ''),
                })) || []}
                value={entityId && entityName ? { value: entityId, label: entityName } : null}
                onInputChange={(value) => setEntitySearch(value)}
                onChange={(selected) => {
                  setEntityId(selected?.value || null);
                  setEntityName(selected?.label || null);
                }}
                placeholder={`Search ${entityType}s...`}
                styles={selectStyles}
                noOptionsMessage={() => 
                  entitySearch.length < 1 
                    ? 'Type to search...' 
                    : 'No results found'
                }
              />
            </div>
          )}
          
          {/* Task Type */}
          <div style={styles.field}>
            <label style={styles.label}>Task Type *</label>
            <Select
              options={TASK_TYPE_OPTIONS}
              value={TASK_TYPE_OPTIONS.find(o => o.value === taskType)}
              onChange={(selected) => setTaskType(selected?.value || 'call')}
              styles={selectStyles}
            />
          </div>
          
          {/* Title */}
          <div style={styles.field}>
            <label style={styles.label}>Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Optional task title"
              style={styles.input}
            />
          </div>
          
          {/* Priority */}
          <div style={styles.field}>
            <label style={styles.label}>Priority</label>
            <Select
              options={PRIORITY_OPTIONS}
              value={PRIORITY_OPTIONS.find(o => o.value === priority)}
              onChange={(selected) => setPriority(selected?.value || 3)}
              styles={selectStyles}
            />
          </div>
          
          {/* Due Date */}
          <div style={styles.field}>
            <label style={styles.label}>Due Date</label>
            <div style={styles.dateTimeContainer}>
              <input
                type="datetime-local"
                value={dueAt}
                onChange={(e) => setDueAt(e.target.value)}
                style={styles.input}
              />
              {dueAt && (
                <button
                  type="button"
                  onClick={() => setDueAt('')}
                  style={styles.clearDateButton}
                  title="Clear date"
                >
                  ✕
                </button>
              )}
            </div>
            <p style={styles.hint}>Leave empty to use default SLA for task type</p>
          </div>
          
          {/* Assignee */}
          <div style={styles.field}>
            <label style={styles.label}>Assignee</label>
            <Select
              options={usersData?.items.map(u => ({
                value: u.id,
                label: u.name || u.email || u.id,
              })) || []}
              value={assigneeId && assigneeName ? { value: assigneeId, label: assigneeName } : null}
              onInputChange={(value) => setAssigneeSearch(value)}
              onChange={(selected) => {
                setAssigneeId(selected?.value || null);
                setAssigneeName(selected?.label || null);
              }}
              placeholder="Search for user..."
              isClearable
              styles={selectStyles}
              noOptionsMessage={() => 
                assigneeSearch.length < 1 
                  ? 'Type to search...' 
                  : 'No users found'
              }
            />
            <p style={styles.hint}>Leave empty to auto-assign based on entity owner</p>
          </div>
          
          {/* Description */}
          <div style={styles.field}>
            <label style={styles.label}>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description"
              rows={3}
              style={styles.textarea}
            />
          </div>
          
          {/* Actions */}
          <div style={styles.actions}>
            <button type="button" onClick={handleClose} style={styles.cancelButton}>
              Cancel
            </button>
            <button
              type="submit"
              disabled={!entityType || !entityId || isLoading}
              style={{
                ...styles.submitButton,
                opacity: (!entityType || !entityId || isLoading) ? 0.6 : 1,
              }}
            >
              {isLoading ? 'Creating...' : 'Create Task'}
            </button>
          </div>
        </form>
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
    backgroundColor: 'rgba(0, 0, 0, 0.4)',
    zIndex: 999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  modal: {
    position: 'fixed',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '500px',
    maxWidth: '90%',
    maxHeight: '90vh',
    backgroundColor: 'white',
    borderRadius: '12px',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.2)',
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
  form: {
    padding: '24px',
    overflow: 'auto',
  },
  field: {
    marginBottom: '20px',
  },
  label: {
    display: 'block',
    fontSize: '13px',
    fontWeight: 500,
    color: '#374151',
    marginBottom: '6px',
  },
  input: {
    width: '100%',
    padding: '10px 12px',
    fontSize: '14px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    outline: 'none',
    boxSizing: 'border-box',
  },
  dateTimeContainer: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  clearDateButton: {
    position: 'absolute',
    right: '8px',
    background: 'none',
    border: 'none',
    fontSize: '16px',
    color: '#64748b',
    cursor: 'pointer',
    padding: '4px 8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
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
    boxSizing: 'border-box',
  },
  hint: {
    fontSize: '12px',
    color: '#94a3b8',
    marginTop: '4px',
    marginBottom: 0,
  },
  actions: {
    display: 'flex',
    justifyContent: 'flex-end',
    gap: '12px',
    marginTop: '24px',
  },
  cancelButton: {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: 500,
    borderRadius: '8px',
    border: '1px solid #e2e8f0',
    backgroundColor: 'white',
    color: '#475569',
    cursor: 'pointer',
  },
  submitButton: {
    padding: '10px 24px',
    fontSize: '14px',
    fontWeight: 500,
    borderRadius: '8px',
    border: 'none',
    backgroundColor: '#6366f1',
    color: 'white',
    cursor: 'pointer',
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
