import type { ReactNode } from 'react';

export type InfoGridItem = {
  label: ReactNode;
  value: ReactNode;
  /**
   * Optional className on the *value* span.
   * Useful for cases like badges (e.g. `source-badge`).
   */
  valueClassName?: string;
  /** Optional className on the item wrapper div. */
  className?: string;
};

type InfoGridProps = {
  items: InfoGridItem[];
  /** ClassName for the grid wrapper (e.g. `campaign-info-grid`, `company-info-grid`). */
  className?: string;
  /** ClassName for each item wrapper. Defaults to `info-item` to match existing CSS. */
  itemClassName?: string;
};

/**
 * Reusable label/value grid.
 * Renders the same DOM shape used across details pages:
 *   <div class="...grid">
 *     <div class="info-item"><label/> <span/></div>
 *   </div>
 *
 * Styling is controlled by existing CSS selectors like `.info-item label` / `.info-item span`.
 */
export const InfoGrid = ({ items, className, itemClassName = 'info-item' }: InfoGridProps) => {
  return (
    <div className={className}>
      {items.map((item, idx) => (
        <div key={idx} className={`${itemClassName}${item.className ? ` ${item.className}` : ''}`}>
          <label>{item.label}</label>
          <span className={item.valueClassName}>{item.value}</span>
        </div>
      ))}
    </div>
  );
};


