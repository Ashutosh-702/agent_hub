import type { ReactNode } from 'react';

type BaseProps = {
  children: ReactNode;
  className?: string;
};

/**
 * Minimal "headless" card primitives.
 * - Designed to be styling-framework agnostic (Bootstrap/Novus/etc.)
 * - Everything is controlled via className from the caller.
 */
export const Card = ({ children, className }: BaseProps) => {
  return <div className={className}>{children}</div>;
};

export const CardHeader = ({ children, className }: BaseProps) => {
  return <div className={className}>{children}</div>;
};

export const CardBody = ({ children, className }: BaseProps) => {
  return <div className={className}>{children}</div>;
};

export const CardFooter = ({ children, className }: BaseProps) => {
  return <div className={className}>{children}</div>;
};


