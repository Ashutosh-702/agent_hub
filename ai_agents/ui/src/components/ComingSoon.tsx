import { useLocation } from 'react-router-dom';
import { Typography } from 'novus';

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
        <Typography variant="heading-xl" type="h1" className="coming-soon-title">
          Coming Soon
        </Typography>
        <Typography variant="body-l" type="p" className="coming-soon-subtitle">
          {getPageName()}
        </Typography>
        <Typography variant="body-m" type="p" className="coming-soon-description">
          We're working hard to bring you this feature. Stay tuned for updates!
        </Typography>
        <div className="coming-soon-decoration">
          <span className="dot"></span>
          <span className="dot"></span>
          <span className="dot"></span>
        </div>
      </div>
    </div>
  );
};

