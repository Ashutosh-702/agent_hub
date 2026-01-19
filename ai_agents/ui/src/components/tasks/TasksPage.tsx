import { useState, useCallback } from 'react';
import Select from 'react-select';
import { TasksTable } from './TasksTable';
import { TaskDrawer } from './TaskDrawer';
import { CreateTaskModal } from './CreateTaskModal';
import { useListTasksQuery } from '../../store/api/tasksApi';
import type { Task, TaskStatus, ListTasksParams } from '../../types/tasks';
import { TASK_STATUS_CONFIG, TASK_TYPE_CONFIG } from '../../types/tasks';

// Filter options
const STATUS_OPTIONS = Object.entries(TASK_STATUS_CONFIG).map(([value, config]) => ({
  value,
  label: config.label,
}));

const TYPE_OPTIONS = Object.entries(TASK_TYPE_CONFIG).map(([value, config]) => ({
  value,
  label: `${config.icon} ${config.label}`,
}));

/**
 * Tasks Inbox Page
 * Main page for viewing and managing tasks
 */
export function TasksPage() {
  // Filter state
  const [selectedStatuses, setSelectedStatuses] = useState<string[]>(['open', 'in_progress']);
  const [selectedTypes, setSelectedTypes] = useState<string[]>([]);
  const [overdueOnly, setOverdueOnly] = useState(false);
  
  // Pagination state
  const [cursor, setCursor] = useState<number | undefined>(undefined);
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  
  // Modal/drawer state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  
  // Build query params
  const queryParams: ListTasksParams = {
    statuses: selectedStatuses.length > 0 ? selectedStatuses.join(',') : undefined,
    types: selectedTypes.length > 0 ? selectedTypes.join(',') : undefined,
    overdue: overdueOnly || undefined,
    sl_no_lt: cursor,
    limit: 50,
  };
  
  const { data, isLoading, isFetching, refetch } = useListTasksQuery(queryParams);
  
  // Merge new data with existing (for load more)
  const tasks = cursor ? [...allTasks, ...(data?.items || [])] : (data?.items || []);
  const hasMore = data?.next?.sl_no_lt !== null;
  
  // Handle load more
  const handleLoadMore = useCallback(() => {
    if (data?.next?.sl_no_lt) {
      setAllTasks(tasks);
      setCursor(data.next.sl_no_lt);
    }
  }, [data?.next?.sl_no_lt, tasks]);
  
  // Handle filter change - reset pagination
  const handleFilterChange = useCallback(() => {
    setCursor(undefined);
    setAllTasks([]);
  }, []);
  
  // Handle task click
  const handleTaskClick = useCallback((task: Task) => {
    setSelectedTaskId(task.id);
  }, []);
  
  // Handle task created
  const handleTaskCreated = useCallback(() => {
    setIsCreateModalOpen(false);
    handleFilterChange();
    refetch();
  }, [handleFilterChange, refetch]);

  return (
    <div className="tasks-page" style={styles.container}>
      {/* Header */}
      <div style={styles.header}>
        <h1 style={styles.title}>Tasks</h1>
        <button 
          onClick={() => setIsCreateModalOpen(true)}
          style={styles.createButton}
        >
          + Create Task
        </button>
      </div>
      
      {/* Filters */}
      <div style={styles.filters}>
        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Status</label>
          <Select
            isMulti
            options={STATUS_OPTIONS}
            value={STATUS_OPTIONS.filter(o => selectedStatuses.includes(o.value))}
            onChange={(selected) => {
              setSelectedStatuses(selected?.map(s => s.value) || []);
              handleFilterChange();
            }}
            placeholder="Filter by status..."
            styles={selectStyles}
          />
        </div>
        
        <div style={styles.filterGroup}>
          <label style={styles.filterLabel}>Type</label>
          <Select
            isMulti
            options={TYPE_OPTIONS}
            value={TYPE_OPTIONS.filter(o => selectedTypes.includes(o.value))}
            onChange={(selected) => {
              setSelectedTypes(selected?.map(s => s.value) || []);
              handleFilterChange();
            }}
            placeholder="Filter by type..."
            styles={selectStyles}
          />
        </div>
        
        <div style={styles.filterGroup}>
          <label style={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={overdueOnly}
              onChange={(e) => {
                setOverdueOnly(e.target.checked);
                handleFilterChange();
              }}
            />
            <span style={{ marginLeft: 8 }}>Overdue only</span>
          </label>
        </div>
      </div>
      
      {/* Tasks Table */}
      <TasksTable
        tasks={tasks}
        isLoading={isLoading && !cursor}
        isFetchingMore={isFetching && !!cursor}
        hasMore={hasMore}
        onLoadMore={handleLoadMore}
        onTaskClick={handleTaskClick}
      />
      
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
        />
      )}
    </div>
  );
}

// Styles
const styles: Record<string, React.CSSProperties> = {
  container: {
    padding: '24px',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '24px',
  },
  title: {
    fontSize: '28px',
    fontWeight: 600,
    color: '#1a1a2e',
    margin: 0,
  },
  createButton: {
    backgroundColor: '#6366f1',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'background-color 0.2s',
  },
  filters: {
    display: 'flex',
    gap: '16px',
    marginBottom: '24px',
    flexWrap: 'wrap' as const,
    alignItems: 'flex-end',
  },
  filterGroup: {
    minWidth: '200px',
  },
  filterLabel: {
    display: 'block',
    fontSize: '12px',
    fontWeight: 500,
    color: '#64748b',
    marginBottom: '6px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    fontSize: '14px',
    color: '#334155',
    cursor: 'pointer',
    padding: '10px 0',
  },
};

const selectStyles = {
  control: (base: any) => ({
    ...base,
    borderColor: '#e2e8f0',
    '&:hover': { borderColor: '#cbd5e1' },
    minHeight: '38px',
  }),
  multiValue: (base: any) => ({
    ...base,
    backgroundColor: '#f1f5f9',
  }),
};
