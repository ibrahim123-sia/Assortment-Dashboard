import { NavLink } from 'react-router-dom';
import {
  Home,
  Link,
  Package,
  TrendingUp,
  Calendar,
  Database,
  Settings
} from 'lucide-react';

const menuItems = [
  { icon: Home, label: 'Dashboard', path: '/' },
  { icon: Link, label: 'Association Rules', path: '/association-rules' },
  { icon: Package, label: 'Product Bundles', path: '/product-bundles' },
  { icon: TrendingUp, label: 'Revenue Analysis', path: '/revenue-analysis' },
  { icon: Calendar, label: 'Seasonal Analysis', path: '/seasonal-analysis' },

  { icon: Database, label: 'Data Summary', path: '/data-summary' },
];

export const Sidebar = ({ isOpen }) => {
  return (
    <aside
      className={`${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transform transition-transform duration-200 ease-in-out lg:translate-x-0 lg:static lg:inset-0`}
    >
      <div className="h-full flex flex-col">
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {menuItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400 border border-primary-100 dark:border-primary-800'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                }`
              }
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        
        <div className="p-4 border-t border-gray-200 dark:border-gray-800">
          
          <div className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
            <p>v1.0.0</p>
            <p className="mt-1">© 2024 MBA Dashboard</p>
          </div>
        </div>
      </div>
    </aside>
  );
};