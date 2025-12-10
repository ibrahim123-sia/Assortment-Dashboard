import React, { useState, useEffect } from 'react';
import { useApi } from '../context/ApiContext';
import {
  Calendar,
  Sun,
  Snowflake,
  Cloud,
  Wind,
  TrendingUp,
  TrendingDown,
  PieChart,
  Filter
} from 'lucide-react';

const SeasonalAnalysis = () => {
  const { getSeasonalAnalysis, loading } = useApi();
  const [seasonalData, setSeasonalData] = useState([]);
  const [selectedSeason, setSelectedSeason] = useState('summer');
  const [year, setYear] = useState('2024');

  useEffect(() => {
    loadSeasonalData();
  }, [year]);

  const loadSeasonalData = async () => {
    const data = await getSeasonalAnalysis({ year });
    setSeasonalData(data.seasonal);
  };

  const getSeasonIcon = (season) => {
    switch(season) {
      case 'summer': return <Sun className="text-yellow-500" size={24} />;
      case 'winter': return <Snowflake className="text-blue-500" size={24} />;
      case 'spring': return <Wind className="text-green-500" size={24} />;
      case 'fall': return <Cloud className="text-orange-500" size={24} />;
      default: return <Calendar className="text-gray-500" size={24} />;
    }
  };

  const getSeasonProducts = (season) => {
    const seasonMap = {
      summer: ['Ice Cream', 'Soft Drinks', 'BBQ Supplies', 'Swimwear', 'Sunscreen'],
      winter: ['Hot Chocolate', 'Soups', 'Heaters', 'Winter Coats', 'Blankets'],
      spring: ['Gardening Tools', 'Cleaning Supplies', 'Light Jackets', 'Allergy Medicine'],
      fall: ['Pumpkin Spice', 'Warm Beverages', 'Sweaters', 'Halloween Candy']
    };
    return seasonMap[season] || [];
  };

  const calculateSeasonalImpact = (product) => {
    const summerSales = product.summerSales || 0;
    const winterSales = product.winterSales || 0;
    const total = summerSales + winterSales;
    const seasonalityIndex = Math.abs(summerSales - winterSales) / total;
    
    return {
      index: seasonalityIndex,
      type: summerSales > winterSales ? 'summer' : 'winter',
      strength: seasonalityIndex > 0.6 ? 'High' : seasonalityIndex > 0.3 ? 'Medium' : 'Low'
    };
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800 flex items-center">
            <Calendar className="mr-3" size={28} />
            Seasonal Assortment Analysis
          </h2>
          <p className="text-gray-600 mt-1">
            Analyze seasonal buying patterns and optimize product assortment
          </p>
        </div>
        <div className="flex space-x-3 mt-4 md:mt-0">
          <select 
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            value={year}
            onChange={(e) => setYear(e.target.value)}
          >
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="2022">2022</option>
          </select>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center">
            <Filter size={18} className="mr-2" />
            Generate Report
          </button>
        </div>
      </div>

      {/* Season Selector */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {['summer', 'winter', 'spring', 'fall'].map((season) => (
          <button
            key={season}
            onClick={() => setSelectedSeason(season)}
            className={`p-6 rounded-xl border-2 transition-all ${
              selectedSeason === season
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="flex items-center mb-2">
                  {getSeasonIcon(season)}
                  <span className="ml-2 font-semibold capitalize">{season}</span>
                </div>
                <p className="text-2xl font-bold">
                  {season === 'summer' ? '35%' :
                   season === 'winter' ? '28%' :
                   season === 'spring' ? '22%' :
                   '15%'} Revenue
                </p>
              </div>
              <div className={`p-2 rounded-lg ${
                selectedSeason === season ? 'bg-blue-100' : 'bg-gray-100'
              }`}>
                <PieChart size={20} />
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Seasonal Products */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold capitalize">{selectedSeason} Products</h3>
            <div className="flex items-center text-sm text-gray-600">
              {getSeasonIcon(selectedSeason)}
              <span className="ml-2">Season Strength: High</span>
            </div>
          </div>

          <div className="space-y-4">
            {getSeasonProducts(selectedSeason).map((product, index) => (
              <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center mr-4">
                    <span className="font-bold text-blue-600">{index + 1}</span>
                  </div>
                  <div>
                    <h4 className="font-semibold">{product}</h4>
                    <p className="text-sm text-gray-600">Seasonal demand</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-lg font-bold">
                    {selectedSeason === 'summer' ? '65%' :
                     selectedSeason === 'winter' ? '72%' :
                     selectedSeason === 'spring' ? '58%' :
                     '42%'} of annual sales
                  </div>
                  <div className="text-sm text-gray-600">in {selectedSeason}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Seasonality Analysis */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-lg font-semibold mb-6">Seasonality Analysis</h3>
          
          <div className="space-y-6">
            {seasonalData.map((product, index) => {
              const impact = calculateSeasonalImpact(product);
              return (
                <div key={index} className="space-y-3">
                  <div className="flex justify-between items-center">
                    <h4 className="font-semibold">{product.product}</h4>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      impact.strength === 'High' ? 'bg-red-100 text-red-800' :
                      impact.strength === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {impact.strength} Seasonality
                    </span>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Summer Sales</span>
                      <span className="font-semibold">{product.summerSales}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full bg-gradient-to-r from-yellow-400 to-yellow-600"
                        style={{ width: `${product.summerSales}%` }}
                      ></div>
                    </div>

                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Winter Sales</span>
                      <span className="font-semibold">{product.winterSales}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full bg-gradient-to-r from-blue-400 to-blue-600"
                        style={{ width: `${product.winterSales}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-gray-200">
                    <div className="flex items-center">
                      {impact.type === 'summer' ? (
                        <Sun size={16} className="text-yellow-500 mr-2" />
                      ) : (
                        <Snowflake size={16} className="text-blue-500 mr-2" />
                      )}
                      <span className="text-sm">
                        Peak season: <span className="font-semibold capitalize">{impact.type}</span>
                      </span>
                    </div>
                    <div className="flex items-center">
                      {product.summerSales > product.winterSales ? (
                        <TrendingUp size={16} className="text-green-600 mr-1" />
                      ) : (
                        <TrendingDown size={16} className="text-blue-600 mr-1" />
                      )}
                      <span className="text-sm">
                        Seasonality Index: <span className="font-semibold">{impact.index.toFixed(2)}</span>
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Monthly Trends */}
      <div className="bg-white rounded-xl shadow-sm p-6">
        <h3 className="text-lg font-semibold mb-6">Monthly Demand Trends</h3>
        
        <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-12 gap-4">
          {[
            { month: 'Jan', demand: 65, season: 'winter' },
            { month: 'Feb', demand: 70, season: 'winter' },
            { month: 'Mar', demand: 75, season: 'spring' },
            { month: 'Apr', demand: 80, season: 'spring' },
            { month: 'May', demand: 85, season: 'spring' },
            { month: 'Jun', demand: 95, season: 'summer' },
            { month: 'Jul', demand: 100, season: 'summer' },
            { month: 'Aug', demand: 90, season: 'summer' },
            { month: 'Sep', demand: 80, season: 'fall' },
            { month: 'Oct', demand: 75, season: 'fall' },
            { month: 'Nov', demand: 70, season: 'fall' },
            { month: 'Dec', demand: 68, season: 'winter' },
          ].map((item) => (
            <div key={item.month} className="text-center">
              <div className="mb-2">
                <div className={`text-sm font-medium ${
                  item.season === 'summer' ? 'text-yellow-600' :
                  item.season === 'winter' ? 'text-blue-600' :
                  item.season === 'spring' ? 'text-green-600' : 'text-orange-600'
                }`}>
                  {item.month}
                </div>
                <div className="text-lg font-bold">{item.demand}%</div>
              </div>
              <div className="h-32 relative">
                <div className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-4 rounded-t-lg" style={{
                  height: `${item.demand}%`,
                  background: item.season === 'summer' ? 'linear-gradient(to top, #fbbf24, #f59e0b)' :
                             item.season === 'winter' ? 'linear-gradient(to top, #60a5fa, #3b82f6)' :
                             item.season === 'spring' ? 'linear-gradient(to top, #34d399, #10b981)' :
                             'linear-gradient(to top, #fb923c, #f97316)'
                }}></div>
              </div>
              <div className="text-xs text-gray-500 mt-2 capitalize">{item.season}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl shadow-sm p-6 border border-blue-100">
        <h3 className="text-lg font-semibold mb-4 text-blue-800">Seasonal Recommendations</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-4 rounded-lg border border-blue-200">
            <h4 className="font-semibold mb-2 text-blue-700">Inventory Planning</h4>
            <p className="text-sm text-gray-600">Increase {selectedSeason} product stock by 30% for next season</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-green-200">
            <h4 className="font-semibold mb-2 text-green-700">Pricing Strategy</h4>
            <p className="text-sm text-gray-600">Implement seasonal pricing with 15% premium during peak</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-purple-200">
            <h4 className="font-semibold mb-2 text-purple-700">Marketing Focus</h4>
            <p className="text-sm text-gray-600">Launch targeted campaigns 4 weeks before season start</p>
          </div>
          <div className="bg-white p-4 rounded-lg border border-yellow-200">
            <h4 className="font-semibold mb-2 text-yellow-700">Cross-selling</h4>
            <p className="text-sm text-gray-600">Bundle seasonal products with complementary items</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SeasonalAnalysis;