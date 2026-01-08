import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useSidebar } from '../context/SidebarContext';
import { useLogoutMutation, getStoredUser } from '../store/api';
import { clearUserIdentity } from '../services/analytics';

// Force instant navigation - hides UI first for immediate feedback
const forceNavigate = (path: string, event: React.MouseEvent) => {
  event.preventDefault();
  event.stopPropagation();
  
  // Hide UI immediately for instant visual feedback
  const root = document.getElementById('root');
  if (root) root.style.visibility = 'hidden';
  
  // Navigate immediately
  window.location.href = path;
};

// Campaign type labels for display
const CAMPAIGN_TYPE_LABELS: Record<string, string> = {
  import_csv: 'Import List',
  single_company: 'Single Company',
  wide_prospecting: 'Wide Prospecting',
  similar_companies: 'Similar Companies',
  nl_filter: 'NL Filter',
};

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
  contactProspecting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
  hubspot: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18.38 7.46V6.28a2.28 2.28 0 0 0 1.32-2.07 2.3 2.3 0 0 0-4.6 0 2.28 2.28 0 0 0 1.32 2.07v1.18a5.51 5.51 0 0 0-2.76 1.28l-6.7-5.21a2.3 2.3 0 1 0-1.31 1.68l6.53 5.07a5.52 5.52 0 0 0 .51 7.09 5.51 5.51 0 0 0 7.78 0 5.52 5.52 0 0 0 0-7.8 5.51 5.51 0 0 0-2.09-1.28z"/>
      <circle cx="16.4" cy="15.07" r="3.3"/>
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
  rocket: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/>
      <path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/>
      <path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/>
    </svg>
  ),
  inbox: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/>
      <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
    </svg>
  ),
  phone: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>
    </svg>
  ),
  clipboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/>
      <rect x="8" y="2" width="8" height="4" rx="1" ry="1"/>
    </svg>
  ),
  lightbulb: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 18h6"/>
      <path d="M10 22h4"/>
      <path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5A4.61 4.61 0 0 1 8.91 14"/>
    </svg>
  ),
  logout: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
  user: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
      <circle cx="12" cy="7" r="4"/>
    </svg>
  ),
};

interface MenuItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  children?: MenuItem[];
}

// Add message icon
const IconsExtended = {
  ...Icons,
  messages: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
    </svg>
  ),
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
      <line x1="3" y1="9" x2="21" y2="9"/>
      <line x1="9" y1="21" x2="9" y2="9"/>
    </svg>
  ),
};

const menuItems: MenuItem[] = [
  // 1. Campaign
  { 
    path: '/campaign', 
    label: 'Prospecting + Outreach', 
    icon: Icons.campaign,
  },
  // 2. Inbox
  { 
    path: '/inbox', 
    label: 'Inbox', 
    icon: Icons.inbox,
    children: [
      { path: '/inbox', label: 'Dashboard', icon: IconsExtended.dashboard },
      { path: '/inbox/company', label: 'Company Wise Messages', icon: Icons.companies },
      { path: '/inbox/messages', label: 'Contact Wise Messages', icon: Icons.contactProspecting },
    ],
  },
  // 3. Client Calls
  { 
    path: '/client-calls', 
    label: 'Client Calls', 
    icon: Icons.phone,
    children: [
      { path: '/client-calls/prep', label: 'Prep for a Call', icon: Icons.clipboard },
      { path: '/client-calls/start', label: 'Start a Call', icon: Icons.phone },
      { path: '/client-calls/reflections', label: 'Reflect', icon: Icons.lightbulb },
    ]
  },
  // 4. Master Data
  { 
    path: '/master-data', 
    label: 'Master Data', 
    icon: Icons.masterData,
    children: [
      { path: '/master-data/companies', label: 'Companies', icon: Icons.companies },
      { path: '/master-data/contacts', label: 'Contacts', icon: Icons.contactProspecting },
    ]
  },
  // 5. HubSpot
  { 
    path: '/hubspot', 
    label: 'HubSpot', 
    icon: Icons.hubspot,
    children: [
      { path: '/hubspot/company', label: 'Create Company', icon: Icons.companies },
      { path: '/hubspot/contact', label: 'Create Contact', icon: Icons.contactProspecting },
      { path: '/hubspot/deal', label: 'Create Deal', icon: Icons.campaign },
    ]
  },
];

