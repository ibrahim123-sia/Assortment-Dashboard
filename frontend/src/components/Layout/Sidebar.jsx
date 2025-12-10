import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Upload,
  Database,
  ShoppingCart,
  Network,
  Package,
  TrendingUp,
  Calendar,
  PieChart,
  Filter,
  Settings,
  LogOut,
  Menu,
  X,
  ChevronRight,
  Home
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, logout } = useAuth();

  const navItems = [
    { path: '/', icon: <Home size={20} />, label: 'Home' },
    { path: '/dashboard', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
    { path: '/data', icon: <Database size={20} />, label: 'Data Management' },
    { path: '/upload', icon: <Upload size={20} />, label: 'Upload Data' },
    { path: '/market-basket', icon: <ShoppingCart size={20} />, label: 'Market Basket' },
    { path: '/network', icon: <Network size={20} />, label: 'Network Graph' },
    { path: '/bundles', icon: <Package size={20} />, label: 'Product Bundles' },
    { path: '/revenue', icon: <TrendingUp size={20} />, label: 'Revenue Analysis' },
    { path: '/seasonal', icon: <Calendar size={20} />, label: 'Seasonal Analysis' },
    { path: '/clustering', icon: <PieChart size={20} />, label: 'Clustering' },
    { path: '/settings', icon: <Settings size={20} />, label: 'Settings' },
  ];

  return (
    <>
      {/* Mobile Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg shadow-lg"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40
          w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800
          transform transition-transform duration-300 ease-in-out
          lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}
          lg:block
        `}
      >
        <div className="h-full flex flex-col">
          {/* Logo */}
          <div className="p-6 border-b border-gray-200 dark:border-gray-800">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <ShoppingCart className="text-white" size={24} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">MBA Analytics</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Market Basket Analysis</p>
              </div>
            </div>
          </div>

          {/* User Info */}
          {user && (
            <div className="p-4 border-b border-gray-200 dark:border-gray-800">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 rounded-full flex items-center justify-center">
                  <span className="font-bold text-blue-600 dark:text-blue-300">
                    {user.name?.charAt(0) || 'U'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {user.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {user.company || 'Personal Account'}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-gray-400" />
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 p-4 overflow-y-auto">
            <div className="space-y-1">
              {navItems.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setIsOpen(false)}
                  className={({ isActive }) => `
                    flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-all
                    ${isActive
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-100 dark:border-blue-800'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800'
                    }
                  `}
                >
                  {item.icon}
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              ))}
            </div>

            {/* Algorithm Info */}
            <div className="mt-8 p-4 bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Powered by</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">FP-Growth</span>
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded-full">Active</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">Apriori</span>
                  <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 rounded-full">Available</span>
                </div>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">K-Means</span>
                  <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-300 rounded-full">Active</span>
                </div>
              </div>
            </div>
          </nav>

          {/* Logout Button */}
          {user && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-800">
              <button
                onClick={logout}
                className="flex items-center justify-center w-full space-x-2 px-4 py-2.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              >
                <LogOut size={18} />
                <span className="font-medium">Logout</span>
              </button>
            </div>
          )}
        </div>
      </aside>
    </>
  );
};

export default Sidebar;