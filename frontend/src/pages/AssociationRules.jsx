import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TrendingUp, Target, Link2, AlertCircle, Zap, RefreshCw } from 'lucide-react';

export const AssociationRules = () => {
  const [loading, setLoading] = useState(false);
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState(null);
  const [dataSummary, setDataSummary] = useState(null);
  const [filters, setFilters] = useState({
    min_support: 0.01,
    min_confidence: 0.3,
    country: 'all',
    year: 'all',
    month: 'all',
    hour: 'all',
    product: 'all',
    simple: true,
  });

  // Fetch data summary on mount
  useEffect(() => {
    fetchDataSummary();
  }, []);

  // Fetch association rules when filters change
  useEffect(() => {
    fetchAssociationRules();
  }, [filters]);

  const fetchDataSummary = async () => {
    try {
      const response = await axios.get('/api/summary');
      if (response.data.success) {
        setDataSummary(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching data summary:', error);
    }
  };

  const fetchAssociationRules = async () => {
    setLoading(true);
    setError(null);
    
    try {
      console.log('Fetching with filters:', filters);
      
      const response = await axios.get('/api/association_rules', {
        params: {
          ...filters,
          limit: 50,
          simple: false  // Always get full data for both views
        },
      });

      console.log('API Response:', response.data);

      if (response.data.success) {
        const rulesData = response.data.data || [];
        console.log('Rules received:', rulesData.length);
        
        // Transform data for both simple and detailed views
        const formattedRules = rulesData.map(rule => {
          // For simple view
          const antecedent = rule.antecedent || (rule.antecedents ? rule.antecedents[0] : '');
          const consequent = rule.consequent || (rule.consequents ? rule.consequents[0] : '');
          
          return {
            // For simple view columns
            rule: `${antecedent} → ${consequent}`,
            confidence: rule.confidence,
            lift: rule.lift,
            support: rule.support,
            
            // For detailed view columns
            antecedents: rule.antecedents || [antecedent],
            consequents: rule.consequents || [consequent],
            
            // Keep original data
            antecedent: antecedent,
            consequent: consequent
          };
        });
        
        setRules(formattedRules);
        setStats(response.data.metadata || {
          total_rules_found: formattedRules.length,
          processing_time: 0.5,
        });
        
        if (formattedRules.length === 0) {
          setError({
            type: 'no_data',
            message: 'No association rules found',
            details: response.data.metadata?.note || 'Try adjusting support/confidence values',
            suggestions: [
              'Lower minimum support to 0.5%',
              'Lower minimum confidence to 20%',
              'Remove product filter if applied'
            ]
          });
        } else {
          setError(null);
        }
      } else {
        setError({
          type: 'api_error',
          message: 'API returned an error',
          details: response.data.error || 'Unknown error'
        });
        setRules([]);
      }
    } catch (error) {
      console.error('Error fetching association rules:', error);
      setError({
        type: 'network_error',
        message: 'Failed to connect to server',
        details: 'Make sure the Python backend is running on port 5000',
        suggestions: [
          'Open terminal and run: python app.py',
          'Check if dataset file exists in data/ folder',
          'Wait for backend to fully start'
        ]
      });
      setRules([]);
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickRetry = (support, confidence) => {
    setFilters({
      ...filters,
      min_support: support,
      min_confidence: confidence
    });
  };

  const handleResetFilters = () => {
    setFilters({
      min_support: 0.01,
      min_confidence: 0.3,
      country: 'all',
      year: 'all',
      month: 'all',
      hour: 'all',
      product: 'all',
      simple: true,
    });
  };

  // Define columns for both views
  const simpleColumns = [
    {
      key: 'rule',
      title: 'Association Rule',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {value || 'No product name'}
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

  const detailedColumns = [
    {
      key: 'antecedents',
      title: 'If Buy These',
      sortable: false,
      render: (value) => {
        const antecedents = Array.isArray(value) ? value : [value];
        return (
          <div className="font-medium text-gray-900 dark:text-white">
            {antecedents.map((item, idx) => (
              <span key={idx} className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-1 rounded mr-1 mb-1">
                {item || 'Unknown Product'}
              </span>
            ))}
          </div>
        );
      },
    },
    {
      key: 'consequents',
      title: 'Then Buy These',
      sortable: false,
      render: (value) => {
        const consequents = Array.isArray(value) ? value : [value];
        return (
          <div className="font-medium text-gray-900 dark:text-white">
            {consequents.map((item, idx) => (
              <span key={idx} className="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs px-2 py-1 rounded mr-1 mb-1">
                {item || 'Unknown Product'}
              </span>
            ))}
          </div>
        );
      },
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

  // Use appropriate columns based on view mode
  const columns = filters.simple ? simpleColumns : detailedColumns;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Association Rules
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Discover product relationships using Market Basket Analysis
        </p>
      </div>

      {/* Quick Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => handleQuickRetry(0.005, 0.2)}
          className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
        >
          <Zap className="h-4 w-4 mr-2" />
          Easy Mode (0.5% support, 20% confidence)
        </button>
        <button
          onClick={() => handleQuickRetry(0.01, 0.3)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Target className="h-4 w-4 mr-2" />
          Balanced (1% support, 30% confidence)
        </button>
        <button
          onClick={handleResetFilters}
          className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Reset All Filters
        </button>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <Link2 className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Rules Found
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
                  Min Support
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(filters.min_support * 100).toFixed(1)}%
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
                  Min Confidence
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(filters.min_confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* View Mode Toggle */}
      <div className="flex justify-between items-center">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          {stats?.note && (
            <div className="flex items-center">
              <AlertCircle className="h-4 w-4 mr-2 text-blue-500" />
              <span>{stats.note}</span>
            </div>
          )}
        </div>
        <label className="inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={filters.simple}
            onChange={(e) => setFilters({...filters, simple: e.target.checked})}
            className="sr-only peer"
          />
          <div className="relative w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
          <span className="ml-3 text-sm font-medium text-gray-900 dark:text-gray-300">
            {filters.simple ? 'Simple View' : 'Detailed View'}
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
            {filters.simple ? (
              <>Simple view showing product relationships</>
            ) : (
              <>Detailed view showing antecedent and consequent products</>
            )}
          </p>
        </div>

        {loading ? (
          <LoadingSpinner text="Generating association rules..." />
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
            
            {error.suggestions && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-4 mb-6 max-w-md mx-auto">
                <h4 className="font-medium text-yellow-800 dark:text-yellow-300 mb-2">
                  Try these solutions:
                </h4>
                <ul className="text-sm text-yellow-700 dark:text-yellow-400 text-left space-y-1">
                  {error.suggestions.map((suggestion, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="mr-2">•</span>
                      <span>{suggestion}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => handleQuickRetry(0.005, 0.2)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Try Easy Mode
              </button>
              <button 
                onClick={fetchAssociationRules}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <RefreshCw className="inline-block h-4 w-4 mr-1" />
                Retry
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
              This usually happens when:
            </p>
            <ul className="text-sm text-gray-600 dark:text-gray-400 text-left max-w-md mx-auto mb-6 space-y-2">
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Support threshold is too high (try 0.5% instead of 1%)</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Confidence threshold is too high (try 20% instead of 30%)</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Product filter is too restrictive</span>
              </li>
              <li className="flex items-start">
                <AlertCircle className="h-4 w-4 mr-2 mt-0.5 text-yellow-500" />
                <span>Dataset has few multi-item transactions</span>
              </li>
            </ul>
            <div className="flex justify-center space-x-4">
              <button 
                onClick={() => handleQuickRetry(0.005, 0.2)}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Try Easy Mode (0.5% support, 20% confidence)
              </button>
              <button 
                onClick={handleResetFilters}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                Remove All Filters
              </button>
            </div>
          </div>
        ) : (
          <>
            <div className="mb-4 text-sm text-gray-600 dark:text-gray-400">
              Found {rules.length} unique association rules. <span className="font-medium">Lift &gt; 1</span> indicates positive association.
              {stats?.unique_products && ` Based on ${stats.unique_products} products.`}
            </div>
            <DataTable
              columns={columns}
              data={rules}
              itemsPerPage={10}
              onRowClick={(rule) => console.log('Rule selected:', rule)}
            />
            {stats?.processing_time && (
              <div className="mt-4 text-xs text-gray-500 dark:text-gray-400">
                Processed in {stats.processing_time} seconds
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};