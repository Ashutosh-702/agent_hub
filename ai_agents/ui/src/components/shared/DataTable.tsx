import type { ReactNode } from 'react';

export type DataTableColumn<T> = {
  id: string;
  header: ReactNode;
  cell: (row: T) => ReactNode;
  thClassName?: string;
  tdClassName?: string;
};

type DataTableProps<T> = {
  rows: T[];
  columns: Array<DataTableColumn<T>>;
  getRowKey: (row: T) => string;
  onRowClick?: (row: T) => void;
  rowClassName?: (row: T) => string;
  tableClassName?: string;
  emptyState?: ReactNode;
};

/**
 * Minimal, reusable table renderer:
 * - No styling assumptions (caller passes className)
 * - Works well with external UI kits by swapping classes only
 */
export function DataTable<T>({
  rows,
  columns,
  getRowKey,
  onRowClick,
  rowClassName,
  tableClassName,
  emptyState,
}: DataTableProps<T>) {
  return (
    <table className={tableClassName}>
      <thead>
        <tr>
          {columns.map((c) => (
            <th key={c.id} className={c.thClassName}>
              {c.header}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr>
            <td colSpan={columns.length}>{emptyState}</td>
          </tr>
        ) : (
          rows.map((row) => (
            <tr
              key={getRowKey(row)}
              className={rowClassName?.(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
            >
              {columns.map((c) => (
                <td key={c.id} className={c.tdClassName}>
                  {c.cell(row)}
                </td>
              ))}
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}


