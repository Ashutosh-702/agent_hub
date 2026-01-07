interface PaginationProps {
  currentPage: number;
  totalRecords?: number;
  pageSize: number;
  hasNext: boolean;
  onPrevious: () => void;
  onNext: () => void;
}

export const Pagination = ({
  currentPage,
  totalRecords,
  pageSize,
  hasNext,
  onPrevious,
  onNext,
}: PaginationProps) => {
  const totalPages = totalRecords ? Math.ceil(totalRecords / pageSize) : null;

  return (
    <div className="pagination-component">
      <div className="pagination-info">
        Showing page {currentPage}
        {totalPages && ` of ${totalPages}`}
        {totalRecords && totalRecords > 0 && ` (${totalRecords} total)`}
      </div>
      <div className="pagination-controls">
        <button
          className="pagination-btn"
          onClick={onPrevious}
          disabled={currentPage === 1}
          aria-label="Previous page"
        >
          Previous
        </button>
        <span className="pagination-current">Page {currentPage}</span>
        <button
          className="pagination-btn"
          onClick={onNext}
          disabled={!hasNext}
          aria-label="Next page"
        >
          Next
        </button>
      </div>
    </div>
  );
};
