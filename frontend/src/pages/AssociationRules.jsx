import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { TrendingUp, Target, Link2 } from 'lucide-react';

export const AssociationRules = () => {
  const [loading, setLoading] = useState(true);
  const [rules, setRules] = useState([]);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({
    min_support: 0.02,
    min_confidence: 0.3,
    country: 'all',
    year: 'all',
    month: 'all',
  });

  useEffect(() => {
    fetchAssociationRules();
  }, [filters]);

  const fetchAssociationRules = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/association_rules', {
        params: filters,
      });

      if (response.data.success) {
        setRules(response.data.data || []);
        setStats({
          totalRules: response.data.total_rules,
          sampleSize: response.data.sample_size,
          processingTime: response.data.processing_time,
        });
      }
    } catch (error) {
      console.error('Error fetching association rules:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      key: 'antecedents',
      title: 'If Buy These',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {value.map((item, idx) => (
            <span key={idx} className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-1 rounded mr-1 mb-1">
              {item}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'consequents',
      title: 'Then Buy These',
      sortable: false,
      render: (value) => (
        <div className="font-medium text-gray-900 dark:text-white">
          {value.map((item, idx) => (
            <span key={idx} className="inline-block bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs px-2 py-1 rounded mr-1 mb-1">
              {item}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'support',
      title: 'Support',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-semibold text-gray-900 dark:text-white">
            {(value * 100).toFixed(2)}%
          </span>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
            <div
              className="bg-blue-600 h-1.5 rounded-full"
              style={{ width: `${value * 1000}%` }}
            ></div>
          </div>
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
            {(value * 100).toFixed(1)}%
          </span>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mt-1">
            <div
              className="bg-green-600 h-1.5 rounded-full"
              style={{ width: `${value * 100}%` }}
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
          {value.toFixed(2)}
          {value > 1 && (
            <TrendingUp className="inline-block ml-1 h-4 w-4" />
          )}
        </div>
      ),
    },
  ];

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
                  Total Rules Found
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {stats.totalRules}
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
                  {stats.sampleSize?.toLocaleString()}
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
                  {stats.processingTime}s
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Rules Table */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Product Association Rules
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Showing rules with support ≥ {(filters.min_support * 100).toFixed(1)}% and confidence ≥ {(filters.min_confidence * 100).toFixed(0)}%
          </p>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : rules.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <Link2 className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No association rules found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your filter settings to find more rules
            </p>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={rules}
            itemsPerPage={10}
            onRowClick={(rule) => console.log('Rule selected:', rule)}
          />
        )}
      </div>

      {/* Legend */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700">
        <h4 className="font-medium text-gray-900 dark:text-white mb-3">
          Understanding the Metrics
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 rounded-full bg-blue-600 mr-2"></div>
              <span className="font-medium text-gray-900 dark:text-white">Support</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Frequency of itemset occurrence in all transactions
            </p>
          </div>
          <div>
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 rounded-full bg-green-600 mr-2"></div>
              <span className="font-medium text-gray-900 dark:text-white">Confidence</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Probability that consequent is bought when antecedent is bought
            </p>
          </div>
          <div>
            <div className="flex items-center mb-2">
              <div className="w-3 h-3 rounded-full bg-purple-600 mr-2"></div>
              <span className="font-medium text-gray-900 dark:text-white">Lift</span>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Improvement over random chance (lift {'>'} 1 indicates positive relationship)
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};