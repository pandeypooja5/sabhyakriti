import { Navigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import LoadingSpinner from './LoadingSpinner';

interface AdminRouteProps {
  children: React.ReactNode;
}

const AdminRoute: React.FC<AdminRouteProps> = ({ children }) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  if (loading) return <LoadingSpinner fullScreen />;

  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (!isAdmin) return <Navigate to="/" replace />;

  return <>{children}</>;
};

export default AdminRoute;
