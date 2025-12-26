import { useLocation } from 'react-router-dom';

export const ComingSoon = () => {
  const location = useLocation();
  
  // Get the page name from the URL
  const getPageName = () => {
    if (location.pathname.includes('company')) return 'Company Prospecting';
    if (location.pathname.includes('contact')) return 'Contact Prospecting';
    return 'This Feature';
  };

  return (
    <div className="coming-soon-page">
      <div className="coming-soon-content">
        <div className="coming-soon-icon" aria-hidden="true">
          <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
            <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
            <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
            <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
          </svg>
        </div>
        <h1 className="coming-soon-title">Coming Soon</h1>
        <p className="coming-soon-subtitle">{getPageName()}</p>
        <p className="coming-soon-description">
          We're working hard to bring you this feature. Stay tuned for updates!
        </p>
        <div className="coming-soon-decoration">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    </div>
  );
};
