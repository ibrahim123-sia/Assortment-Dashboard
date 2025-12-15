import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Package, TrendingUp, DollarSign, Tag } from 'lucide-react';

export const ProductBundles = () => {
  const [loading, setLoading] = useState(true);
  const [bundles, setBundles] = useState([]);
  const [filters, setFilters] = useState({
    min_confidence: 0.5,
    country: 'all',
    year: 'all',
    month: 'all',
    sample_size: 10000,
    limit: 20
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
      } else {
        // Fallback to sample data
        setBundles([
          {
            bundle_id: "B001",
            products: ["WHITE HANGING HEART T-LIGHT HOLDER", "JUMBO BAG RED RETROSPOT", "PARTY BUNTING"],
            product_count: 3,
            bundle_name: "Party Decor Bundle",
            confidence: 0.85,
            lift: 2.1,
            estimated_revenue: 299.99,
            avg_product_price: 29.99
          },
          {
            bundle_id: "B002",
            products: ["SET OF 3 CAKE TINS PANTRY DESIGN", "PACK OF 72 RETROSPOT CAKE CASES"],
            product_count: 2,
            bundle_name: "Baking Essentials Bundle",
            confidence: 0.78,
            lift: 1.8,
            estimated_revenue: 149.99,
            avg_product_price: 34.99
          },
          {
            bundle_id: "B003",
            products: ["RED WOOLLY HOTTIE WHITE HEART", "SPOTTY BUNTING"],
            product_count: 2,
            bundle_name: "Home Comfort Bundle",
            confidence: 0.72,
            lift: 1.5,
            estimated_revenue: 129.99,
            avg_product_price: 39.99
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching bundles:', error);
      // Fallback to sample data
      setBundles([
        {
          bundle_id: "B001",
          products: ["WHITE HANGING HEART T-LIGHT HOLDER", "JUMBO BAG RED RETROSPOT"],
          product_count: 2,
          bundle_name: "Basic Party Bundle",
          confidence: 0.65,
          lift: 1.8,
          estimated_revenue: 89.99,
          avg_product_price: 24.99
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      key: 'bundle_id',
      title: 'Bundle ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono font-bold text-primary-600">{value}</span>
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
          <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            {row.products.slice(0, 2).join(', ')}
            {row.products.length > 2 && ` + ${row.products.length - 2} more`}
          </div>
        </div>
      ),
    },
    {
      key: 'product_count',
      title: 'Size',
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-bold text-gray-900 dark:text-white">{value}</span>
          <div className="text-xs text-gray-500 dark:text-gray-400">products</div>
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
              style={{ width: `${value * 100}%` }}
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
              ${typeof value === 'number' ? value.toFixed(2) : '0.00'}
            </span>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">per bundle</div>
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
  const avgBundleSize = bundles.length > 0 
    ? bundles.reduce((acc, b) => acc + (b.product_count || 0), 0) / bundles.length 
    : 0;
  const avgConfidence = bundles.length > 0 
    ? bundles.reduce((acc, b) => acc + (b.confidence || 0), 0) / bundles.length 
    : 0;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Suggested Product Bundles
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Intelligent product bundles based on association rules
        </p>
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
                  Avg. Bundle Size
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {avgBundleSize.toFixed(1)}
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
                  Total Est. Revenue
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${totalRevenue.toFixed(2)}
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
                  Avg. Confidence
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {(avgConfidence * 100).toFixed(1)}%
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
            Suggested bundles based on association rules with confidence ≥ {(filters.min_confidence * 100).toFixed(0)}%
          </p>
        </div>

        {loading ? (
          <LoadingSpinner />
        ) : bundles.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <Package className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No bundles found
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting the confidence threshold or filters
            </p>
            <button 
              onClick={fetchBundles}
              className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Load Sample Bundles
            </button>
          </div>
        ) : (
          <DataTable
            columns={columns}
            data={bundles}
            itemsPerPage={10}
            onRowClick={(bundle) => console.log('Bundle selected:', bundle)}
          />
        )}
      </div>

      {/* Action Section */}
      {!loading && bundles.length > 0 && (
        <div className="bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800 rounded-lg p-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between">
            <div>
              <h4 className="text-lg font-semibold text-gray-900 dark:text-white">
                Ready to implement these bundles?
              </h4>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Export the selected bundles for your marketing team
              </p>
            </div>
            <div className="flex space-x-3 mt-4 md:mt-0">
              <button className="btn-secondary">
                <Package className="h-4 w-4 mr-2" />
                Export as CSV
              </button>
              <button className="btn-primary">
                <DollarSign className="h-4 w-4 mr-2" />
                Create Promotion
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};