import { useState, useEffect } from 'react';
import axios from 'axios';
import { FilterPanel } from '../components/FilterPanel';
import { DataTable } from '../components/DataTable';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { Calendar, Clock, Globe, TrendingUp, BarChart3, TrendingDown } from 'lucide-react';

export const SeasonalAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [seasonalData, setSeasonalData] = useState(null);
  const [filters, setFilters] = useState({});

  useEffect(() => {
    fetchSeasonalData();
  }, [filters]);

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

  const calculateSeasonalInsights = () => {
    if (!seasonalData) return null;
    
    const monthlyData = seasonalData.monthly_data || [];
    const hourlyData = seasonalData.hourly_data || [];
    const weekdayData = seasonalData.weekday_data || [];
    
    const bestMonth = monthlyData.reduce((max, month) => 
      month.revenue > max.revenue ? month : max, { revenue: 0, month_name: 'N/A' }
    );
    
    const bestHour = hourlyData.reduce((max, hour) => 
      hour.revenue > max.revenue ? hour : max, { revenue: 0, hour: 'N/A' }
    );
    
    const bestWeekday = weekdayData.reduce((max, day) => 
      day.revenue > max.revenue ? day : max, { revenue: 0, weekday: 'N/A' }
    );
    
    // Calculate trends
    const sortedMonths = [...monthlyData].sort((a, b) => a.month - b.month);
    const monthlyTrend = sortedMonths.length > 1 ? 
      (sortedMonths[sortedMonths.length-1].revenue / sortedMonths[0].revenue - 1) * 100 : 0;
    
    return {
      best_month: bestMonth.month_name,
      best_month_revenue: bestMonth.revenue,
      peak_hour: bestHour.hour + ':00',
      peak_hour_revenue: bestHour.revenue,
      top_weekday: bestWeekday.weekday,
      top_weekday_revenue: bestWeekday.revenue,
      monthly_trend: monthlyTrend,
    };
  };

  const monthColumns = [
    { key: 'month_name', title: 'Month', sortable: true },
    { key: 'revenue', title: 'Revenue', sortable: true, render: (value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    { key: 'transactions', title: 'Transactions', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'customers', title: 'Customers', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'avg_transaction', title: 'Avg. Transaction', sortable: true, render: (value) => `$${value.toFixed(2)}` },
    { key: 'revenue_share', title: 'Market Share', sortable: true, render: (value) => `${value.toFixed(1)}%` },
  ];

  const hourlyColumns = [
    { key: 'hour', title: 'Hour', sortable: true, render: (value) => `${value}:00` },
    { key: 'time_period', title: 'Period', sortable: true },
    { key: 'revenue', title: 'Revenue', sortable: true, render: (value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    { key: 'transactions', title: 'Transactions', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'avg_transaction', title: 'Avg. Spend', sortable: true, render: (value) => `$${value.toFixed(2)}` },
  ];

  const weekdayColumns = [
    { key: 'weekday', title: 'Day', sortable: true },
    { key: 'revenue', title: 'Revenue', sortable: true, render: (value) => `$${value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` },
    { key: 'transactions', title: 'Transactions', sortable: true, render: (value) => value.toLocaleString() },
    { key: 'avg_transaction', title: 'Avg. Spend', sortable: true, render: (value) => `$${value.toFixed(2)}` },
    { key: 'revenue_per_customer', title: 'Per Customer', sortable: true, render: (value) => `$${value.toFixed(2)}` },
  ];

  const insights = calculateSeasonalInsights();

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
      {insights && (
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
                  {insights.best_month}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  ${insights.best_month_revenue.toFixed(2)}
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
                  {insights.peak_hour}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  ${insights.peak_hour_revenue.toFixed(2)}
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
                  Best Weekday
                </p>
                <p className="text-lg font-bold text-gray-900 dark:text-white">
                  {insights.top_weekday}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  ${insights.top_weekday_revenue.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
                {insights.monthly_trend >= 0 ? (
                  <TrendingUp className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                ) : (
                  <TrendingDown className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                )}
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Monthly Trend
                </p>
                <p className={`text-lg font-bold ${insights.monthly_trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {insights.monthly_trend >= 0 ? '+' : ''}{insights.monthly_trend.toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Year-over-year
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

      {/* Hourly Analysis */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Hourly Shopping Patterns
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Revenue distribution throughout the day
          </p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : seasonalData?.hourly_data?.length > 0 ? (
          <DataTable
            columns={hourlyColumns}
            data={seasonalData.hourly_data}
            itemsPerPage={6}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No hourly data available
            </p>
          </div>
        )}
      </div>

      {/* Weekday Analysis */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Weekday Performance
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Revenue distribution by day of week
          </p>
        </div>
        {loading ? (
          <LoadingSpinner />
        ) : seasonalData?.weekday_data?.length > 0 ? (
          <DataTable
            columns={weekdayColumns}
            data={seasonalData.weekday_data}
            itemsPerPage={7}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600 dark:text-gray-400">
              No weekday data available
            </p>
          </div>
        )}
      </div>

      {/* Summary Statistics */}
      {seasonalData?.metadata && (
        <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6">
          <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
            Analysis Summary
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Months</p>
              <p className="font-bold text-gray-900 dark:text-white">{seasonalData.metadata.total_months || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Hours</p>
              <p className="font-bold text-gray-900 dark:text-white">{seasonalData.metadata.total_hours || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Weekdays</p>
              <p className="font-bold text-gray-900 dark:text-white">{seasonalData.metadata.total_weekdays || 0}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Data Coverage</p>
              <p className="font-bold text-gray-900 dark:text-white">100%</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};