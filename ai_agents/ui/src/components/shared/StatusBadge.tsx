type StatusType = 'success' | 'warning' | 'error' | 'info' | 'default';

interface StatusBadgeProps {
  status: string;
  type?: StatusType;
}

const statusColors: Record<StatusType, { bg: string; text: string }> = {
  success: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981' },
  warning: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b' },
  error: { bg: 'rgba(239, 68, 68, 0.15)', text: '#ef4444' },
  info: { bg: 'rgba(99, 102, 241, 0.15)', text: '#6366f1' },
  default: { bg: 'rgba(156, 163, 175, 0.15)', text: '#9ca3af' },
};

// Auto-detect type based on status string
const getTypeFromStatus = (status: string): StatusType => {
  const lowerStatus = status.toLowerCase();
  if (['active', 'verified', 'completed', 'success', 'enriched'].includes(lowerStatus)) return 'success';
  if (['pending', 'processing', 'in_progress'].includes(lowerStatus)) return 'warning';
  if (['failed', 'error', 'invalid', 'rejected'].includes(lowerStatus)) return 'error';
  if (['paused', 'draft'].includes(lowerStatus)) return 'info';
  return 'default';
};

export const StatusBadge = ({ status, type }: StatusBadgeProps) => {
  const resolvedType = type || getTypeFromStatus(status);
  const colors = statusColors[resolvedType];

  return (
    <span
      className="status-badge-component"
      style={{
        backgroundColor: colors.bg,
        color: colors.text,
      }}
    >
      {status}
    </span>
  );
};

