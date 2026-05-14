import { BarChart3 } from 'lucide-react';

export const AuthLayout = ({ children, title, subtitle }) => {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <BarChart3 className="h-12 w-12 text-primary-600" />
          <h1 className="mt-3 text-2xl font-bold text-gray-900 dark:text-white">Assortment Dashboard</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400">Market Basket Analytics Platform</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8 border border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-1">{title}</h2>
          {subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">{subtitle}</p>}
          {children}
        </div>
      </div>
    </div>
  );
};
