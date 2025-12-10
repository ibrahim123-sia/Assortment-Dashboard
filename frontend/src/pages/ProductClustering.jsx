import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import {
  PieChart,
  Target,
  Users,
  Zap,
  TrendingUp,
  GitBranch,
  Filter,
  Download,
  Eye,
  EyeOff
} from 'lucide-react';

const ProductClustering = () => {
  const { getProductClusters, loading } = useApi();
  const [clusters, setClusters] = useState([]);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [viewMode, setViewMode] = useState('grid');
  const [showCentroids, setShowCentroids] = useState(true);

  useEffect(() => {
    loadClusters();
  }, []);

  const loadClusters = async () => {
    const data = await getProductClusters({});
    setClusters(data.clusters);
    if (data.clusters.length > 0) {
      setSelectedCluster(data.clusters[0]);
    }
  };

  const getClusterColor = (clusterId) => {
    const colors = [
      'bg-blue-500 border-blue-600 text-blue-700',
      'bg-green-500 border-green-600 text-green-700',
      'bg-purple-500 border-purple-600 text-purple-700',
      'bg-yellow-500 border-yellow-600 text-yellow-700',
      'bg-pink-500 border-pink-600 text-pink-700',
      'bg-indigo-500 border-indigo-600 text-indigo-700',
    ];
    return colors[(clusterId - 1) % colors.length];
  };

  const getClusterScore = (cluster) => {
    const sizeScore = (cluster.size / 500) * 40;
    const supportScore = cluster.avgSupport * 30;
    const cohesionScore = 30; // This would be calculated from actual data
    return Math.min(Math.round(sizeScore + supportScore + cohesionScore), 100);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <PieChart className="mr-3" size={28} />
            Product Clustering Analysis
          </h2>
          <p className="text-gray-600 mt-1">
            K-Means clustering of products based on sales behavior and co-purchase patterns
          </p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1 rounded-lg ${viewMode === 'grid' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
            >
              Grid
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1 rounded-lg ${viewMode === 'list' ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-100'}`}
            >
              List
            </button>
          </div>
          <button 
            onClick={() => setShowCentroids(!showCentroids)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center"
          >
            {showCentroids ? <EyeOff size={18} className="mr-2" /> : <Eye size={18} className="mr-2" />}
            {showCentroids ? 'Hide Centroids' : 'Show Centroids'}
          </button>
        </div>
      </div>

      {/* Cluster Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Clusters</p>
              <p className="text-2xl font-bold mt-2">{clusters.length}</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <Target size={24} className="text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Products</p>
              <p className="text-2xl font-bold mt-2">
                {clusters.reduce((sum, cluster) => sum + cluster.size, 0)}
              </p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <Users size={24} className="text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg. Support</p>
              <p className="text-2xl font-bold mt-2">
                {clusters.length > 0 
                  ? ((clusters.reduce((sum, cluster) => sum + cluster.avgSupport, 0) / clusters.length) * 100).toFixed(1) + '%'
                  : '0%'
                }
              </p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <TrendingUp size={24} className="text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Silhouette Score</p>
              <p className="text-2xl font-bold mt-2">0.72</p>
            </div>
            <div className="p-3 bg-yellow-50 rounded-lg">
              <Zap size={24} className="text-yellow-600" />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Clusters Visualization */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">Cluster Visualization</h3>
              <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center">
                <Download size={18} className="mr-2" />
                Export
              </button>
            </div>

            {loading ? (
              <div className="h-96 flex items-center justify-center">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                  <p className="mt-4 text-gray-600">Calculating clusters...</p>
                </div>
              </div>
            ) : (
              <div className="relative h-96 border border-gray-200 rounded-lg bg-gray-50 overflow-hidden">
                {/* Simulated Scatter Plot */}
                {clusters.map((cluster) => (
                  <div key={cluster.id} className="absolute" style={{
                    left: `${cluster.centroid[0] * 100}%`,
                    top: `${cluster.centroid[1] * 100}%`,
                    transform: 'translate(-50%, -50%)'
                  }}>
                    {/* Cluster centroid */}
                    {showCentroids && (
                      <div className={`absolute w-8 h-8 ${getClusterColor(cluster.id).split(' ')[0]} rounded-full border-4 border-white shadow-lg animate-pulse`}></div>
                    )}
                    
                    {/* Cluster products */}
                    {cluster.products.map((product, index) => {
                      const angle = (index * (360 / cluster.products.length)) * (Math.PI / 180);
                      const radius = 80 + (index % 3) * 20;
                      const x = Math.cos(angle) * radius;
                      const y = Math.sin(angle) * radius;
                      
                      return (
                        <div
                          key={product}
                          className={`absolute w-16 h-16 ${getClusterColor(cluster.id)} rounded-full border-2 flex items-center justify-center text-white font-semibold cursor-pointer hover:scale-110 transition-transform`}
                          style={{
                            left: `${x}px`,
                            top: `${y}px`,
                            transform: 'translate(-50%, -50%)'
                          }}
                          onClick={() => setSelectedCluster(cluster)}
                        >
                          <div className="text-center px-1">
                            <div className="text-xs">{product.split(' ')[0]}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ))}

                {/* Legend */}
                <div className="absolute bottom-4 right-4 bg-white/90 backdrop-blur-sm p-4 rounded-lg border shadow-sm">
                  <h4 className="font-semibold mb-2">Clusters Legend</h4>
                  <div className="space-y-2">
                    {clusters.map((cluster) => (
                      <div key={cluster.id} className="flex items-center">
                        <div className={`w-3 h-3 ${getClusterColor(cluster.id).split(' ')[0]} rounded-full mr-2`}></div>
                        <span className="text-sm">Cluster {cluster.id}: {cluster.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Clusters Grid */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
            {clusters.map((cluster) => (
              <div
                key={cluster.id}
                className={`bg-white rounded-xl shadow-sm p-6 border-2 transition-all cursor-pointer ${
                  selectedCluster?.id === cluster.id 
                    ? 'border-blue-500 ring-2 ring-blue-100' 
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => setSelectedCluster(cluster)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center mb-2">
                      <div className={`w-10 h-10 ${getClusterColor(cluster.id).split(' ')[0]} rounded-lg flex items-center justify-center mr-3`}>
                        <span className="text-white font-bold">{cluster.id}</span>
                      </div>
                      <div>
                        <h3 className="font-bold text-lg">{cluster.name}</h3>
                        <p className="text-gray-600 text-sm">{cluster.products.length} products</p>
                      </div>
                    </div>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getClusterColor(cluster.id)}`}>
                    Score: {getClusterScore(cluster)}%
                  </div>
                </div>

                <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Cluster Size:</span>
                    <span className="font-semibold">{cluster.size} items</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Avg. Support:</span>
                    <span className="font-semibold">{(cluster.avgSupport * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Cohesion:</span>
                    <span className="font-semibold">0.{(78 + cluster.id * 3)}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-medium mb-2">Top Products:</h4>
                  <div className="flex flex-wrap gap-2">
                    {cluster.products.slice(0, 3).map((product) => (
                      <span
                        key={product}
                        className={`px-2 py-1 text-xs ${getClusterColor(cluster.id).replace('700', '100').replace('500', '100')} ${getClusterColor(cluster.id)} rounded`}
                      >
                        {product}
                      </span>
                    ))}
                    {cluster.products.length > 3 && (
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                        +{cluster.products.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Selected Cluster Details */}
        <div className="space-y-6">
          {selectedCluster ? (
            <>
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold mb-6">Cluster Details</h3>
                
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Characteristics</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Cluster ID:</span>
                        <span className="font-semibold">{selectedCluster.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Name:</span>
                        <span className="font-semibold">{selectedCluster.name}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Products Count:</span>
                        <span className="font-semibold">{selectedCluster.products.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Items:</span>
                        <span className="font-semibold">{selectedCluster.size}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Metrics</h4>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Cluster Quality</span>
                          <span className="font-semibold">{getClusterScore(selectedCluster)}/100</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${getClusterColor(selectedCluster.id).split(' ')[0]}`}
                            style={{ width: `${getClusterScore(selectedCluster)}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                          <div className="text-blue-600 font-bold text-xl">
                            {(selectedCluster.avgSupport * 100).toFixed(0)}%
                          </div>
                          <div className="text-xs text-gray-600">Avg Support</div>
                        </div>
                        <div className="text-center p-3 bg-green-50 rounded-lg">
                          <div className="text-green-600 font-bold text-xl">
                            {Math.round(selectedCluster.size / selectedCluster.products.length)}
                          </div>
                          <div className="text-xs text-gray-600">Avg Items/Product</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">All Products</h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                      {selectedCluster.products.map((product, index) => (
                        <div
                          key={product}
                          className="flex items-center justify-between p-2 hover:bg-gray-50 rounded-lg"
                        >
                          <div className="flex items-center">
                            <div className="w-6 h-6 bg-gray-100 rounded flex items-center justify-center mr-3">
                              <span className="text-xs font-medium">{index + 1}</span>
                            </div>
                            <span>{product}</span>
                          </div>
                          <span className="text-sm text-gray-500">Product</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-sm p-6 border border-purple-100">
                <h3 className="text-lg font-semibold mb-4 text-purple-800">Cluster Recommendations</h3>
                <div className="space-y-3">
                  <div className="flex items-start">
                    <GitBranch size={16} className="text-purple-600 mt-1 mr-3 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-purple-700">Cross-Sell Strategy</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Bundle products within this cluster for maximum lift
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <Target size={16} className="text-blue-600 mt-1 mr-3 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-blue-700">Inventory Optimization</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Stock cluster products together for space efficiency
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start">
                    <TrendingUp size={16} className="text-green-600 mt-1 mr-3 flex-shrink-0" />
                    <div>
                      <h4 className="font-medium text-green-700">Pricing Strategy</h4>
                      <p className="text-sm text-gray-600 mt-1">
                        Implement cluster-based dynamic pricing
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <PieChart size={48} className="mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Select a cluster to view details</p>
            </div>
          )}
        </div>
      </div>

      {/* Algorithm Settings */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-6">Clustering Algorithm Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-semibold mb-2">K-Means Parameters</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Number of Clusters (k):</span>
                <span className="font-mono">{clusters.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Max Iterations:</span>
                <span className="font-mono">300</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Tolerance:</span>
                <span className="font-mono">1e-4</span>
              </div>
            </div>
          </div>

          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-semibold mb-2">Feature Selection</h4>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Purchase Frequency</span>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Basket Size</span>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Time of Day</span>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Seasonality</span>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
            </div>
          </div>

          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-semibold mb-2">Performance Metrics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Silhouette Score:</span>
                <span className="font-mono">0.72</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Davies-Bouldin Index:</span>
                <span className="font-mono">0.89</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Calinski-Harabasz Index:</span>
                <span className="font-mono">124.3</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductClustering;