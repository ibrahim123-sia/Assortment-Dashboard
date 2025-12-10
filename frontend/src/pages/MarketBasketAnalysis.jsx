import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import { 
  Search, 
  Filter, 
  Download,
  TrendingUp,
  BarChart3,
  ChevronRight
} from 'lucide-react';

const MarketBasketAnalysis = () => {
  const { getFrequentItemsets, getAssociationRules, loading } = useApi();
  const [activeTab, setActiveTab] = useState('itemsets');
  const [itemsets, setItemsets] = useState([]);
  const [rules, setRules] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    const [itemsetsData, rulesData] = await Promise.all([
      getFrequentItemsets({}),
      getAssociationRules({})
    ]);
    setItemsets(itemsetsData.itemsets);
    setRules(rulesData.rules);
  };

  const filteredRules = rules.filter(rule => 
    rule.antecedent.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.consequent.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getLiftColor = (lift) => {
    if (lift >= 2) return 'bg-purple-100 text-purple-800';
    if (lift >= 1.5) return 'bg-blue-100 text-blue-800';
    return 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Market Basket Analysis</h2>
          <p className="text-gray-600 mt-1">Discover frequently purchased product combinations</p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center">
            <Download size={18} className="mr-2" />
            Export
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
            <BarChart3 size={18} className="mr-2" />
            Run Analysis
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {['itemsets', 'rules'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`
                py-3 px-1 font-medium text-sm border-b-2 transition-colors
                ${activeTab === tab 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700'
                }
              `}
            >
              {tab === 'itemsets' ? 'Frequent Itemsets' : 'Association Rules'}
            </button>
          ))}
        </nav>
      </div>

      {/* Search and Filter */}
      <div className="bg-white rounded-xl shadow-sm p-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between">
          <div className="relative flex-1 mb-4 md:mb-0 md:mr-4">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search products, rules..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex space-x-2">
            <button className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center">
              <Filter size={18} className="mr-2" />
              Filters
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">Loading analysis data...</p>
        </div>
      ) : activeTab === 'itemsets' ? (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Itemset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Support
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Frequency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {itemsets.map((itemset, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="flex flex-wrap gap-2">
                          {itemset.items.map((item, i) => (
                            <React.Fragment key={i}>
                              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                                {item}
                              </span>
                              {i < itemset.items.length - 1 && (
                                <ChevronRight size={16} className="text-gray-400" />
                              )}
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${itemset.support * 100}%` }}
                          ></div>
                        </div>
                        <span className="ml-3 font-medium">
                          {(itemset.support * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-gray-600">
                      {Math.round(itemset.support * 10000)}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                        itemset.support > 0.3 
                          ? 'bg-green-100 text-green-800'
                          : itemset.support > 0.2
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {itemset.support > 0.3 ? 'High' : itemset.support > 0.2 ? 'Medium' : 'Low'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rule
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Support
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Confidence
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Lift
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Strength
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredRules.map((rule, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <span className="font-medium">{rule.antecedent}</span>
                        <ChevronRight size={16} className="mx-2 text-gray-400" />
                        <span className="font-medium">{rule.consequent}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full"
                            style={{ width: `${rule.support * 100}%` }}
                          ></div>
                        </div>
                        <span className="ml-3 text-sm">
                          {(rule.support * 100).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(rule.confidence)}`}>
                        {(rule.confidence * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getLiftColor(rule.lift)}`}>
                        {rule.lift.toFixed(2)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <TrendingUp size={16} className={rule.lift >= 2 ? 'text-green-600' : 'text-yellow-600'} />
                        <span className="ml-2">
                          {rule.lift >= 2 ? 'Strong' : rule.lift >= 1.5 ? 'Moderate' : 'Weak'}
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketBasketAnalysis;