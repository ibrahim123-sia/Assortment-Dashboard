// pages/DataSummary.jsx
import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Database, BarChart, PieChart, LineChart } from 'lucide-react';

export const DataSummary = () => {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState(null);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    fetchDataSummary();
  }, []);

  const fetchDataSummary = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/summary');
      if (response.data.success) {
        setSummary(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching data summary:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner />;
  }

  if (!summary) {
    return (
      <div className="text-center py-12">
        <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          No data available
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Unable to load data summary
        </p>
      </div>
    );
  }

  const dataQualityItems = [
    { label: 'Total Records', value: summary.data_quality?.total_records?.toLocaleString() || '0' },
    { label: 'Data Completeness', value: `${summary.data_quality?.data_completeness || '0'}%` },
  ];

  const businessMetrics = [
    { label: 'Avg Transaction Value', value: `$${summary.avg_transaction_value?.toFixed(2) || '0.00'}` },
    { label: 'Total Countries', value: summary.total_countries || '0' },
  ];

  const dateRangeItems = [
    { label: 'Time Period', value: summary.date_range?.time_period || 'N/A' },
    { label: 'Data Status', value: 'Optimized' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Data Summary
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Comprehensive overview of your dataset and business metrics
        </p>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
              <Database className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Transactions
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {summary.total_transactions?.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
              <BarChart className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Revenue
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                ${summary.total_revenue?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
              <PieChart className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Products
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {summary.total_products?.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
              <LineChart className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Total Customers
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {summary.total_customers?.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Quality */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Data Quality Metrics
          </h3>
          <div className="space-y-4">
            {dataQualityItems.map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <span className="text-gray-600 dark:text-gray-400">{item.label}</span>
                <span className="font-medium text-gray-900 dark:text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Business Metrics */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Business Metrics
          </h3>
          <div className="space-y-4">
            {businessMetrics.map((item, index) => (
              <div key={index} className="flex justify-between items-center py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
                <span className="text-gray-600 dark:text-gray-400">{item.label}</span>
                <span className="font-medium text-gray-900 dark:text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Date Range */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Date Range
          </h3>
          <div className="space-y-3">
            {dateRangeItems.map((item, index) => (
              <div key={index} className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">{item.label}</span>
                <span className="font-medium text-gray-900 dark:text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Geographic Coverage */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Geographic Coverage
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Total Countries</span>
              <span className="font-medium text-gray-900 dark:text-white">
                {summary.total_countries}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Avg Transaction Value</span>
              <span className="font-medium text-gray-900 dark:text-white">
                ${summary.avg_transaction_value?.toFixed(2)}
              </span>
            </div>
          </div>
        </div>

        {/* Data Health */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Data Health Score
          </h3>
          <div className="text-center py-6">
            <div className="inline-flex items-center justify-center">
              <div className="relative">
                <svg className="w-32 h-32">
                  <circle
                    className="text-gray-200 dark:text-gray-700"
                    strokeWidth="10"
                    stroke="currentColor"
                    fill="transparent"
                    r="56"
                    cx="64"
                    cy="64"
                  />
                  <circle
                    className="text-green-500"
                    strokeWidth="10"
                    strokeLinecap="round"
                    stroke="currentColor"
                    fill="transparent"
                    r="56"
                    cx="64"
                    cy="64"
                    strokeDasharray={`${(summary.data_quality?.data_completeness || 0) * 3.52} 352`}
                    strokeDashoffset="0"
                    transform="rotate(-90 64 64)"
                  />
                </svg>
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <span className="text-3xl font-bold text-gray-900 dark:text-white">
                    {summary.data_quality?.data_completeness || 0}%
                  </span>
                </div>
              </div>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mt-4">
              Overall data completeness score
            </p>
          </div>
        </div>
      </div>

      {/* Performance Note */}
      <div className="card bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Performance Optimizations
        </h3>
        <div className="space-y-3">
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-green-600 dark:text-green-400">✓</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Data sampling enabled (max 20,000 records per query)
            </span>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-green-600 dark:text-green-400">✓</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Response compression and caching enabled
            </span>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-green-600 dark:text-green-400">✓</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Pagination and limits applied to all queries
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};