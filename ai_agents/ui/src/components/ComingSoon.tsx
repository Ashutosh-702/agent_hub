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
        <div className="coming-soon-icon">🚀</div>
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

