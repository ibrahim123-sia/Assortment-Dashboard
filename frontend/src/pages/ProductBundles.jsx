import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Package, TrendingUp, DollarSign, Tag, RefreshCw, AlertCircle, ShoppingCart } from 'lucide-react';

export const ProductBundles = () => {
  const [loading, setLoading] = useState(false);
  const [bundles, setBundles] = useState([]);
  const [metadata, setMetadata] = useState(null);
  const [filters, setFilters] = useState({
    min_confidence: 0.3,
    min_transactions: 5,
    country: 'all',
    year: 'all',
    month: 'all',
    hour: 'all',
    product: 'all',
    weekday: 'all'
  });

  useEffect(() => {
    fetchBundles();
  }, [filters]);

  const fetchBundles = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/suggested_bundles', {
        params: filters,
      });

      if (response.data.success) {
        setBundles(response.data.bundles || []);
        setMetadata(response.data.metadata || null);
      } else {
        console.error('API returned error:', response.data.error);
        setBundles([]);
        setMetadata(null);
      }
    } catch (error) {
      console.error('Error fetching bundles:', error);
      setBundles([]);
      setMetadata(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    fetchBundles();
  };

  const handleResetFilters = () => {
    setFilters({
      min_confidence: 0.3,
      min_transactions: 5,
      country: 'all',
      year: 'all',
      month: 'all',
      hour: 'all',
      product: 'all',
      weekday: 'all'
    });
  };

  const columns = [
    {
      key: 'bundle_id',
      title: 'Bundle ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono font-bold text-blue-600 dark:text-blue-400">{value}</span>
      ),
    },
    {
      key: 'bundle_name',
      title: 'Bundle Name',
      sortable: true,
      render: (value, row) => (
        <div>
          <div className="font-medium text-gray-900 dark:text-white">
            {value}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">
            {row.products?.slice(0, 2).map(p => p.substring(0, 20)).join(' + ')}
            {row.products?.length > 2 && ` + ${row.products.length - 2} more`}
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
          <div className="flex items-center justify-center">
            <ShoppingCart className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">{value || 0}</span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">occurrences</div>
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
            {(value * 100).toFixed(1)}%
          </span>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
            <div
              className="bg-green-600 h-1.5 rounded-full"
              style={{ width: `${Math.min(value * 100, 100)}%` }}
            ></div>
          </div>
        </div>
      ),
    },
    {
      key: 'estimated_revenue',
      title: 'Est. Revenue',
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              ${typeof value === 'number' ? value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00'}
            </span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">total revenue</div>
        </div>
      ),
    },
    {
      key: 'lift',
      title: 'Lift',
      sortable: true,
      render: (value) => (
        <div
          className={`font-bold text-center ${
            value > 1.5
              ? 'text-green-600'
              : value > 1
              ? 'text-yellow-600'
              : 'text-red-600'
          }`}
        >
          {typeof value === 'number' ? value.toFixed(2) : '0.00'}
        </div>
      ),
    },
  ];

  // Calculate stats
  const totalRevenue = bundles.reduce((acc, b) => acc + (b.estimated_revenue || 0), 0);
  const avgConfidence = bundles.length > 0 
    ? bundles.reduce((acc, b) => acc + (b.confidence || 0), 0) / bundles.length 
    : 0;
  const totalTransactions = bundles.reduce((acc, b) => acc + (b.transaction_count || 0), 0);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Suggested Product Bundles
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Intelligent product bundles based on co-purchase patterns
        </p>
      </div>

      {/* Quick Actions */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => setFilters({...filters, min_confidence: 0.2})}
          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Package className="h-4 w-4 mr-2" />
          Lower Confidence (20%)
        </button>
        <button
          onClick={() => setFilters({...filters, min_transactions: 2})}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <ShoppingCart className="h-4 w-4 mr-2" />
          Minimum 2 Transactions
        </button>
        <button
          onClick={handleResetFilters}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Reset Filters
        </button>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Bundle Stats */}
      {!loading && bundles.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <Package className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Bundles
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {bundles.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <Tag className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${totalRevenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <DollarSign className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Avg. Confidence
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(avgConfidence * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
                <TrendingUp className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Transactions
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totalTransactions}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Bundles Table */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Recommended Product Bundles
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Suggested bundles based on co-purchase patterns with confidence ≥ {(filters.min_confidence * 100).toFixed(0)}%
            {metadata?.filtered_records && ` • From ${metadata.filtered_records.toLocaleString()} filtered records`}
          </p>
        </div>

        {loading ? (
          <LoadingSpinner text="Finding product bundles..." />
        ) : bundles.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <Package className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No bundles found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              This could be because:
            </p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 text-left max-w-md mx-auto mb-6 space-y-2">
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Confidence threshold is too high (try 20% instead of 30%)</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Minimum transaction count is too high (try 2 instead of 5)</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Filters are too restrictive (try removing filters)</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Dataset has few co-purchased products</span>
              </li>
            </ul>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => setFilters({...filters, min_confidence: 0.2, min_transactions: 2})}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Try Lower Thresholds
              </button>
              <button 
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="inline-block h-4 w-4 mr-1" />
                Retry
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Found {bundles.length} product bundles from {metadata?.top_products_analyzed || 0} top products. 
              Lift &gt; 1 indicates products are purchased together more often than expected.
            </div>
            <DataTable
              columns={columns}
              data={bundles}
              itemsPerPage={10}
              onRowClick={(bundle) => console.log('Bundle selected:', bundle)}
            />
            {metadata && (
              <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                Analyzed {metadata.top_products_analyzed} top products • 
                Minimum {metadata.min_transactions} transactions per bundle • 
                Filtered from {metadata.filtered_records} records
              </div>
            )}
          </>
        )}
      </div>

      {/* Action Section */}
      {!loading && bundles.length > 0 && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                Ready to implement these bundles?
              </h4>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                These bundles are based on actual customer purchase patterns with {bundles.length} unique combinations
              </p>
            </div>
            <div className="flex space-x-3 mt-4 md:mt-0">
              <button 
                onClick={() => {
                  const csvContent = bundles.map(b => ({
                    'Bundle ID': b.bundle_id,
                    'Products': b.products.join(';'),
                    'Confidence': `${(b.confidence * 100).toFixed(1)}%`,
                    'Lift': b.lift.toFixed(2),
                    'Transactions': b.transaction_count,
                    'Estimated Revenue': `$${b.estimated_revenue.toFixed(2)}`
                  }));
                  console.log('Exporting bundles:', csvContent);
                  alert('Export functionality would be implemented here');
                }}
                className="btn-secondary flex items-center"
              >
                <Package className="h-4 w-4 mr-2" />
                Export as CSV
              </button>
              <button 
                onClick={() => {
                  const topBundle = bundles.sort((a, b) => b.confidence - a.confidence)[0];
                  alert(`Create promotion for: ${topBundle.bundle_name}\nProducts: ${topBundle.products.join(', ')}\nConfidence: ${(topBundle.confidence * 100).toFixed(1)}%`);
                }}
                className="btn-primary flex items-center"
              >
                <DollarSign className="h-4 w-4 mr-2" />
                Create Top Promotion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};