import React from 'react';
import { Bell, Search, User, HelpCircle, Database, Zap } from 'lucide-react';
import ThemeToggle from './ThemeToggle';
import { useAuth } from '../../context/AuthContext';
import { useData } from '../../context/DataContext';

const Header = ({ title, onSearch }) => {
  const { user } = useAuth();
  const { datasets, activeDataset } = useData();

  return (
    <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-900/80 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left Section */}
          <div className="flex-1">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Market Basket Analysis Dashboard
                </p>
              </div>
              
              {/* Dataset Selector */}
              {datasets.length > 0 && (
                <div className="hidden md:flex items-center space-x-2 px-3 py-1.5 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                  <Database className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {datasets.find(d => d.id === activeDataset)?.name || 'Select Dataset'}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    ({datasets.length} datasets)
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Right Section */}
          <div className="flex items-center space-x-3">
            {/* Search */}
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search analysis, products..."
                className="pl-10 pr-4 py-2 w-64 bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                onChange={(e) => onSearch(e.target.value)}
              />
            </div>

            {/* Quick Stats */}
            <div className="hidden lg:flex items-center space-x-4">
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-900 dark:text-white">
                  {datasets.length}
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Datasets</div>
              </div>
              <div className="text-center">
                <div className="text-sm font-semibold text-gray-900 dark:text-white flex items-center">
                  <Zap className="w-3 h-3 text-yellow-500 mr-1" />
                  85%
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">Accuracy</div>
              </div>
            </div>

            {/* Icons */}
            <ThemeToggle />
            
            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg relative">
              <Bell className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            <button className="p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
              <HelpCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>

            {/* User Avatar */}
            {user && (
              <div className="flex items-center space-x-2 pl-3 border-l border-gray-200 dark:border-gray-800">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 rounded-full flex items-center justify-center">
                  <span className="font-bold text-blue-600 dark:text-blue-300 text-sm">
                    {user.name?.charAt(0) || 'U'}
                  </span>
                </div>
                <div className="hidden md:block">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{user.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">{user.plan} Plan</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;