import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  /**
   * Visual variant:
   * - default: includes bottom divider + spacing (via CSS)
   * - inline: no divider/extra spacing (use when the parent already adds those)
   */
  variant?: 'default' | 'inline';
  className?: string;
  titleClassName?: string;
  subtitleClassName?: string;
}

export const PageHeader = ({
  title,
  subtitle,
  action,
  variant = 'default',
  className,
  titleClassName,
  subtitleClassName,
}: PageHeaderProps) => {
  const rootClassName = [
    'page-header-component',
    variant === 'inline' ? 'page-header-inline' : '',
    className || '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={rootClassName}>
      <div className="page-header-text">
        <h1 className={titleClassName || 'page-header-title'}>{title}</h1>
        {subtitle && (
          <p className={subtitleClassName || 'page-header-subtitle'}>{subtitle}</p>
        )}
      </div>
      {action && <div className="page-header-action">{action}</div>}
    </div>
  );
};

