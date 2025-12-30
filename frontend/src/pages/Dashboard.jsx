import { useState, useEffect } from 'react';
import axios from 'axios';
import {
  ShoppingCart,
  Package,
  Users,
  DollarSign,
  TrendingUp,
  BarChart3,
} from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [topProducts, setTopProducts] = useState([]);
  const [recentRules, setRecentRules] = useState([]);
  const [filters, setFilters] = useState({
    country: 'all',
    year: 'all',
    month: 'all',
    hour: 'all',
    product: 'all'
  });

  useEffect(() => {
    fetchDashboardData();
  }, [filters]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Fetch summary
      const summaryRes = await axios.get('/api/summary');
      if (summaryRes.data.success) {
        setSummary(summaryRes.data.data);
      }

      // Fetch top products
      const productsRes = await axios.get('/api/top_products', {
        params: { ...filters, limit: 5 }
      });
      if (productsRes.data.success) {
        setTopProducts(productsRes.data.products || []);
      }

      // Fetch recent rules
      const rulesRes = await axios.get('/api/association_rules', {
        params: { ...filters, limit: 5, simple: true }
      });
      if (rulesRes.data.success) {
        setRecentRules(rulesRes.data.data || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const statCards = [
    {
      title: 'Total Transactions',
      value: summary?.total_transactions?.toLocaleString() || '0',
      icon: ShoppingCart,
    },
    {
      title: 'Total Products',
      value: summary?.total_products?.toLocaleString() || '0',
      icon: Package,
    },
    {
      title: 'Total Customers',
      value: summary?.total_customers?.toLocaleString() || '0',
      icon: Users,
    },
    {
      title: 'Total Revenue',
      value: `$${summary?.total_revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0'}`,
      icon: DollarSign,
    },
  ];

  const productColumns = [
    { key: 'Description', title: 'Product', sortable: true },
    { 
      key: 'total_revenue', 
      title: 'Revenue', 
      sortable: true, 
      render: (value) => `$${typeof value === 'number' ? value.toFixed(2) : '0.00'}` 
    },
  ];

  const rulesColumns = [
    { key: 'rule', title: 'Association Rule', sortable: false },
    { 
      key: 'confidence', 
      title: 'Confidence', 
      sortable: true, 
      render: (value) => `${(typeof value === 'number' ? value * 100 : 0).toFixed(1)}%` 
    },
    { 
      key: 'lift', 
      title: 'Lift', 
      sortable: true, 
      render: (value) => typeof value === 'number' ? value.toFixed(2) : '0.00' 
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard Overview
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Real-time insights from your market basket analysis
        </p>
      </div>

      <FilterPanel onFilterChange={handleFilterChange} loading={loading} />

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat, index) => (
          <StatCard key={index} loading={loading} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Products */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Top Products by Revenue
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Best performing products
              </p>
            </div>
            <TrendingUp className="h-5 w-5 text-primary-600" />
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : (
            <DataTable
              columns={productColumns}
              data={topProducts}
              itemsPerPage={5}
              className="border-none shadow-none"
            />
          )}
        </div>

        {/* Recent Association Rules */}
        <div className="card">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                Recent Association Rules
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Latest product associations
              </p>
            </div>
            <BarChart3 className="h-5 w-5 text-primary-600" />
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : (
            <DataTable
              columns={rulesColumns}
              data={recentRules}
              itemsPerPage={5}
              className="border-none shadow-none"
            />
          )}
        </div>
      </div>
    </div>
  );
};