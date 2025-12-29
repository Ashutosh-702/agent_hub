import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useSidebar } from '../context/SidebarContext';

// SVG Icon Components - Clean, accessible icons
const Icons = {
  masterData: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  campaign: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
      <polyline points="14 2 14 8 20 8"/>
      <line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/>
      <polyline points="10 9 9 9 8 9"/>
    </svg>
  ),
  companies: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 21h18"/>
      <path d="M5 21V7l8-4v18"/>
      <path d="M19 21V11l-6-4"/>
      <path d="M9 9h.01"/>
      <path d="M9 12h.01"/>
      <path d="M9 15h.01"/>
      <path d="M9 18h.01"/>
    </svg>
  ),
  prospecting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <circle cx="12" cy="12" r="6"/>
      <circle cx="12" cy="12" r="2"/>
    </svg>
  ),
  companyProspecting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/>
      <line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  ),
  contactProspecting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  wideProspecting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="2" y1="12" x2="22" y2="12"/>
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  ),
  chevronRight: (
    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6"/>
    </svg>
  ),
  arrowLeft: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12"/>
      <polyline points="12 19 5 12 12 5"/>
    </svg>
  ),
  arrowRight: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12"/>
      <polyline points="12 5 19 12 12 19"/>
    </svg>
  ),
};

interface MenuItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  { 
    path: '/campaign', 
    label: 'Campaign', 
    icon: Icons.campaign,
  },
  { 
    path: '/master-data', 
    label: 'Master Data', 
    icon: Icons.masterData,
    children: [
      { path: '/master-data/companies', label: 'Companies', icon: Icons.companies },
      { path: '/master-data/contacts', label: 'Contacts', icon: Icons.contactProspecting },
    ]
  },
  { 
    path: '/prospecting', 
    label: 'Prospecting', 
    icon: Icons.prospecting,
    children: [
      { path: '/prospecting/campaigns', label: 'Campaign Prospecting', icon: Icons.campaign },
      { path: '/prospecting/company', label: 'Company Prospecting', icon: Icons.companyProspecting },
      { path: '/prospecting/contact', label: 'Contact Prospecting', icon: Icons.contactProspecting },
      { path: '/prospecting/wide', label: 'Wide Prospecting', icon: Icons.wideProspecting },
    ]
  },
];

export const Sidebar = () => {
  const { isCollapsed, toggleSidebar } = useSidebar();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const location = useLocation();

  const toggleExpand = (path: string) => {
    setExpandedItems(prev => 
      prev.includes(path) 
        ? prev.filter(p => p !== path)
        : [...prev, path]
    );
  };

  const isChildActive = (item: MenuItem) => {
    return item.children?.some(child => location.pathname.startsWith(child.path));
  };

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      {/* Toggle Button */}
      <button
        className="sidebar-toggle-btn"
        onClick={toggleSidebar}
        aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
      >
        <span className="toggle-icon">
          {isCollapsed ? Icons.arrowRight : Icons.arrowLeft}
        </span>
      </button>

      {/* Header */}
      <div className="sidebar-header">
        <h2>{isCollapsed ? 'AH' : 'Agent Hub'}</h2>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav" role="navigation" aria-label="Main navigation">
        {menuItems.map((item) => (
          <div key={item.path} className="sidebar-item-wrapper">
            {item.children ? (
              <>
                <button
                  className={`sidebar-link sidebar-parent ${isChildActive(item) ? 'active' : ''}`}
                  onClick={() => !isCollapsed && toggleExpand(item.path)}
                  title={isCollapsed ? item.label : undefined}
                  aria-expanded={expandedItems.includes(item.path)}
                  aria-controls={`submenu-${item.path.replace('/', '-')}`}
                >
                  <span className="sidebar-icon" aria-hidden="true">{item.icon}</span>
                  {!isCollapsed && (
                    <>
                      <span className="sidebar-label">{item.label}</span>
                      <span 
                        className={`sidebar-expand-icon ${expandedItems.includes(item.path) ? 'expanded' : ''}`}
                        aria-hidden="true"
                      >
                        {Icons.chevronRight}
                      </span>
                    </>
                  )}
                </button>
                {!isCollapsed && expandedItems.includes(item.path) && (
                  <div 
                    className="sidebar-children" 
                    id={`submenu-${item.path.replace('/', '-')}`}
                    role="group"
                    aria-label={`${item.label} submenu`}
                  >
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        className={({ isActive }) =>
                          `sidebar-link sidebar-child ${isActive ? 'active' : ''}`
                        }
                      >
                        <span className="sidebar-icon" aria-hidden="true">{child.icon}</span>
                        <span className="sidebar-label">{child.label}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
                {/* Show children as tooltip-style links when collapsed */}
                {isCollapsed && (
                  <div className="sidebar-collapsed-children">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        className={({ isActive }) =>
                          `sidebar-link sidebar-child ${isActive ? 'active' : ''}`
                        }
                        title={child.label}
                        aria-label={child.label}
                      >
                        <span className="sidebar-icon" aria-hidden="true">{child.icon}</span>
                      </NavLink>
                    ))}
                  </div>
                )}
              </>
            ) : (
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `sidebar-link ${isActive ? 'active' : ''}`
                }
                title={isCollapsed ? item.label : undefined}
              >
                <span className="sidebar-icon" aria-hidden="true">{item.icon}</span>
                {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
              </NavLink>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};
