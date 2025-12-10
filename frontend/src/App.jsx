import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { DataProvider } from './context/DataContext';

// Layout
import Sidebar from './components/Layout/Sidebar';
import Header from './components/Layout/Header';

// Auth Pages
import Login from './components/Auth/Login';
import Register from './components/Auth/Register';

// Data Pages
import DataUpload from './components/Data/DataUpload';
import DatasetManager from './components/Data/DatasetManager';

// Main Pages
import Dashboard from './pages/Dashboard';
import MarketBasketAnalysis from './pages/MarketBasketAnalysis';
import NetworkGraph from './pages/NetworkGraph';
import ProductBundles from './pages/ProductBundles';
import RevenueAnalysis from './pages/RevenueAnalysis';
import SeasonalAnalysis from './pages/SeasonalAnalysis';
import ProductClustering from './pages/ProductClustering';

// Protected Route Wrapper
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
        </div>
      </div>
    );
  }
  
  if (!user) {
    return <Navigate to="/login" />;
  }
  
  return children;
};

// Layout Component
const MainLayout = ({ children }) => {
  const [searchQuery, setSearchQuery] = React.useState('');

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title="Dashboard" onSearch={setSearchQuery} />
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
        <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-4 px-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between">
            <p className="text-sm text-gray-600 dark:text-gray-400">
              MBA Analytics Platform • Market Basket Analysis • FP-Growth • Apriori • K-Means
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2 md:mt-0">
              © 2024 All rights reserved
            </p>
          </div>
        </footer>
      </div>
    </div>
  );
};

// App Routes
const AppRoutes = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected Routes */}
      <Route path="/" element={
        <ProtectedRoute>
          <MainLayout>
            <Dashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <MainLayout>
            <Dashboard />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/upload" element={
        <ProtectedRoute>
          <MainLayout>
            <DataUpload />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/data" element={
        <ProtectedRoute>
          <MainLayout>
            <DatasetManager />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/market-basket" element={
        <ProtectedRoute>
          <MainLayout>
            <MarketBasketAnalysis />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/network" element={
        <ProtectedRoute>
          <MainLayout>
            <NetworkGraph />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/bundles" element={
        <ProtectedRoute>
          <MainLayout>
            <ProductBundles />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/revenue" element={
        <ProtectedRoute>
          <MainLayout>
            <RevenueAnalysis />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/seasonal" element={
        <ProtectedRoute>
          <MainLayout>
            <SeasonalAnalysis />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/clustering" element={
        <ProtectedRoute>
          <MainLayout>
            <ProductClustering />
          </MainLayout>
        </ProtectedRoute>
      } />
      
      
      
      {/* Redirect to dashboard for any unknown route */}
      <Route path="*" element={<Navigate to="/dashboard" />} />
    </Routes>
  );
};

// Main App Component
function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <DataProvider>
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'var(--bg-color)',
                  color: 'var(--text-color)',
                  border: '1px solid var(--border-color)',
                },
              }}
            />
            <AppRoutes />
          </DataProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

export default App;