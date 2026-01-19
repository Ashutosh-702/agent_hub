/**
 * Task Management System TypeScript types
 */

// Task statuses
export type TaskStatus = 'open' | 'in_progress' | 'done' | 'snoozed' | 'cancelled';

// Task types
export type TaskType = 'call' | 'followup_email' | 'reply_email' | 'data_clean' | 'custom';

// Entity types that tasks can be linked to
export type EntityType = 'contact' | 'company' | 'deal';

// Link reasons
export type LinkReason = 'primary' | 'derived_company';

// Activity event types
export type TaskEventType = 'created' | 'updated' | 'status_changed' | 'assigned' | 'snoozed' | 'completed' | 'reopened';

// Priority levels (1 = highest, 5 = lowest)
export type Priority = 1 | 2 | 3 | 4 | 5;

/**
 * Brief entity info
 */
export interface EntityBrief {
  id: string;
  type: EntityType;
  name?: string;
  email?: string;
}

/**
 * Brief user info
 */
export interface UserBrief {
  id: string;
  name?: string;
  email?: string;
}

/**
 * Task link (association to an entity)
 */
export interface TaskLink {
  entity_type: EntityType;
  entity_id: string;
  entity_name?: string;
  link_reason: LinkReason;
}

/**
 * Main Task interface
 */
export interface Task {
  id: string;
  sl_no: number;
  primary_entity_type: EntityType;
  primary_entity_id: string;
  type: string;
  status: TaskStatus;
  priority: Priority;
  due_at?: string;
  snoozed_until?: string;
  completed_at?: string;
  assigned_to_user_id?: string;
  owner_user_id?: string;
  created_by_user_id?: string;
  title?: string;
  description?: string;
  source?: string;
  source_ref?: string;
  context_json?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  
  // Computed fields
  effective_due_at?: string;
  is_overdue: boolean;
  
  // Optional enriched data
  primary_entity?: EntityBrief;
  assigned_to?: UserBrief;
  links?: TaskLink[];
}

/**
 * Task activity entry
 */
export interface TaskActivity {
  id: string;
  sl_no: number;
  task_id: string;
  at: string;
  actor_user_id?: string;
  event_type: TaskEventType;
  diff_json: {
    before?: Record<string, unknown>;
    after?: Record<string, unknown>;
  };
  
  // Optional enriched data
  actor?: UserBrief;
}

/**
 * Pagination cursor
 */
export interface PaginatedNext {
  sl_no_lt: number | null;
}

/**
 * Create task request
 */
export interface CreateTaskRequest {
  primary_entity_type: EntityType;
  primary_entity_id: string;
  type: string;
  title?: string;
  description?: string;
  due_at?: string;
  priority?: Priority;
  assigned_to_user_id?: string;
}

/**
 * Update task request
 */
export interface UpdateTaskRequest {
  status?: TaskStatus;
  priority?: Priority;
  due_at?: string;
  snoozed_until?: string;
  assigned_to_user_id?: string;
  title?: string;
  description?: string;
}

/**
 * List tasks parameters
 */
export interface ListTasksParams {
  statuses?: string; // Comma-separated
  types?: string; // Comma-separated
  assigned_to_user_id?: string;
  overdue?: boolean;
  entity_type?: EntityType;
  entity_id?: string;
  sl_no_lt?: number;
  limit?: number;
}

/**
 * List tasks response
 */
export interface ListTasksResponse {
  items: Task[];
  next: PaginatedNext;
}

/**
 * Task detail response (with links)
 */
export interface TaskDetailResponse {
  task: Task;
  links: TaskLink[];
}

/**
 * List activity response
 */
export interface ListActivityResponse {
  items: TaskActivity[];
  next: PaginatedNext;
}

/**
 * User search result
 */
export interface UserSearchResult {
  id: string;
  email?: string;
  name?: string;
}

/**
 * Entity search result
 */
export interface EntitySearchResult {
  id: string;
  type: EntityType;
  name: string;
  email?: string;
}

/**
 * Task status display info
 */
export const TASK_STATUS_CONFIG: Record<TaskStatus, { label: string; color: string }> = {
  open: { label: 'Open', color: '#2196f3' },
  in_progress: { label: 'In Progress', color: '#ff9800' },
  done: { label: 'Done', color: '#4caf50' },
  snoozed: { label: 'Snoozed', color: '#9e9e9e' },
  cancelled: { label: 'Cancelled', color: '#f44336' },
};

/**
 * Task type display info
 */
export const TASK_TYPE_CONFIG: Record<string, { label: string; icon: string }> = {
  call: { label: 'Call', icon: '📞' },
  followup_email: { label: 'Follow-up Email', icon: '📧' },
  reply_email: { label: 'Reply Email', icon: '↩️' },
  data_clean: { label: 'Data Clean', icon: '🧹' },
  custom: { label: 'Custom', icon: '📝' },
};

/**
 * Priority display info
 */
export const PRIORITY_CONFIG: Record<Priority, { label: string; color: string }> = {
  1: { label: 'Urgent', color: '#f44336' },
  2: { label: 'High', color: '#ff9800' },
  3: { label: 'Medium', color: '#2196f3' },
  4: { label: 'Low', color: '#9e9e9e' },
  5: { label: 'Lowest', color: '#bdbdbd' },
};
