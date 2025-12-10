import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUp, 
  Package, 
  DollarSign, 
  Users,
  Database,
  Zap,
  BarChart3,
  ShoppingCart,
  Clock,
  AlertCircle,
  ArrowRight,
  Upload
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

const Dashboard = () => {
  const { user } = useAuth();
  const { datasets, activeDataset } = useData();
  const [stats, setStats] = useState({
    totalTransactions: 0,
    uniqueProducts: 0,
    totalRevenue: 0,
    avgBasketSize: 0
  });

  useEffect(() => {
    // Load dashboard stats
    if (datasets.length > 0) {
      const active = datasets.find(d => d.id === activeDataset) || datasets[0];
      setStats({
        totalTransactions: active.rows,
        uniqueProducts: active.columns,
        totalRevenue: Math.floor(active.rows * 50), // Mock calculation
        avgBasketSize: Math.floor(Math.random() * 5) + 3
      });
    }
  }, [datasets, activeDataset]);

  const StatCard = ({ icon, title, value, change, color }) => (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold mt-2 text-gray-900 dark:text-white">{value}</p>
          {change && (
            <p className={`text-sm mt-1 flex items-center ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change > 0 ? '↑' : '↓'} {Math.abs(change)}%
              <span className="text-gray-500 dark:text-gray-400 ml-2">from last month</span>
            </p>
          )}
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const QuickAction = ({ icon, title, description, to, color }) => (
    <Link
      to={to}
      className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:border-blue-500 dark:hover:border-blue-500 transition-all group"
    >
      <div className="flex items-start space-x-4">
        <div className={`p-3 rounded-lg ${color} group-hover:scale-110 transition-transform`}>
          {icon}
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
            {title}
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{description}</p>
        </div>
        <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
      </div>
    </Link>
  );

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Welcome back, {user?.name}!</h1>
            <p className="text-blue-100 mt-2">
              {datasets.length > 0 
                ? `You have ${datasets.length} dataset${datasets.length !== 1 ? 's' : ''} ready for analysis`
                : 'Upload your first dataset to start analyzing customer patterns'
              }
            </p>
          </div>
          <div className="mt-4 md:mt-0">
            <Link
              to="/upload"
              className="inline-flex items-center space-x-2 px-6 py-3 bg-white text-blue-600 font-semibold rounded-xl hover:bg-gray-100 transition-colors"
            >
              <Upload className="w-5 h-5" />
              <span>Upload New Data</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon={<Database className="w-6 h-6 text-blue-600" />}
          title="Total Transactions"
          value={stats.totalTransactions.toLocaleString()}
          change={12}
          color="bg-blue-50 dark:bg-blue-900/30"
        />
        <StatCard
          icon={<Package className="w-6 h-6 text-green-600" />}
          title="Unique Products"
          value={stats.uniqueProducts}
          change={8}
          color="bg-green-50 dark:bg-green-900/30"
        />
        <StatCard
          icon={<DollarSign className="w-6 h-6 text-purple-600" />}
          title="Total Revenue"
          value={`$${(stats.totalRevenue / 1000).toFixed(1)}K`}
          change={15}
          color="bg-purple-50 dark:bg-purple-900/30"
        />
        <StatCard
          icon={<ShoppingCart className="w-6 h-6 text-yellow-600" />}
          title="Avg Basket Size"
          value={stats.avgBasketSize.toFixed(1)}
          change={3}
          color="bg-yellow-50 dark:bg-yellow-900/30"
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <QuickAction
            to="/upload"
            icon={<Upload className="w-6 h-6 text-blue-600" />}
            title="Upload Data"
            description="Upload new transaction data for analysis"
            color="bg-blue-100 dark:bg-blue-900"
          />
          <QuickAction
            to="/market-basket"
            icon={<BarChart3 className="w-6 h-6 text-green-600" />}
            title="Run Analysis"
            description="Generate association rules and patterns"
            color="bg-green-100 dark:bg-green-900"
          />
          <QuickAction
            to="/bundles"
            icon={<Package className="w-6 h-6 text-purple-600" />}
            title="Create Bundles"
            description="Design product bundles for cross-selling"
            color="bg-purple-100 dark:bg-purple-900"
          />
        </div>
      </div>

      {/* Recent Activity & Datasets */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Datasets */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Datasets</h3>
            <Link
              to="/data"
              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700"
            >
              View all
            </Link>
          </div>

          {datasets.length > 0 ? (
            <div className="space-y-4">
              {datasets.slice(0, 3).map((dataset) => (
                <div
                  key={dataset.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <Database className="w-5 h-5 text-blue-600" />
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{dataset.name}</h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {dataset.rows.toLocaleString()} rows • {dataset.format}
                      </p>
                    </div>
                  </div>
                  <Link
                    to="/market-basket"
                    className="px-3 py-1.5 text-sm bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800"
                  >
                    Analyze
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <Database className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No datasets uploaded yet</p>
              <Link
                to="/upload"
                className="inline-flex items-center space-x-2 mt-4 text-blue-600 dark:text-blue-400 font-medium"
              >
                <span>Upload your first dataset</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          )}
        </div>

        {/* Analysis Status */}
        <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Analysis Status</h3>
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">Ready</span>
            </div>
          </div>

          <div className="space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600 dark:text-gray-400">Algorithm Performance</span>
                <span className="font-medium text-gray-900 dark:text-white">85%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-green-500 to-emerald-600 h-2 rounded-full"
                  style={{ width: '85%' }}
                ></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600 dark:text-gray-400">Data Processing Speed</span>
                <span className="font-medium text-gray-900 dark:text-white">Fast</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
                  style={{ width: '92%' }}
                ></div>
              </div>
            </div>

            <div className="pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Clock className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">Last Analysis</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">2 hours ago</p>
                  </div>
                </div>
                <span className="px-3 py-1 text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded-full">
                  Completed
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Getting Started */}
      {datasets.length === 0 && (
        <div className="bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-2xl border border-gray-200 dark:border-gray-700 p-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800 mb-6">
              <AlertCircle className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Get Started with MBA Analytics
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-8 max-w-2xl mx-auto">
              Upload your transaction data to unlock powerful insights into customer buying patterns,
              product associations, and revenue optimization opportunities.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                to="/upload"
                className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 transition-all flex items-center justify-center space-x-2"
              >
                <Upload className="w-5 h-5" />
                <span>Upload First Dataset</span>
              </Link>
              <Link
                to="/guide"
                className="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 font-semibold border border-gray-300 dark:border-gray-700 rounded-xl hover:border-gray-400 dark:hover:border-gray-600 transition-all"
              >
                View Documentation
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;