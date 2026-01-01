import { useState, useEffect } from "react";
import axios from "axios";
import { FilterPanel } from "../components/FilterPanel";
import { DataTable } from "../components/DataTable";
import { LoadingSpinner } from "../components/LoadingSpinner";
import { DollarSign, TrendingUp, BarChart3, Target, Globe, Users } from "lucide-react";

export const RevenueAnalysis = () => {
  const [loading, setLoading] = useState(true);
  const [revenueData, setRevenueData] = useState([]);
  const [filters, setFilters] = useState({
    limit: 10,
    country: 'all',
    year: 'all',
    month: 'all'
  });

  useEffect(() => {
    fetchRevenueAnalysis();
  }, [filters]);

  const fetchRevenueAnalysis = async () => {
    setLoading(true);
    try {
      const response = await axios.get("/api/revenue_analysis", {
        params: filters,
      });

      if (response.data.success) {
        setRevenueData(response.data.revenue_analysis || []);
      } else {
        console.error('API error:', response.data.error);
        setRevenueData([]);
      }
    } catch (error) {
      console.error("Error fetching revenue analysis:", error);
      setRevenueData([]);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      key: "country",
      title: "Country",
      sortable: true,
      render: (value, row) => (
        <div className="flex items-center">
          <Globe className="h-4 w-4 text-gray-400 mr-2" />
          <div>
            <div className="font-medium text-gray-900 dark:text-white">
              {value || 'Unknown'}
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Market share: {row.market_share?.toFixed(1) || '0.0'}%
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "total_revenue",
      title: "Total Revenue",
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === "number"
                ? value.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })
                : "0.00"}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: "transaction_count",
      title: "Transactions",
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <span className="font-bold text-gray-900 dark:text-white">
            {typeof value === "number" ? value.toLocaleString() : "0"}
          </span>
        </div>
      ),
    },
    {
      key: "customer_count",
      title: "Customers",
      sortable: true,
      render: (value) => (
        <div className="text-center">
          <div className="flex items-center justify-center">
            <Users className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === "number" ? value.toLocaleString() : "0"}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: "avg_transaction_value",
      title: "Avg. Transaction",
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === "number" ? value.toFixed(2) : "0.00"}
            </span>
          </div>
        </div>
      ),
    },
    {
      key: "revenue_per_customer",
      title: "Per Customer",
      sortable: true,
      render: (value) => (
        <div className="text-right">
          <div className="flex items-center justify-end">
            <DollarSign className="h-4 w-4 text-gray-400 mr-1" />
            <span className="font-bold text-gray-900 dark:text-white">
              {typeof value === "number" ? value.toFixed(2) : "0.00"}
            </span>
          </div>
        </div>
      ),
    },
  ];

  const calculateTotals = () => {
    const totals = revenueData.reduce(
      (acc, item) => ({
        totalRevenue: acc.totalRevenue + (item.total_revenue || 0),
        totalTransactions: acc.totalTransactions + (item.transaction_count || 0),
        totalCustomers: acc.totalCustomers + (item.customer_count || 0),
        avgTransaction: (acc.avgTransaction * acc.count + (item.avg_transaction_value || 0)) / (acc.count + 1),
        count: acc.count + 1,
      }),
      { totalRevenue: 0, totalTransactions: 0, totalCustomers: 0, avgTransaction: 0, count: 0 }
    );
    return totals;
  };

  const totals = calculateTotals();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
          Revenue Analysis
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Financial performance analysis by country
        </p>
      </div>

      <FilterPanel onFilterChange={setFilters} loading={loading} />

      {/* Revenue Stats */}
      {!loading && revenueData.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20">
                <DollarSign className="h-6 w-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Revenue
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  $
                  {totals.totalRevenue.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
                <TrendingUp className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Transactions
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totals.totalTransactions.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20">
                <Users className="h-6 w-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Total Customers
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {totals.totalCustomers.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
          <div className="card">
            <div className="flex items-center">
              <div className="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
                <Target className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
              </div>
              <div className="ml-4">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Avg. Transaction
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  ${totals.avgTransaction.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Revenue Table */}
      <div className="card">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Country Revenue Analysis
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Revenue distribution and performance metrics by country
          </p>
        </div>

        {loading ? (
          <LoadingSpinner text="Loading revenue data..." />
        ) : revenueData.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-400 dark:text-gray-500 mb-4">
              <BarChart3 className="h-12 w-12 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              No revenue data available
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Try adjusting your filters to see revenue analysis
            </p>
            <button
              onClick={fetchRevenueAnalysis}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Retry Loading
            </button>
          </div>
        ) : (
          <>
            <DataTable
              columns={columns}
              data={revenueData}
              itemsPerPage={10}
              onRowClick={(item) => console.log("Country selected:", item)}
            />
            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Showing {revenueData.length} countries • Total {totals.count} analyzed
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Global Average Transaction: <span className="text-blue-600">${totals.avgTransaction.toFixed(2)}</span>
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Across all countries and customers
                  </p>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Insights */}
      {!loading && revenueData.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
              Top Performing Countries
            </h4>
            <div className="space-y-4">
              {[...revenueData]
                .sort((a, b) => (b.total_revenue || 0) - (a.total_revenue || 0))
                .slice(0, 3)
                .map((item) => (
                  <div
                    key={item.country}
                    className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-900 rounded-lg"
                  >
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">
                        {item.country}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {item.customer_count?.toLocaleString() || 0} customers
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-gray-900 dark:text-white">
                        ${(item.total_revenue || 0).toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </p>
                      <p className="text-sm text-green-600">
                        ${(item.revenue_per_customer || 0).toFixed(2)} per customer
                      </p>
                    </div>
                  </div>
                ))}
            </div>
          </div>
          <div className="card">
            <h4 className="font-semibold text-gray-900 dark:text-white mb-4">
              Market Insights
            </h4>
            <ul className="space-y-3">
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-green-600 dark:text-green-400">
                    1
                  </span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Focus on high-value markets with revenue per customer &gt; $50
                </span>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-blue-600 dark:text-blue-400">
                    2
                  </span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Expand in markets with high transaction frequency
                </span>
              </li>
              <li className="flex items-start">
                <div className="flex-shrink-0 h-5 w-5 rounded-full bg-purple-100 dark:bg-purple-900 flex items-center justify-center mt-0.5">
                  <span className="text-xs font-bold text-purple-600 dark:text-purple-400">
                    3
                  </span>
                </div>
                <span className="ml-3 text-gray-700 dark:text-gray-300">
                  Consider localization for markets with &gt; 5% market share
                </span>
              </li>
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};