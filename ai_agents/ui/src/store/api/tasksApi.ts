import { baseApi } from './baseApi';
import type {
  Task,
  TaskActivity,
  TaskLink,
  CreateTaskRequest,
  UpdateTaskRequest,
  ListTasksParams,
  ListTasksResponse,
  TaskDetailResponse,
  ListActivityResponse,
  UserSearchResult,
  EntitySearchResult,
  EntityType,
} from '../../types/tasks';

/**
 * Tasks API endpoints using RTK Query
 */
export const tasksApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // List tasks with filters and pagination
    listTasks: builder.query<ListTasksResponse, ListTasksParams>({
      query: (params) => {
        const searchParams = new URLSearchParams();
        
        if (params.statuses) searchParams.set('statuses', params.statuses);
        if (params.types) searchParams.set('types', params.types);
        if (params.assigned_to_user_id) searchParams.set('assigned_to_user_id', params.assigned_to_user_id);
        if (params.overdue !== undefined) searchParams.set('overdue', String(params.overdue));
        if (params.entity_type) searchParams.set('entity_type', params.entity_type);
        if (params.entity_id) searchParams.set('entity_id', params.entity_id);
        if (params.sl_no_lt !== undefined) searchParams.set('sl_no_lt', String(params.sl_no_lt));
        if (params.limit) searchParams.set('limit', String(params.limit));
        
        return `/api/v1/tasks?${searchParams.toString()}`;
      },
      providesTags: ['Tasks'],
    }),

    // Get a single task with links
    getTask: builder.query<TaskDetailResponse, string>({
      query: (taskId) => `/api/v1/tasks/${taskId}`,
      providesTags: (_result, _error, id) => [{ type: 'Tasks', id }],
    }),

    // Create a new task
    createTask: builder.mutation<Task, CreateTaskRequest>({
      query: (body) => ({
        url: '/api/v1/tasks',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Tasks'],
    }),

    // Update a task
    updateTask: builder.mutation<Task, { taskId: string; data: UpdateTaskRequest }>({
      query: ({ taskId, data }) => ({
        url: `/api/v1/tasks/${taskId}`,
        method: 'PATCH',
        body: data,
      }),
      invalidatesTags: (_result, _error, { taskId }) => [
        { type: 'Tasks', id: taskId },
        'Tasks',
      ],
    }),

    // Get task activity log
    getTaskActivity: builder.query<ListActivityResponse, { taskId: string; sl_no_lt?: number; limit?: number }>({
      query: ({ taskId, sl_no_lt, limit }) => {
        const searchParams = new URLSearchParams();
        if (sl_no_lt !== undefined) searchParams.set('sl_no_lt', String(sl_no_lt));
        if (limit) searchParams.set('limit', String(limit));
        
        return `/api/v1/tasks/${taskId}/activity?${searchParams.toString()}`;
      },
      providesTags: (_result, _error, { taskId }) => [{ type: 'Tasks', id: `activity-${taskId}` }],
    }),

    // Search users (for assignee type-ahead)
    searchUsers: builder.query<{ items: UserSearchResult[] }, { query: string; limit?: number }>({
      query: ({ query, limit = 10 }) => `/api/v1/tasks/users/search?query=${encodeURIComponent(query)}&limit=${limit}`,
    }),

    // Search entities (for entity picker type-ahead)
    searchEntities: builder.query<{ items: EntitySearchResult[] }, { entity_type: EntityType; query: string; limit?: number }>({
      query: ({ entity_type, query, limit = 10 }) => 
        `/api/v1/tasks/entities/search?entity_type=${entity_type}&query=${encodeURIComponent(query)}&limit=${limit}`,
    }),
  }),
});

// Export hooks
export const {
  useListTasksQuery,
  useGetTaskQuery,
  useCreateTaskMutation,
  useUpdateTaskMutation,
  useGetTaskActivityQuery,
  useSearchUsersQuery,
  useSearchEntitiesQuery,
} = tasksApi;

// Export lazy queries for infinite scroll / load more
export const {
  useLazyListTasksQuery,
  useLazyGetTaskActivityQuery,
} = tasksApi;
