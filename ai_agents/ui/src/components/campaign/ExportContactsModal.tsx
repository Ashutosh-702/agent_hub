import { useState, useEffect } from 'react';
import { useLazyGetExportContactsMetadataQuery } from '../../store';

interface ExportContactsModalProps {
  isOpen: boolean;
  onClose: () => void;
  campaignId: string;
  campaignName?: string;
}

export const ExportContactsModal = ({
  isOpen,
  onClose,
  campaignId,
  campaignName,
}: ExportContactsModalProps) => {
  const [fetchMetadata, { data: metadataResponse, isLoading, error }] = useLazyGetExportContactsMetadataQuery();
  const [downloadingPage, setDownloadingPage] = useState<number | null>(null);

  // Fetch metadata when modal opens
  useEffect(() => {
    if (isOpen && campaignId) {
      fetchMetadata({ campaign_id: campaignId });
    }
  }, [isOpen, campaignId, fetchMetadata]);

  if (!isOpen) return null;

  const metadata = metadataResponse?.data;
  const totalCount = metadata?.total_count || 0;
  const totalPages = metadata?.total_pages || 0;
  const perPage = metadata?.per_page || 500;

  const handleDownload = async (page: number) => {
    setDownloadingPage(page);
    try {
      // Trigger browser download
      const url = `/api/v1/export_contacts_csv?campaign_id=${encodeURIComponent(campaignId)}&page=${page}&limit=${perPage}`;
      
      // Create a temporary link and trigger download
      const link = document.createElement('a');
      link.href = url;
      link.download = `contacts_export_${campaignId}_page_${page}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloadingPage(null);
    }
  };

  const getPageRange = (page: number): string => {
    const start = (page - 1) * perPage + 1;
    const end = Math.min(page * perPage, totalCount);
    return `${start}-${end}`;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content export-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <h3>Export Contacts</h3>
          <button className="modal-close-btn" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div className="modal-body">
          {campaignName && (
            <div className="export-campaign-name">
              <strong>Campaign:</strong> {campaignName}
            </div>
          )}

          {isLoading ? (
            <div className="export-loading">
              <div className="spinner" />
              <span>Loading export information...</span>
            </div>
          ) : error ? (
            <div className="export-error">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="15" y1="9" x2="9" y2="15" />
                <line x1="9" y1="9" x2="15" y2="15" />
              </svg>
              <span>Failed to load export information. Please try again.</span>
            </div>
          ) : totalCount === 0 ? (
            <div className="export-empty">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                <polyline points="13 2 13 9 20 9" />
              </svg>
              <h4>No Contacts to Export</h4>
              <p>There are no qualified and enriched contacts in this campaign.</p>
            </div>
          ) : (
            <>
              <div className="export-info">
                <div className="export-stat">
                  <span className="export-stat-value">{totalCount.toLocaleString()}</span>
                  <span className="export-stat-label">Total Contacts</span>
                </div>
                <div className="export-stat">
                  <span className="export-stat-value">{totalPages}</span>
                  <span className="export-stat-label">{totalPages === 1 ? 'Page' : 'Pages'}</span>
                </div>
                <div className="export-stat">
                  <span className="export-stat-value">{perPage}</span>
                  <span className="export-stat-label">Per Page</span>
                </div>
              </div>

              <div className="export-description">
                <p>Select a page to download (max {perPage} contacts per download):</p>
              </div>

              <div className="export-pages-grid">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                  const isDownloading = downloadingPage === page;
                  return (
                    <button
                      key={page}
                      className={`export-page-btn ${isDownloading ? 'downloading' : ''}`}
                      onClick={() => handleDownload(page)}
                      disabled={downloadingPage !== null}
                    >
                      <div className="export-page-info">
                        <span className="export-page-number">Page {page}</span>
                        <span className="export-page-range">Contacts {getPageRange(page)}</span>
                      </div>
                      <div className="export-page-action">
                        {isDownloading ? (
                          <div className="spinner small" />
                        ) : (
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                            <polyline points="7 10 12 15 17 10" />
                            <line x1="12" y1="15" x2="12" y2="3" />
                          </svg>
                        )}
                      </div>
                    </button>
                  );
                })}
              </div>

              <div className="export-csv-info">
                <h5>CSV Fields:</h5>
                <p>sl_no, company_name, company_industry, contact_name, email, jobtitle, linkedin_url, country, city</p>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>

      <style>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content.export-modal {
          background: var(--color-white, #fff);
          border-radius: 12px;
          width: 100%;
          max-width: 560px;
          max-height: 80vh;
          overflow: hidden;
          display: flex;
          flex-direction: column;
          box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }

        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 20px 24px;
          border-bottom: 1px solid var(--color-gray-200, #e5e7eb);
        }

        .modal-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
          color: var(--color-gray-900, #111827);
        }

        .modal-close-btn {
          background: none;
          border: none;
          cursor: pointer;
          padding: 4px;
          color: var(--color-gray-500, #6b7280);
          border-radius: 4px;
          transition: all 0.2s;
        }

        .modal-close-btn:hover {
          background: var(--color-gray-100, #f3f4f6);
          color: var(--color-gray-700, #374151);
        }

        .modal-body {
          padding: 24px;
          overflow-y: auto;
          flex: 1;
        }

        .export-campaign-name {
          background: var(--color-gray-50, #f9fafb);
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 20px;
          font-size: 14px;
          color: var(--color-gray-700, #374151);
        }

        .export-loading,
        .export-error {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          padding: 40px;
          color: var(--color-gray-500, #6b7280);
        }

        .export-error {
          color: var(--color-red-500, #ef4444);
        }

        .export-empty {
          text-align: center;
          padding: 40px 20px;
          color: var(--color-gray-500, #6b7280);
        }

        .export-empty svg {
          margin-bottom: 16px;
          opacity: 0.5;
        }

        .export-empty h4 {
          margin: 0 0 8px 0;
          font-size: 16px;
          color: var(--color-gray-700, #374151);
        }

        .export-empty p {
          margin: 0;
          font-size: 14px;
        }

        .export-info {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 16px;
          margin-bottom: 20px;
        }

        .export-stat {
          background: var(--color-gray-50, #f9fafb);
          padding: 16px;
          border-radius: 8px;
          text-align: center;
        }

        .export-stat-value {
          display: block;
          font-size: 24px;
          font-weight: 700;
          color: var(--color-primary, #6366f1);
        }

        .export-stat-label {
          display: block;
          font-size: 12px;
          color: var(--color-gray-500, #6b7280);
          margin-top: 4px;
        }

        .export-description {
          margin-bottom: 16px;
        }

        .export-description p {
          margin: 0;
          font-size: 14px;
          color: var(--color-gray-600, #4b5563);
        }

        .export-pages-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 12px;
          margin-bottom: 20px;
        }

        .export-page-btn {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          background: var(--color-white, #fff);
          border: 1px solid var(--color-gray-200, #e5e7eb);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .export-page-btn:hover:not(:disabled) {
          border-color: var(--color-primary, #6366f1);
          background: var(--color-primary-50, #eef2ff);
        }

        .export-page-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .export-page-btn.downloading {
          border-color: var(--color-primary, #6366f1);
          background: var(--color-primary-50, #eef2ff);
        }

        .export-page-info {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 2px;
        }

        .export-page-number {
          font-weight: 600;
          font-size: 14px;
          color: var(--color-gray-900, #111827);
        }

        .export-page-range {
          font-size: 12px;
          color: var(--color-gray-500, #6b7280);
        }

        .export-page-action {
          color: var(--color-primary, #6366f1);
        }

        .export-csv-info {
          background: var(--color-gray-50, #f9fafb);
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 12px;
        }

        .export-csv-info h5 {
          margin: 0 0 4px 0;
          font-size: 12px;
          font-weight: 600;
          color: var(--color-gray-700, #374151);
        }

        .export-csv-info p {
          margin: 0;
          color: var(--color-gray-500, #6b7280);
          font-family: monospace;
          word-break: break-word;
        }

        .modal-footer {
          padding: 16px 24px;
          border-top: 1px solid var(--color-gray-200, #e5e7eb);
          display: flex;
          justify-content: flex-end;
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 2px solid var(--color-gray-200, #e5e7eb);
          border-top-color: var(--color-primary, #6366f1);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        .spinner.small {
          width: 16px;
          height: 16px;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .btn-secondary {
          padding: 8px 16px;
          font-size: 14px;
          font-weight: 500;
          color: var(--color-gray-700, #374151);
          background: var(--color-white, #fff);
          border: 1px solid var(--color-gray-300, #d1d5db);
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-secondary:hover {
          background: var(--color-gray-50, #f9fafb);
        }
      `}</style>
    </div>
  );
};

