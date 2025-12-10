import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import { 
  Package, 
  TrendingUp, 
  Zap, 
  CheckCircle,
  ShoppingCart,
  DollarSign,
  Users,
  Star,
  Target
} from 'lucide-react';

const ProductBundles = () => {
  const { getSuggestedBundles, loading } = useApi();
  const [bundles, setBundles] = useState([]);
  const [sortBy, setSortBy] = useState('lift');
  const [selectedBundle, setSelectedBundle] = useState(null);

  useEffect(() => {
    loadBundles();
  }, []);

  const loadBundles = async () => {
    const data = await getSuggestedBundles({});
    setBundles(data.bundles);
    if (data.bundles.length > 0) {
      setSelectedBundle(data.bundles[0]);
    }
  };

  const sortBundles = (bundles) => {
    switch(sortBy) {
      case 'lift':
        return [...bundles].sort((a, b) => b.lift - a.lift);
      case 'confidence':
        return [...bundles].sort((a, b) => b.confidence - a.confidence);
      case 'uplift':
        return [...bundles].sort((a, b) => parseFloat(b.projectedUplift) - parseFloat(a.projectedUplift));
      default:
        return bundles;
    }
  };

  const getBundleScore = (bundle) => {
    const liftScore = bundle.lift * 20;
    const confidenceScore = bundle.confidence * 30;
    const upliftScore = parseFloat(bundle.projectedUplift) * 2;
    return Math.min(Math.round(liftScore + confidenceScore + upliftScore), 100);
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const sortedBundles = sortBundles(bundles);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <Package className="mr-3" size={28} />
            Suggested Product Bundles
          </h2>
          <p className="text-gray-600 mt-1">
            AI-generated product bundles optimized for cross-selling and revenue uplift
          </p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <select 
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="lift">Sort by Lift</option>
            <option value="confidence">Sort by Confidence</option>
            <option value="uplift">Sort by Uplift</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
            <Target size={18} className="mr-2" />
            Generate Bundles
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Bundle List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Recommended Bundles ({bundles.length})</h3>
            </div>
            
            {loading ? (
              <div className="p-12 text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
                <p className="mt-4 text-gray-600">Generating optimal bundles...</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {sortedBundles.map((bundle) => (
                  <div
                    key={bundle.id}
                    onClick={() => setSelectedBundle(bundle)}
                    className={`p-6 hover:bg-gray-50 cursor-pointer transition-all ${
                      selectedBundle?.id === bundle.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center mb-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3 ${
                            getBundleScore(bundle).includes('green') ? 'bg-green-100' : 
                            getBundleScore(bundle).includes('yellow') ? 'bg-yellow-100' : 'bg-red-100'
                          }`}>
                            <span className={`font-bold ${getBundleScore(bundle).split(' ')[0]}`}>
                              {getBundleScore(bundle)}%
                            </span>
                          </div>
                          <div>
                            <h4 className="font-bold text-lg">Bundle {bundle.id}</h4>
                            <p className="text-gray-600">AI-generated based on purchase patterns</p>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 mb-4">
                          {bundle.products.map((product, index) => (
                            <React.Fragment key={product}>
                              <span className="px-3 py-1.5 bg-blue-100 text-blue-800 rounded-lg font-medium">
                                {product}
                              </span>
                              {index < bundle.products.length - 1 && (
                                <span className="text-gray-400 font-bold">+</span>
                              )}
                            </React.Fragment>
                          ))}
                        </div>

                        <div className="grid grid-cols-3 gap-4">
                          <div className="text-center">
                            <div className="flex items-center justify-center text-green-600 mb-1">
                              <TrendingUp size={20} />
                            </div>
                            <div className="text-sm font-semibold">{bundle.lift.toFixed(2)}</div>
                            <div className="text-xs text-gray-500">Lift</div>
                          </div>
                          <div className="text-center">
                            <div className="flex items-center justify-center text-blue-600 mb-1">
                              <CheckCircle size={20} />
                            </div>
                            <div className="text-sm font-semibold">{(bundle.confidence * 100).toFixed(1)}%</div>
                            <div className="text-xs text-gray-500">Confidence</div>
                          </div>
                          <div className="text-center">
                            <div className="flex items-center justify-center text-purple-600 mb-1">
                              <Zap size={20} />
                            </div>
                            <div className="text-sm font-semibold">{bundle.projectedUplift}</div>
                            <div className="text-xs text-gray-500">Uplift</div>
                          </div>
                        </div>
                      </div>

                      <button className="ml-4 px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                        <ShoppingCart size={20} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Bundle Details & Actions */}
        <div className="space-y-6">
          {selectedBundle ? (
            <>
              {/* Bundle Details */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold mb-6">Bundle Details</h3>
                
                <div className="space-y-6">
                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Bundle Composition</h4>
                    <div className="space-y-3">
                      {selectedBundle.products.map((product, index) => (
                        <div key={product} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex items-center">
                            <div className="w-8 h-8 bg-white border rounded-lg flex items-center justify-center mr-3">
                              <span className="font-bold">{index + 1}</span>
                            </div>
                            <span className="font-medium">{product}</span>
                          </div>
                          <span className="text-gray-600">25% weight</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-700 mb-3">Performance Metrics</h4>
                    <div className="space-y-4">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Bundle Score</span>
                          <span className="font-semibold">{getBundleScore(selectedBundle)}/100</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              getBundleScore(selectedBundle) >= 80 ? 'bg-green-500' :
                              getBundleScore(selectedBundle) >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${getBundleScore(selectedBundle)}%` }}
                          ></div>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-4">
                        <div className="text-center p-3 bg-green-50 rounded-lg">
                          <div className="text-green-600 font-bold text-xl">{(selectedBundle.lift * 10).toFixed(0)}</div>
                          <div className="text-xs text-gray-600">Cross-sell Potential</div>
                        </div>
                        <div className="text-center p-3 bg-blue-50 rounded-lg">
                          <div className="text-blue-600 font-bold text-xl">{(selectedBundle.confidence * 100).toFixed(0)}%</div>
                          <div className="text-xs text-gray-600">Purchase Probability</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Action Panel */}
              <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold mb-6">Bundle Actions</h3>
                <div className="space-y-3">
                  <button className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center justify-center">
                    <ShoppingCart className="mr-2" size={20} />
                    Implement Bundle Strategy
                  </button>
                  <button className="w-full px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center">
                    <Target className="mr-2" size={20} />
                    A/B Test This Bundle
                  </button>
                  <button className="w-full px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center justify-center">
                    <Users className="mr-2" size={20} />
                    Create Marketing Campaign
                  </button>
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <Package size={48} className="mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600">Select a bundle to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductBundles;