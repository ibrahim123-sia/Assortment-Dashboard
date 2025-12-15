import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { NetworkGraph } from '../components/NetworkGraph';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Network, GitBranch, Target } from 'lucide-react';

export const NetworkView = () => {
  const [loading, setLoading] = useState(true);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [filters, setFilters] = useState({
    min_support: 0.02,
    country: 'all',
    year: 'all',
    month: 'all',
    sample_size: 10000, // Added sample size
    max_items: 2, // Limit items per itemset
    limit: 30, // Limit itemsets
  });

  useEffect(() => {
    fetchNetworkData();
  }, [filters]);

  const fetchNetworkData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/frequent_itemsets', {
        params: filters,
      });

      if (response.data.success && response.data.network) {
        const { nodes, links } = response.data.network;
        
        setGraphData({
          nodes: nodes.slice(0, 50), // Limit nodes for performance
          links: links.slice(0, 100), // Limit links for performance
        });
      }
    } catch (error) {
      console.error('Error fetching network data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Network View
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Visualize product relationships as an interactive network graph
        </p>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Network Stats */}
      {!loading && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <Network className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Products
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {graphData.nodes.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <GitBranch className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Connections
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {graphData.links.length}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <Target className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Min. Support
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(filters.min_support * 100).toFixed(1)}%
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Network Graph Visualization */}
      <div className="card p-0 overflow-hidden">
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Product Relationship Network
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Showing up to 50 products and 100 connections for optimal performance
          </p>
        </div>
        <NetworkGraph
          data={graphData}
          loading={loading}
          height={600}
        />
      </div>

      {/* Performance Note */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
        <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
          Performance Optimization
        </h4>
        <div className="space-y-3">
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-blue-600 dark:text-blue-400">i</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Network view limited to 50 nodes and 100 links for optimal performance
            </span>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-green-600 dark:text-green-400">i</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Using {filters.sample_size?.toLocaleString() || '10,000'} sample transactions
            </span>
          </div>
          <div className="flex items-start">
            <div className="flex-shrink-0 h-5 w-5 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mt-0.5">
              <span className="text-xs font-bold text-purple-600 dark:text-purple-400">i</span>
            </div>
            <span className="ml-3 text-gray-700 dark:text-gray-300">
              Adjust sample size in filters for different detail levels
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};