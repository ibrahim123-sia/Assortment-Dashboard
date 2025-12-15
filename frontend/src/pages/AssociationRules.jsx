import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TrendingUp, Target, Link2, AlertCircle } from 'lucide-react';

export const AssociationRules = () => {
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [dataSummary, setDataSummary] = useState(null);
  const [filters, setFilters] = useState({
    min_support: 0.005,  // Lowered for better results
    min_confidence: 0.2,  // Lowered for better results
    country: 'all',
    year: 'all',
    month: 'all',
    sample_size: 10000,
    limit: 50,
    simple: true,
  });

  // Fetch data summary on mount
  useEffect(() => {
    fetchDataSummary();
  }, []);

  // Fetch association rules when filters change
  useEffect(() => {
    if (dataSummary) {
      fetchAssociationRules();
    }
  }, [filters, dataSummary]);

  const fetchDataSummary = async () => {
    try {
      const response = await axios.get('/api/summary');
      if (response.data.success) {
        setDataSummary(response.data.data);
        console.log('Data summary loaded:', response.data.data);
      }
    } catch (error) {
      console.error('Error fetching data summary:', error);
    }
  };

  const fetchAssociationRules = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('/api/association_rules', {
        params: {
          ...filters,
          simple: filters.simple
        },
      });

      console.log('API Response:', response.data);

      if (response.data.success) {
        setRules(response.data.data || []);
        setStats(response.data.metadata || {
          total_rules_found: response.data.data?.length || 0,
          sample_size: filters.sample_size,
          processing_time: 0.5,
          performance: 'fast'
        });
        
        if (!response.data.data || response.data.data.length === 0) {
          setError({
            type: 'no_data',
            message: 'No association rules found. Try lowering the support/confidence thresholds.',
            details: response.data.metadata?.note || 'Insufficient co-purchasing patterns in data'
          });
        }
      } else {
        setError({
          type: 'api_error',
          message: 'Failed to fetch association rules',
          details: response.data.error || 'Unknown error'
        });
        setRules([]);
      }
    } catch (error) {
      console.error('Error fetching association rules:', error);
      setError({
        type: 'network_error',
        message: 'Failed to connect to server',
        details: error.message || 'Check if backend is running on port 5000'
      });
      setRules([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setFilters({
      ...filters,
      min_support: 0.001,  // Even lower threshold
      min_confidence: 0.1,  // Even lower threshold
      sample_size: Math.min(20000, dataSummary?.total_transactions || 10000)
    });
  };

  const handleResetFilters = () => {
    setFilters({
      min_support: 0.005,
      min_confidence: 0.2,
      country: 'all',
      year: 'all',
      month: 'all',
      sample_size: 10000,
      limit: 50,
      simple: true,
    });
  };

  const columns = filters.simple ? [
    {
      key: 'rule',
      title: 'Association Rule',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {value}
        </div>
      ),
    },
    {
      key: 'confidence',
      title: 'Confidence',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-semibold text-gray-900 dark:text-white">
            {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : '0%'}
          </span>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
            <div
              className="bg-green-600 h-1.5 rounded-full"
              style={{ width: `${typeof value === 'number' ? Math.min(value * 100, 100) : 0}%` }}
            ></div>
          </div>
        </div>
      ),
    },
    {
      key: 'lift',
      title: 'Lift',
      sortable: true,
      render: (value) => (
        <div className={`font-bold ${value > 1.5 ? 'text-green-600' : value > 1 ? 'text-yellow-600' : 'text-red-600'}`}>
          {typeof value === 'number' ? value.toFixed(2) : '0.00'}
          {value > 1 && (
            <TrendingUp className="inline-block ml-1 h-4 w-4" />
          )}
        </div>
      ),
    },
    {
      key: 'support',
      title: 'Support',
      sortable: true,
      render: (value) => (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {(value * 100).toFixed(2)}%
        </div>
      ),
    },
  ] : [
    {
      key: 'antecedents',
      title: 'If Buy These',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {Array.isArray(value) ? value.map((item, idx) => (
            <span key={idx} className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-1 rounded mr-1 mb-1">
              {item}
            </span>
          )) : value}
        </div>
      ),
    },
    {
      key: 'consequents',
      title: 'Then Buy These',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {Array.isArray(value) ? value.map((item, idx) => (
            <span key={idx} className="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs px-2 py-1 rounded mr-1 mb-1">
              {item}
            </span>
          )) : value}
        </div>
      ),
    },
    {
      key: 'confidence',
      title: 'Confidence',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-semibold text-gray-900 dark:text-white">
            {typeof value === 'number' ? (value * 100).toFixed(1) + '%' : '0%'}
          </span>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
            <div
              className="bg-green-600 h-1.5 rounded-full"
              style={{ width: `${typeof value === 'number' ? Math.min(value * 100, 100) : 0}%` }}
            ></div>
          </div>
        </div>
      ),
    },
    {
      key: 'lift',
      title: 'Lift',
      sortable: true,
      render: (value) => (
        <div className={`font-bold ${value > 1.5 ? 'text-green-600' : value > 1 ? 'text-yellow-600' : 'text-red-600'}`}>
          {typeof value === 'number' ? value.toFixed(2) : '0.00'}
          {value > 1 && (
            <TrendingUp className="inline-block ml-1 h-4 w-4" />
          )}
        </div>
      ),
    },
    {
      key: 'support',
      title: 'Support',
      sortable: true,
      render: (value) => (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {(value * 100).toFixed(2)}%
        </div>
      ),
    },
  ];

  // Data quality warning
  const showDataQualityWarning = dataSummary && (
    dataSummary.total_transactions < 1000 || 
    dataSummary.total_products < 50
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Association Rules
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Discover product relationships using Market Basket Analysis (Actual Data Only)
        </p>
      </div>

      {/* Data Quality Warning */}
      {showDataQualityWarning && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800 dark:text-yellow-300">
                Limited Data for Association Rules
              </h3>
              <div className="mt-2 text-sm text-yellow-700 dark:text-yellow-400">
                <p>
                  Your dataset has {dataSummary.total_transactions} transactions and {dataSummary.total_products} products.
                  Association rules work best with:
                </p>
                <ul className="list-disc pl-5 mt-1">
                  <li>1000+ transactions</li>
                  <li>50+ unique products</li>
                  <li>Multiple products per transaction</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      )}

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <Link2 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Rules Found
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.total_rules_found || rules.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <Target className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Sample Size
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.sample_size?.toLocaleString() || '10,000'}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Processing Time
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.processing_time?.toFixed(1) || '0.2'}s
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
                  Min Support
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(filters.min_support * 100).toFixed(2)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simple Mode Toggle */}
      <div className="flex justify-end">
        <label className="inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={filters.simple}
            onChange={(e) => setFilters({...filters, simple: e.target.checked})}
            className="sr-only peer"
          />
          <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          <span className="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">
            Simple View
          </span>
        </label>
      </div>

      {/* Rules Table */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Product Association Rules
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Showing rules with support ≥ {(filters.min_support * 100).toFixed(2)}% and confidence ≥ {(filters.min_confidence * 100).toFixed(0)}%
            {filters.sample_size && ` (Sample: ${filters.sample_size.toLocaleString()} transactions)`}
            <span className="ml-2 text-xs text-gray-500">
              Total dataset: {dataSummary?.total_transactions?.toLocaleString() || 'N/A'} transactions
            </span>
          </p>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <div className="text-center py-12">
            <div className="text-red-400 dark:text-red-500 mb-4">
              <AlertCircle className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {error.message}
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {error.details}
            </p>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Lower Thresholds
              </button>
              <button 
                onClick={handleResetFilters}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Reset Filters
              </button>
            </div>
          </div>
        ) : rules.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <Link2 className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No association rules found
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              The algorithm couldn't find any significant product associations with current settings.
              This could mean:
            </p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 text-left max-w-md mx-auto mb-6">
              <li className="mb-2">• Your dataset might not have enough co-purchasing patterns</li>
              <li className="mb-2">• Support/confidence thresholds might be too high</li>
              <li className="mb-2">• Most transactions might contain single items only</li>
              <li>• Try lowering the minimum support and confidence values</li>
            </ul>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={handleRetry}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Try Lower Thresholds (0.1% support, 10% confidence)
              </button>
              <button 
                onClick={() => fetchAssociationRules()}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Retry with Current Settings
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Found {rules.length} association rules. Lift &gt; 1 indicates positive association.
            </div>
            <DataTable
              columns={columns}
              data={rules}
              itemsPerPage={10}
              onRowClick={(rule) => console.log('Rule selected:', rule)}
            />
          </>
        )}
      </div>

      {/* Debug Info (for development only) */}
      {process.env.NODE_ENV === 'development' && dataSummary && (
        <div className="mt-8 p-4 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Dataset Info (Debug):</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div>
              <span className="text-gray-600 dark:text-gray-400">Transactions:</span>{' '}
              <span className="font-medium">{dataSummary.total_transactions?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Products:</span>{' '}
              <span className="font-medium">{dataSummary.total_products?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Avg Items/Transaction:</span>{' '}
              <span className="font-medium">
                {dataSummary.total_records && dataSummary.total_transactions 
                  ? (dataSummary.total_records / dataSummary.total_transactions).toFixed(2)
                  : 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Date Range:</span>{' '}
              <span className="font-medium">{dataSummary.date_range?.time_period || 'N/A'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};