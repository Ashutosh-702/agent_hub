import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { ToastProvider } from './ui/Toast';

const navItems = [
  { path: '/hubspot/company', label: 'Create Company', icon: BuildingIcon },
  { path: '/hubspot/contact', label: 'Create Contact', icon: UserIcon },
  { path: '/hubspot/deal', label: 'Create Deal', icon: DealIcon },
];

function BuildingIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 21h18" />
      <path d="M5 21V7l8-4v18" />
      <path d="M19 21V11l-6-4" />
      <path d="M9 9h.01" />
      <path d="M9 12h.01" />
      <path d="M9 15h.01" />
      <path d="M9 18h.01" />
    </svg>
  );
}

function UserIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function DealIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="M12 9v6" />
      <path d="M9 12h6" />
    </svg>
  );
}

export const HubSpotLayout = () => {
  const location = useLocation();
  const isRootPath = location.pathname === '/hubspot';

  return (
    <ToastProvider>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: 'calc(100vh - 4rem)',
          padding: '0',
        }}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1.5rem 2rem',
            borderBottom: '1px solid var(--color-gray-200)',
            background: 'var(--color-white)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {/* HubSpot Logo */}
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #ff7a59 0%, #ff5c35 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 2px 8px rgba(255, 122, 89, 0.3)',
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="white">
                <path d="M18.38 7.46V6.28a2.28 2.28 0 0 0 1.32-2.07 2.3 2.3 0 0 0-4.6 0 2.28 2.28 0 0 0 1.32 2.07v1.18a5.51 5.51 0 0 0-2.76 1.28l-6.7-5.21a2.3 2.3 0 1 0-1.31 1.68l6.53 5.07a5.52 5.52 0 0 0 .51 7.09 5.51 5.51 0 0 0 7.78 0 5.52 5.52 0 0 0 0-7.8 5.51 5.51 0 0 0-2.09-1.28zM16.4 17.4a3.3 3.3 0 1 1 0-4.67 3.3 3.3 0 0 1 0 4.67z" />
              </svg>
            </div>
            <div>
              <h1
                style={{
                  margin: 0,
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: 'var(--color-gray-900)',
                }}
              >
                HubSpot Integration
              </h1>
              <p
                style={{
                  margin: '0.125rem 0 0 0',
                  fontSize: '0.875rem',
                  color: 'var(--color-gray-500)',
                }}
              >
                Create and link companies, contacts, and deals
              </p>
            </div>
          </div>
        </div>

        {/* Sub Navigation */}
        <div
          style={{
            display: 'flex',
            gap: '0.5rem',
            padding: '1rem 2rem',
            background: 'var(--color-gray-50)',
            borderBottom: '1px solid var(--color-gray-200)',
          }}
        >
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.625rem 1rem',
                borderRadius: '8px',
                fontSize: '0.875rem',
                fontWeight: 500,
                textDecoration: 'none',
                color: isActive ? 'var(--color-primary)' : 'var(--color-gray-600)',
                background: isActive ? 'var(--color-white)' : 'transparent',
                border: isActive ? '1px solid var(--color-gray-200)' : '1px solid transparent',
                boxShadow: isActive ? '0 1px 3px rgba(0, 0, 0, 0.04)' : 'none',
                transition: 'all 0.15s ease',
              })}
            >
              <item.icon />
              {item.label}
            </NavLink>
          ))}
        </div>

        {/* Content Area */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            padding: '2rem',
            background: 'var(--color-gray-50)',
          }}
        >
          {isRootPath ? (
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100%',
                textAlign: 'center',
              }}
            >
              <div
                style={{
                  width: '80px',
                  height: '80px',
                  borderRadius: '20px',
                  background: 'linear-gradient(135deg, #ff7a59 0%, #ff5c35 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '1.5rem',
                  boxShadow: '0 8px 24px rgba(255, 122, 89, 0.25)',
                }}
              >
                <svg width="40" height="40" viewBox="0 0 24 24" fill="white">
                  <path d="M18.38 7.46V6.28a2.28 2.28 0 0 0 1.32-2.07 2.3 2.3 0 0 0-4.6 0 2.28 2.28 0 0 0 1.32 2.07v1.18a5.51 5.51 0 0 0-2.76 1.28l-6.7-5.21a2.3 2.3 0 1 0-1.31 1.68l6.53 5.07a5.52 5.52 0 0 0 .51 7.09 5.51 5.51 0 0 0 7.78 0 5.52 5.52 0 0 0 0-7.8 5.51 5.51 0 0 0-2.09-1.28zM16.4 17.4a3.3 3.3 0 1 1 0-4.67 3.3 3.3 0 0 1 0 4.67z" />
                </svg>
              </div>
              <h2
                style={{
                  margin: '0 0 0.5rem 0',
                  fontSize: '1.5rem',
                  fontWeight: 700,
                  color: 'var(--color-gray-900)',
                }}
              >
                Welcome to HubSpot Integration
              </h2>
              <p
                style={{
                  margin: '0 0 2rem 0',
                  fontSize: '1rem',
                  color: 'var(--color-gray-500)',
                  maxWidth: '400px',
                }}
              >
                Create and link companies, contacts, and deals to your HubSpot CRM. Choose an option above to get started.
              </p>
              <div
                style={{
                  display: 'flex',
                  gap: '1rem',
                  flexWrap: 'wrap',
                  justifyContent: 'center',
                }}
              >
                {navItems.map((item) => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '1.5rem 2rem',
                      background: 'var(--color-white)',
                      border: '1px solid var(--color-gray-200)',
                      borderRadius: '12px',
                      textDecoration: 'none',
                      transition: 'all 0.15s ease',
                      minWidth: '160px',
                    }}
                    onMouseOver={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-primary)';
                      e.currentTarget.style.boxShadow = '0 4px 12px rgba(46, 49, 190, 0.1)';
                      e.currentTarget.style.transform = 'translateY(-2px)';
                    }}
                    onMouseOut={(e) => {
                      e.currentTarget.style.borderColor = 'var(--color-gray-200)';
                      e.currentTarget.style.boxShadow = 'none';
                      e.currentTarget.style.transform = 'none';
                    }}
                  >
                    <div
                      style={{
                        width: '48px',
                        height: '48px',
                        borderRadius: '12px',
                        background: 'var(--color-primary-light)',
                        color: 'var(--color-primary)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <item.icon />
                    </div>
                    <span
                      style={{
                        fontSize: '0.9375rem',
                        fontWeight: 600,
                        color: 'var(--color-gray-800)',
                      }}
                    >
                      {item.label}
                    </span>
                  </NavLink>
                ))}
              </div>
              <p
                style={{
                  marginTop: '2rem',
                  fontSize: '0.8125rem',
                  color: 'var(--color-gray-400)',
                  fontStyle: 'italic',
                }}
              >
                💡 Match-first prevents duplicates and keeps HubSpot clean.
              </p>
            </div>
          ) : (
            <Outlet />
          )}
        </div>
      </div>
    </ToastProvider>
  );
};


