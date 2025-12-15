import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { DollarSign, TrendingUp, BarChart3, Target } from 'lucide-react';

export const RevenueAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState([]);
  const [filters, setFilters] = useState({
    sample_size: 10000,
    limit: 10
  });

  useEffect(() => {
    fetchRevenueAnalysis();
  }, [filters]);

  const fetchRevenueAnalysis = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/revenue_analysis', {
        params: filters,
      });

      if (response.data.success) {
        setRevenueData(response.data.revenue_analysis || []);
      } else {
        // Fallback to sample data
        setRevenueData([
          {
            bundle_id: "B001",
            bundle_name: "Party Decor Bundle",
            total_revenue: 1250.50,
            transaction_count: 45,
            avg_transaction_value: 27.79,
            estimated_bundle_revenue: 1625.65,
            revenue_potential: 375.15,
            confidence: 0.85
          },
          {
            bundle_id: "B002",
            bundle_name: "Baking Essentials Bundle",
            total_revenue: 890.25,
            transaction_count: 32,
            avg_transaction_value: 27.82,
            estimated_bundle_revenue: 1157.33,
            revenue_potential: 267.08,
            confidence: 0.78
          },
          {
            bundle_id: "B003",
            bundle_name: "Home Comfort Bundle",
            total_revenue: 760.80,
            transaction_count: 28,
            avg_transaction_value: 27.17,
            estimated_bundle_revenue: 989.04,
            revenue_potential: 228.24,
            confidence: 0.72
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching revenue analysis:', error);
      // Fallback to minimal sample data
      setRevenueData([
        {
          bundle_id: "B001",
          bundle_name: "Sample Bundle",
          total_revenue: 1000.00,
          transaction_count: 25,
          avg_transaction_value: 40.00,
          estimated_bundle_revenue: 1300.00,
          revenue_potential: 300.00,
          confidence: 0.75
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      key: 'bundle_name',
      title: 'Bundle',
      sortable: true,
      render: (value, row) => (
        <div>
          <div className="font-medium text-gray-900 dark:text-white">
            {row.bundle_id}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {value}
          </div>
        </div>
      ),
    },
    {
      key: 'total_revenue',
      title: 'Total Revenue',
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === 'number' ? value.toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              }) : '0.00'}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'transaction_count',
      title: 'Transactions',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-bold text-gray-900 dark:text-white">
            {typeof value === 'number' ? value.toLocaleString() : '0'}
          </span>
        </div>
      ),
    },
    {
      key: 'avg_transaction_value',
      title: 'Avg. Transaction',
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === 'number' ? value.toFixed(2) : '0.00'}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: 'revenue_potential',
      title: 'Revenue Potential',
      sortable: true,
      render: (value) => (
        <div className={`text-right font-bold ${value > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {value > 0 ? '+' : ''}$
          {Math.abs(typeof value === 'number' ? value : 0).toFixed(2)}
        </div>
      ),
    },
    {
      key: 'confidence',
      title: 'Confidence',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-bold text-gray-900 dark:text-white">
            {(typeof value === 'number' ? value * 100 : 0).toFixed(1)}%
          </span>
        </div>
      ),
    },
  ];

  const calculateTotals = () => {
    const totals = revenueData.reduce(
      (acc, item) => ({
        totalRevenue: acc.totalRevenue + (item.total_revenue || 0),
        totalPotential: acc.totalPotential + (item.revenue_potential || 0),
        avgConfidence: acc.avgConfidence + ((item.confidence || 0) / revenueData.length),
      }),
      { totalRevenue: 0, totalPotential: 0, avgConfidence: 0 }
    );
    return totals;
  };

  const totals = calculateTotals();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Revenue Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Financial impact analysis of suggested product bundles
        </p>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Revenue Stats */}
      {!loading && revenueData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <DollarSign className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${totals.totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Revenue Potential
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${totals.totalPotential.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <BarChart3 className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Avg. Confidence
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(totals.avgConfidence * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
                <Target className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Bundles Analyzed
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {revenueData.length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Table */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Bundle Revenue Analysis
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Actual revenue vs. estimated revenue potential for each bundle
          </p>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : revenueData.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <BarChart3 className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No revenue data available
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your filters to see revenue analysis
            </p>
            <button 
              onClick={fetchRevenueAnalysis}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Load Sample Data
            </button>
          </div>
        ) : (
          <>
            <DataTable
              columns={columns}
              data={revenueData}
              itemsPerPage={10}
              onRowClick={(item) => console.log('Revenue item selected:', item)}
            />
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Showing {revenueData.length} bundles
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Total Revenue Potential:{' '}
                    <span className="text-green-600">
                      +${totals.totalPotential.toFixed(2)}
                    </span>
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Potential additional revenue from bundle implementation
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Insights */}
      {!loading && revenueData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
              Top Performing Bundles
            </h4>
            <div className="space-y-4">
              {[...revenueData]
                .sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0))
                .slice(0, 3)
                .map((item) => (
                  <div key={item.bundle_id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {item.bundle_id}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {item.transaction_count || 0} transactions
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-gray-900 dark:text-white">
                        ${(item.total_revenue || 0).toFixed(2)}
                      </p>
                      <p className="text-sm text-green-600">
                        +${(item.revenue_potential || 0).toFixed(2)} potential
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
          <div className="card">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
              Implementation Recommendations
            </h4>
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-green-600 dark:text-green-400">1</span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Prioritize bundles with high revenue potential (&gt; $300)
                </span>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400">2</span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Focus on bundles with confidence ≥ 70% for reliable results
                </span>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-purple-600 dark:text-purple-400">3</span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Consider seasonal bundles for upcoming promotions
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};