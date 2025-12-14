import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Calendar, Clock, Globe, TrendingUp } from 'lucide-react';

export const SeasonalAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [seasonalData, setSeasonalData] = useState(null);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    fetchSeasonalData();
  }, []);

  const fetchSeasonalData = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/seasonal_data');
      if (response.data.success) {
        setSeasonalData(response.data);
      }
    } catch (error) {
      console.error('Error fetching seasonal data:', error);
    } finally {
      setLoading(false);
    }
  };

  const monthColumns = [
    { key: 'month_name', title: 'Month', sortable: true },
    { key: 'revenue', title: 'Revenue', sortable: true, render: (value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    { key: 'transactions', title: 'Transactions', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'avg_transaction', title: 'Avg. Transaction', sortable: true, render: (value) => `$${value.toFixed(2)}` },
    { key: 'product_variety', title: 'Products', sortable: true },
  ];

  const countryColumns = [
    { key: 'country', title: 'Country', sortable: true },
    { key: 'revenue', title: 'Revenue', sortable: true, render: (value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    { key: 'transactions', title: 'Transactions', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'customers', title: 'Customers', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'avg_transaction_value', title: 'Avg. Spend', sortable: true, render: (value) => `$${value.toFixed(2)}` },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Seasonal Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Analyze purchasing patterns by time and geography
        </p>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Seasonal Insights */}
      {seasonalData?.seasonal_insights && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <Calendar className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Best Month
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {seasonalData.seasonal_insights.best_month}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <Clock className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Peak Hour
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {seasonalData.seasonal_insights.peak_hour}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <Globe className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Top Country
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {seasonalData.seasonal_insights.top_country}
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
                  Best Weekday
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {seasonalData.seasonal_insights.best_weekday}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Monthly Analysis */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Monthly Performance
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Revenue and transaction patterns by month
          </p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : seasonalData?.monthly_data?.length > 0 ? (
          <DataTable
            columns={monthColumns}
            data={seasonalData.monthly_data}
            itemsPerPage={6}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No monthly data available
            </p>
          </div>
        )}
      </div>

      {/* Country Analysis */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Country Performance
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Revenue distribution across countries
          </p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : seasonalData?.country_data?.length > 0 ? (
          <DataTable
            columns={countryColumns}
            data={seasonalData.country_data}
            itemsPerPage={5}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No country data available
            </p>
          </div>
        )}
      </div>

      {/* Hourly & Weekday Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Hourly Patterns */}
        <div className="card">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            Hourly Shopping Patterns
          </h4>
          {seasonalData?.hourly_data?.length > 0 ? (
            <div className="space-y-4">
              {seasonalData.hourly_data
                .sort((a, b) => a.hour - b.hour)
                .map((hour) => (
                  <div key={hour.hour} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {hour.hour}:00
                    </span>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {hour.transactions} trans
                      </span>
                      <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{
                            width: `${(hour.transactions / Math.max(...seasonalData.hourly_data.map(h => h.transactions))) * 100}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-center py-8">
              No hourly data available
            </p>
          )}
        </div>

        {/* Weekday Patterns */}
        <div className="card">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            Weekday Performance
          </h4>
          {seasonalData?.weekday_data?.length > 0 ? (
            <div className="space-y-4">
              {seasonalData.weekday_data
                .sort((a, b) => {
                  const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
                  return days.indexOf(a.weekday) - days.indexOf(b.weekday);
                })
                .map((day) => (
                  <div key={day.weekday} className="flex items-center justify-between">
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {day.weekday_short}
                    </span>
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        ${day.revenue.toFixed(2)}
                      </span>
                      <div className="w-32 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{
                            width: `${(day.revenue / Math.max(...seasonalData.weekday_data.map(d => d.revenue))) * 100}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-center py-8">
              No weekday data available
            </p>
          )}
        </div>
      </div>
    </div>
  );
};