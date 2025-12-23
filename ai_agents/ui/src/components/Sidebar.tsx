import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

interface MenuItem {
  path: string;
  label: string;
  icon: string;
  children?: MenuItem[];
}

const menuItems: MenuItem[] = [
  { path: '/campaign', label: 'Campaign', icon: '📋' },
  { 
    path: '/master-data', 
    label: 'Master Data', 
    icon: '🏢',
    children: [
      { path: '/master-data/companies', label: 'Companies', icon: '🏭' },
    ]
  },
];

export const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
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
    <>
      {/* Hamburger Button */}
      <button
        className="hamburger-btn"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle menu"
      >
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
        <span className={`hamburger-line ${isOpen ? 'open' : ''}`} />
      </button>

      {/* Overlay */}
      {isOpen && <div className="sidebar-overlay" onClick={() => setIsOpen(false)} />}

      {/* Sidebar */}
      <aside className={`sidebar ${isOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h2>Agent Hub</h2>
        </div>
        <nav className="sidebar-nav">
          {menuItems.map((item) => (
            <div key={item.path} className="sidebar-item-wrapper">
              {item.children ? (
                <>
                  <button
                    className={`sidebar-link sidebar-parent ${isChildActive(item) ? 'active' : ''}`}
                    onClick={() => toggleExpand(item.path)}
                  >
                    <span className="sidebar-icon">{item.icon}</span>
                    <span className="sidebar-label">{item.label}</span>
                    <span className={`sidebar-expand-icon ${expandedItems.includes(item.path) ? 'expanded' : ''}`}>
                      ▶
                    </span>
                  </button>
                  {expandedItems.includes(item.path) && (
                    <div className="sidebar-children">
                      {item.children.map((child) => (
                        <NavLink
                          key={child.path}
                          to={child.path}
                          className={({ isActive }) =>
                            `sidebar-link sidebar-child ${isActive ? 'active' : ''}`
                          }
                          onClick={() => setIsOpen(false)}
                        >
                          <span className="sidebar-icon">{child.icon}</span>
                          <span className="sidebar-label">{child.label}</span>
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
                  onClick={() => setIsOpen(false)}
                >
                  <span className="sidebar-icon">{item.icon}</span>
                  <span className="sidebar-label">{item.label}</span>
                </NavLink>
              )}
            </div>
          ))}
        </nav>
      </aside>
    </>
  );
};
