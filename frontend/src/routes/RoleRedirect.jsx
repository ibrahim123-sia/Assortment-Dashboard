import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const RoleRedirect = () => {
  const { isAuthenticated, loading, user } = useAuth();
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center"><LoadingSpinner /></div>;
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (user.role === 'super_admin') return <Navigate to="/admin/stores" replace />;
  return <Navigate to="/dashboard" replace />;
};
