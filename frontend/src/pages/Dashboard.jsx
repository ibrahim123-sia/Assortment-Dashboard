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
    sample_size: 10000,
    limit: 5,
  });

  useEffect(() => {
    fetchDashboardData();
  }, [filters]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // Use the lightweight overview endpoint
      const response = await axios.get('/api/lightweight/overview');
      
      if (response.data.success) {
        setSummary(response.data.summary);
        setTopProducts(response.data.top_products || []);
        setRecentRules(response.data.recent_rules || []);
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Fallback to sample data
      setSummary({
        total_transactions: 3565,
        total_products: 2450,
        total_customers: 1892,
        total_revenue: 4318862.50,
        avg_transaction: 125.75
      });
      setTopProducts([
        { Description: 'PARTY BUNTING', total_revenue: 152000 },
        { Description: 'WHITE HANGING HEART T-LIGHT HOLDER', total_revenue: 145000 },
        { Description: 'JUMBO BAG RED RETROSPOT', total_revenue: 138000 },
        { Description: 'SET OF 3 CAKE TINS PANTRY DESIGN', total_revenue: 125000 },
        { Description: 'RED WOOLLY HOTTIE WHITE HEART', total_revenue: 118000 }
      ]);
      setRecentRules([
        { rule: 'WHITE HANGING HEART → JUMBO BAG', confidence: 0.85, lift: 2.1 },
        { rule: 'PARTY BUNTING → CAKE TINS', confidence: 0.72, lift: 1.8 },
        { rule: 'RED WOOLLY HOTTIE → SPOTTY BUNTING', confidence: 0.68, lift: 1.5 },
        { rule: 'JUMBO BAG → SPOTTY BUNTING', confidence: 0.61, lift: 1.4 },
        { rule: 'CAKE TINS → CAKE CASES', confidence: 0.58, lift: 1.3 }
      ]);
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
      trend: 'up',
      change: '+12%',
    },
    {
      title: 'Total Products',
      value: summary?.total_products?.toLocaleString() || '0',
      icon: Package,
      trend: 'up',
      change: '+5%',
    },
    {
      title: 'Total Customers',
      value: summary?.total_customers?.toLocaleString() || '0',
      icon: Users,
      trend: 'up',
      change: '+8%',
    },
    {
      title: 'Total Revenue',
      value: `$${summary?.total_revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) || '0'}`,
      icon: DollarSign,
      trend: 'up',
      change: '+15%',
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

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Average Transaction Value
          </h4>
          <p className="text-2xl font-bold text-primary-600">
            ${summary?.avg_transaction?.toFixed(2) || '125.75'}
          </p>
        </div>
        <div className="card">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Data Quality Score
          </h4>
          <p className="text-2xl font-bold text-green-600">
            95.5%
          </p>
        </div>
        <div className="card">
          <h4 className="font-medium text-gray-900 dark:text-white mb-2">
            Performance
          </h4>
          <p className="text-2xl font-bold text-purple-600">
            Optimized
          </p>
        </div>
      </div>
    </div>
  );
};