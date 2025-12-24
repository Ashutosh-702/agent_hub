import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useSidebar } from '../context/SidebarContext';

interface MenuItem {
  path: string;
  label: string;
  icon: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  { 
    path: '/master-data', 
    label: 'Master Data', 
    icon: '🏢',
    children: [
      { path: '/master-data/campaign', label: 'Campaign', icon: '📋' },
      { path: '/master-data/companies', label: 'Companies', icon: '🏭' },
    ]
  },
  { 
    path: '/prospecting', 
    label: 'Prospecting', 
    icon: '🎯',
    children: [
      { path: '/prospecting/company', label: 'Company Prospecting', icon: '🔍' },
      { path: '/prospecting/contact', label: 'Contact Prospecting', icon: '👤' },
      { path: '/prospecting/wide', label: 'Wide Prospecting', icon: '🌐' },
    ]
  },
];

export const Sidebar = () => {
  const { isCollapsed, toggleSidebar } = useSidebar();
  const [expandedItems, setExpandedItems] = useState<string[]>(['/master-data']);
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
        <span className="toggle-icon">{isCollapsed ? '→' : '←'}</span>
      </button>

      {/* Header */}
      <div className="sidebar-header">
        <h2>{isCollapsed ? 'AH' : 'Agent Hub'}</h2>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {menuItems.map((item) => (
          <div key={item.path} className="sidebar-item-wrapper">
            {item.children ? (
              <>
                <button
                  className={`sidebar-link sidebar-parent ${isChildActive(item) ? 'active' : ''}`}
                  onClick={() => !isCollapsed && toggleExpand(item.path)}
                  title={isCollapsed ? item.label : undefined}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  {!isCollapsed && (
                    <>
                      <span className="sidebar-label">{item.label}</span>
                      <span className={`sidebar-expand-icon ${expandedItems.includes(item.path) ? 'expanded' : ''}`}>
                        ▶
                      </span>
                    </>
                  )}
                </button>
                {!isCollapsed && expandedItems.includes(item.path) && (
                  <div className="sidebar-children">
                    {item.children.map((child) => (
                      <NavLink
                        key={child.path}
                        to={child.path}
                        className={({ isActive }) =>
                          `sidebar-link sidebar-child ${isActive ? 'active' : ''}`
                        }
                      >
                        <span className="sidebar-icon">{child.icon}</span>
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
                      >
                        <span className="sidebar-icon">{child.icon}</span>
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
                <span className="sidebar-icon">{item.icon}</span>
                {!isCollapsed && <span className="sidebar-label">{item.label}</span>}
              </NavLink>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
};
