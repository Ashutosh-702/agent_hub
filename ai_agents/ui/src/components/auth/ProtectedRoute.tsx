import { Navigate, useLocation } from 'react-router-dom';
import { isAuthenticated } from '../../store/api';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const location = useLocation();

  // Simple check: if token exists in localStorage, allow access
  // The backend will validate the token on every API request
  // If token is invalid/expired, API calls will return 401 and we handle that globally
  if (!isAuthenticated()) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Render protected content
  return <>{children}</>;
};

export default ProtectedRoute;

