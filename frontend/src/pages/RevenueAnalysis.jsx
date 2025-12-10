import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import {
  BarChart3,
  TrendingUp,
  DollarSign,
  Target,
  PieChart,
  Calendar,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

const RevenueAnalysis = () => {
  const { getRevenueAnalysis, getSuggestedBundles, loading } = useApi();
  const [revenueData, setRevenueData] = useState([]);
  const [bundles, setBundles] = useState([]);
  const [timeRange, setTimeRange] = useState('month');
  const [selectedMetric, setSelectedMetric] = useState('uplift');

  useEffect(() => {
    loadData();
  }, [timeRange]);

  const loadData = async () => {
    const [revenue, bundlesData] = await Promise.all([
      getRevenueAnalysis({ timeRange }),
      getSuggestedBundles({})
    ]);
    setRevenueData(revenue.analysis);
    setBundles(bundlesData.bundles);
  };

  const calculateTotalMetrics = () => {
    const totalCurrent = revenueData.reduce((sum, item) => sum + item.currentRevenue, 0);
    const totalProjected = revenueData.reduce((sum, item) => sum + item.projectedRevenue, 0);
    const totalUplift = revenueData.reduce((sum, item) => sum + item.uplift, 0);
    const upliftPercentage = ((totalUplift / totalCurrent) * 100).toFixed(1);

    return { totalCurrent, totalProjected, totalUplift, upliftPercentage };
  };

  const metrics = calculateTotalMetrics();

  const getRevenueChartData = () => {
    return revenueData.map((item, index) => ({
      name: item.bundle,
      current: item.currentRevenue / 1000,
      projected: item.projectedRevenue / 1000,
      uplift: item.uplift / 1000,
    }));
  };

  const getROIColor = (roi) => {
    if (roi >= 30) return 'text-green-600 bg-green-100';
    if (roi >= 15) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const chartData = getRevenueChartData();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <DollarSign className="mr-3" size={28} />
            Revenue Impact Analysis
          </h2>
          <p className="text-gray-600 mt-1">
            Projected revenue uplift from implementing suggested product bundles
          </p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <select 
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="week">Weekly</option>
            <option value="month">Monthly</option>
            <option value="quarter">Quarterly</option>
            <option value="year">Yearly</option>
          </select>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Revenue</p>
              <p className="text-2xl font-bold mt-2">${(metrics.totalCurrent / 1000).toFixed(0)}K</p>
            </div>
            <div className="p-3 bg-blue-50 rounded-lg">
              <DollarSign size={24} className="text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Projected Revenue</p>
              <p className="text-2xl font-bold mt-2">${(metrics.totalProjected / 1000).toFixed(0)}K</p>
            </div>
            <div className="p-3 bg-green-50 rounded-lg">
              <TrendingUp size={24} className="text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Uplift</p>
              <p className="text-2xl font-bold mt-2">+${(metrics.totalUplift / 1000).toFixed(0)}K</p>
            </div>
            <div className="p-3 bg-purple-50 rounded-lg">
              <ArrowUpRight size={24} className="text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Uplift %</p>
              <p className="text-2xl font-bold mt-2">+{metrics.upliftPercentage}%</p>
            </div>
            <div className={`p-3 rounded-lg ${getROIColor(parseFloat(metrics.upliftPercentage))}`}>
              <Target size={24} />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Chart */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Revenue Projection by Bundle</h3>
            <div className="flex space-x-2">
              {['uplift', 'current', 'projected'].map((metric) => (
                <button
                  key={metric}
                  onClick={() => setSelectedMetric(metric)}
                  className={`px-3 py-1 text-sm rounded-lg ${
                    selectedMetric === metric 
                      ? 'bg-blue-100 text-blue-700' 
                      : 'hover:bg-gray-100'
                  }`}
                >
                  {metric === 'uplift' ? 'Uplift' : metric === 'current' ? 'Current' : 'Projected'}
                </button>
              ))}
            </div>
          </div>

          {loading ? (
            <div className="h-64 flex items-center justify-center">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="mt-2 text-gray-600">Loading revenue data...</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {chartData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{item.name}</span>
                    <span className="text-gray-600">
                      ${selectedMetric === 'current' ? item.current.toFixed(0) : 
                        selectedMetric === 'projected' ? item.projected.toFixed(0) : 
                        item.uplift.toFixed(0)}K
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full ${
                        selectedMetric === 'current' ? 'bg-blue-500' :
                        selectedMetric === 'projected' ? 'bg-green-500' : 'bg-purple-500'
                      }`}
                      style={{
                        width: `${selectedMetric === 'current' ? 
                          (item.current / Math.max(...chartData.map(d => d.current)) * 100) :
                          selectedMetric === 'projected' ?
                          (item.projected / Math.max(...chartData.map(d => d.projected)) * 100) :
                          (item.uplift / Math.max(...chartData.map(d => d.uplift)) * 100)}%`
                      }}
                    ></div>
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Current: ${item.current.toFixed(0)}K</span>
                    <span>Projected: ${item.projected.toFixed(0)}K</span>
                    <span>Uplift: ${item.uplift.toFixed(0)}K</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ROI Analysis */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">ROI Analysis</h3>
            <PieChart size={20} className="text-gray-400" />
          </div>

          <div className="space-y-6">
            {revenueData.map((item, index) => {
              const roi = ((item.uplift / item.currentRevenue) * 100).toFixed(1);
              return (
                <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-semibold">{item.bundle}</h4>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getROIColor(roi)}`}>
                      ROI: {roi}%
                    </span>
                  </div>
                  
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Investment Needed:</span>
                      <span className="font-semibold">${(item.currentRevenue * 0.1).toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Payback Period:</span>
                      <span className="font-semibold">3.2 months</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">NPV (3 years):</span>
                      <span className="font-semibold text-green-600">
                        ${(item.uplift * 36 - item.currentRevenue * 0.1).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  <div className="mt-4 pt-4 border-t border-gray-200">
                    <div className="flex items-center text-sm">
                      {parseFloat(roi) >= 20 ? (
                        <ArrowUpRight size={16} className="text-green-600 mr-2" />
                      ) : (
                        <ArrowDownRight size={16} className="text-yellow-600 mr-2" />
                      )}
                      <span className={parseFloat(roi) >= 20 ? 'text-green-600' : 'text-yellow-600'}>
                        {parseFloat(roi) >= 20 ? 'High ROI - Recommended' : 'Medium ROI - Consider'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Implementation Timeline */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold">Implementation Timeline</h3>
          <Calendar size={20} className="text-gray-400" />
        </div>

        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>

          <div className="space-y-8 pl-16">
            {[
              { month: 'Jan', action: 'Bundle Design & Pricing', status: 'completed' },
              { month: 'Feb', action: 'Inventory Optimization', status: 'completed' },
              { month: 'Mar', action: 'Staff Training', status: 'in-progress' },
              { month: 'Apr', action: 'Marketing Campaign Launch', status: 'pending' },
              { month: 'May', action: 'Performance Monitoring', status: 'pending' },
            ].map((item, index) => (
              <div key={index} className="relative">
                <div className={`absolute -left-16 w-8 h-8 rounded-full border-4 border-white ${
                  item.status === 'completed' ? 'bg-green-500' :
                  item.status === 'in-progress' ? 'bg-yellow-500' : 'bg-gray-300'
                }`}></div>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div>
                      <h4 className="font-semibold">{item.action}</h4>
                      <p className="text-sm text-gray-600">Scheduled for {item.month}</p>
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      item.status === 'completed' ? 'bg-green-100 text-green-800' :
                      item.status === 'in-progress' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {item.status === 'completed' ? 'Completed' :
                       item.status === 'in-progress' ? 'In Progress' : 'Pending'}
                    </span>
                  </div>
                  <div className="mt-3 text-sm text-gray-600">
                    Estimated Revenue Impact: +${(10000 + index * 5000).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RevenueAnalysis;