import { useState, useCallback } from 'react';
import { useListTasksQuery } from '../../store/api/tasksApi';
import { TaskDrawer } from './TaskDrawer';
import { CreateTaskModal } from './CreateTaskModal';
import type { Task, EntityType } from '../../types/tasks';
import { TASK_STATUS_CONFIG, TASK_TYPE_CONFIG } from '../../types/tasks';

interface EntityTasksWidgetProps {
  entityType: EntityType;
  entityId: string;
  title?: string;
  maxHeight?: string;
}

/**
 * Embeddable widget showing tasks linked to an entity
 * For use on Company, Contact, and Deal detail pages
 */
export function EntityTasksWidget({
  entityType,
  entityId,
  title = 'Tasks',
  maxHeight = '400px',
}: EntityTasksWidgetProps) {
  // Pagination state
  const [cursor, setCursor] = useState<number | undefined>(undefined);
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  
  // Modal/drawer state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  
  const { data, isLoading, isFetching, refetch } = useListTasksQuery({
    entity_type: entityType,
    entity_id: entityId,
    sl_no_lt: cursor,
    limit: 10,
  });
  
  // Merge tasks for pagination
  const tasks = cursor 
    ? [...allTasks, ...(data?.items || [])] 
    : (data?.items || []);
  
  const hasMore = data?.next?.sl_no_lt !== null;
  
  // Handle load more
  const handleLoadMore = useCallback(() => {
    if (data?.next?.sl_no_lt) {
      setAllTasks(tasks);
      setCursor(data.next.sl_no_lt);
    }
  }, [data?.next?.sl_no_lt, tasks]);
  
  // Handle task created
  const handleTaskCreated = useCallback(() => {
    setIsCreateModalOpen(false);
    setCursor(undefined);
    setAllTasks([]);
    refetch();
  }, [refetch]);

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h3 style={styles.title}>{title}</h3>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          style={styles.addButton}
        >
          + Add
        </button>
      </div>
      
      {/* Content */}
      <div style={{ ...styles.content, maxHeight }}>
        {isLoading ? (
          <div style={styles.loading}>Loading tasks...</div>
        ) : tasks.length === 0 ? (
          <div style={styles.empty}>
            <p>No tasks linked to this {entityType}</p>
            <button
              onClick={() => setIsCreateModalOpen(true)}
              style={styles.createFirstButton}
            >
              Create first task
            </button>
          </div>
        ) : (
          <>
            <div style={styles.list}>
              {tasks.map((task) => (
                <TaskItem
                  key={task.id}
                  task={task}
                  onClick={() => setSelectedTaskId(task.id)}
                />
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
                {isFetching ? 'Loading...' : 'Load more'}
              </button>
            )}
          </>
        )}
      </div>
      
      {/* Task Drawer */}
      {selectedTaskId && (
        <TaskDrawer
          taskId={selectedTaskId}
          isOpen={!!selectedTaskId}
          onClose={() => setSelectedTaskId(null)}
          onUpdate={() => refetch()}
        />
      )}
      
      {/* Create Task Modal */}
      {isCreateModalOpen && (
        <CreateTaskModal
          isOpen={isCreateModalOpen}
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={handleTaskCreated}
          defaultEntityType={entityType}
          defaultEntityId={entityId}
        />
      )}
    </div>
  );
}

interface TaskItemProps {
  task: Task;
  onClick: () => void;
}

function TaskItem({ task, onClick }: TaskItemProps) {
  const statusConfig = TASK_STATUS_CONFIG[task.status];
  const typeConfig = TASK_TYPE_CONFIG[task.type] || TASK_TYPE_CONFIG.custom;
  
  return (
    <div
      onClick={onClick}
      style={styles.item}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = '#f8fafc';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = 'transparent';
      }}
    >
      <div style={styles.itemIcon}>{typeConfig.icon}</div>
      <div style={styles.itemContent}>
        <div style={styles.itemTitle}>
          {task.title || `${typeConfig.label} task`}
        </div>
        <div style={styles.itemMeta}>
          <span
            style={{
              ...styles.statusDot,
              backgroundColor: statusConfig.color,
            }}
          />
          <span style={styles.statusLabel}>{statusConfig.label}</span>
          {task.is_overdue && (
            <span style={styles.overdueLabel}>Overdue</span>
          )}
        </div>
      </div>
      <div style={styles.itemArrow}>→</div>
    </div>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    backgroundColor: 'white',
    borderRadius: '8px',
    border: '1px solid #e2e8f0',
    overflow: 'hidden',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '12px 16px',
    borderBottom: '1px solid #e2e8f0',
    backgroundColor: '#f8fafc',
  },
  title: {
    fontSize: '14px',
    fontWeight: 600,
    color: '#1e293b',
    margin: 0,
  },
  addButton: {
    padding: '4px 12px',
    fontSize: '12px',
    fontWeight: 500,
    borderRadius: '4px',
    border: 'none',
    backgroundColor: '#6366f1',
    color: 'white',
    cursor: 'pointer',
  },
  content: {
    overflow: 'auto',
  },
  loading: {
    padding: '32px',
    textAlign: 'center',
    color: '#64748b',
    fontSize: '13px',
  },
  empty: {
    padding: '32px',
    textAlign: 'center',
    color: '#94a3b8',
  },
  createFirstButton: {
    marginTop: '12px',
    padding: '8px 16px',
    fontSize: '13px',
    borderRadius: '6px',
    border: '1px solid #e2e8f0',
    backgroundColor: 'white',
    color: '#475569',
    cursor: 'pointer',
  },
  list: {
    display: 'flex',
    flexDirection: 'column',
  },
  item: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    borderBottom: '1px solid #f1f5f9',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  itemIcon: {
    fontSize: '16px',
  },
  itemContent: {
    flex: 1,
    minWidth: 0,
  },
  itemTitle: {
    fontSize: '13px',
    fontWeight: 500,
    color: '#1e293b',
    marginBottom: '4px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  itemMeta: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  statusDot: {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
  },
  statusLabel: {
    fontSize: '11px',
    color: '#64748b',
  },
  overdueLabel: {
    fontSize: '10px',
    fontWeight: 500,
    color: '#ef4444',
    backgroundColor: '#fef2f2',
    padding: '2px 6px',
    borderRadius: '4px',
  },
  itemArrow: {
    color: '#94a3b8',
    fontSize: '12px',
  },
  loadMoreButton: {
    display: 'block',
    width: '100%',
    padding: '10px',
    fontSize: '12px',
    fontWeight: 500,
    border: 'none',
    borderTop: '1px solid #f1f5f9',
    backgroundColor: '#f8fafc',
    color: '#475569',
    cursor: 'pointer',
  },
};