export const Sidebar = () => {
  const { isCollapsed, toggleSidebar, wizardProgress } = useSidebar();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);
  const location = useLocation();
  const navigate = useNavigate();
  const [logout, { isLoading: isLoggingOut }] = useLogoutMutation();
  
  const currentUser = getStoredUser();
  const isInWizard = location.pathname.includes('/campaign/new');

  const handleLogout = async () => {
    try {
      await logout().unwrap();
    } catch {
      // Even if logout fails, clear local storage and redirect
    }
    // Clear user identity from analytics (Zipy, Usersnap)
    clearUserIdentity();
    navigate('/login', { replace: true });
  };

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
        <h2>{isCollapsed ? 'NE' : 'Nebula'}</h2>
      </div>

      {/* Wizard Progress Section - shown when in campaign wizard */}
      {isInWizard && wizardProgress.isActive && !isCollapsed && (
        <div className="wizard-progress-section">
          <div className="wizard-progress-header">
            <span className="wizard-icon">{Icons.rocket}</span>
            <span className="wizard-label">Creating Campaign</span>
          </div>
          
          {wizardProgress.campaignType && (
            <div className="wizard-type-badge">
              {CAMPAIGN_TYPE_LABELS[wizardProgress.campaignType] || wizardProgress.campaignType}
            </div>
          )}

          {wizardProgress.steps.length > 0 && (
            <div className="wizard-steps-progress">
              <div className="progress-bar-mini">
                <div 
                  className="progress-fill-mini" 
                  style={{ 
                    width: `${(wizardProgress.currentStep / wizardProgress.totalSteps) * 100}%` 
                  }}
                />
              </div>
              <span className="progress-text-mini">
                Step {wizardProgress.currentStep} of {wizardProgress.totalSteps}
              </span>
              
              <div className="wizard-steps-list">
                {wizardProgress.steps.map((step) => (
                  <div 
                    key={step.id}
                    className={`wizard-step-item ${
                      step.stepNumber === wizardProgress.currentStep ? 'active' : ''
                    } ${step.stepNumber < wizardProgress.currentStep ? 'completed' : ''}`}
                  >
                    <span className="step-indicator">
                      {step.stepNumber < wizardProgress.currentStep ? (
                        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                          <polyline points="20 6 9 17 4 12"/>
                        </svg>
                      ) : (
                        step.stepNumber
                      )}
                    </span>
                    <span className="step-title">{step.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Collapsed wizard indicator */}
      {isInWizard && wizardProgress.isActive && isCollapsed && (
        <div className="wizard-progress-collapsed" title={`Step ${wizardProgress.currentStep} of ${wizardProgress.totalSteps}`}>
          <span className="wizard-icon-small">{Icons.rocket}</span>
          <span className="wizard-step-badge">{wizardProgress.currentStep}/{wizardProgress.totalSteps}</span>
        </div>
      )}

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
                        onClick={isInWizard ? (e) => forceNavigate(child.path, e) : undefined}
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
                        onClick={isInWizard ? (e) => forceNavigate(child.path, e) : undefined}
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
                onClick={isInWizard ? (e) => forceNavigate(item.path, e) : undefined}
              >
                <span className="sidebar-icon" aria-hidden="true">{item.icon}</span>
                {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
              </NavLink>
            )}
          </div>
        ))}
      </nav>

      {/* User section at bottom */}
      <div className="sidebar-footer">
        {!isCollapsed && currentUser && (
          <div className="sidebar-user-info">
            <span className="sidebar-icon">{Icons.user}</span>
            <div className="sidebar-user-details">
              <span className="sidebar-user-name">{currentUser.name}</span>
              <span className="sidebar-user-email">{currentUser.email}</span>
            </div>
          </div>
        )}
        <button
          className="sidebar-logout-btn"
          onClick={handleLogout}
          disabled={isLoggingOut}
          title={isCollapsed ? 'Logout' : undefined}
        >
          <span className="sidebar-icon">{Icons.logout}</span>
          {!isCollapsed && <span className="sidebar-label">{isLoggingOut ? 'Logging out...' : 'Logout'}</span>}
        </button>
      </div>
    </aside>
  );
};
