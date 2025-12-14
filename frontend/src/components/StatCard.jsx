// Components/StatCard.jsx
export const StatCard = ({ title, value, change, icon: Icon, trend, loading = false }) => {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
            {title}
          </p>
          {loading ? (
            <div className="h-8 w-24 bg-gray-200 dark:bg-gray-700 rounded mt-2 animate-pulse"></div>
          ) : (
            <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
              {value}
            </p>
          )}
        </div>
        {Icon && (
          <div className="p-3 rounded-lg bg-primary-50 dark:bg-primary-900/20">
            <Icon className="h-6 w-6 text-primary-600 dark:text-primary-400" />
          </div>
        )}
      </div>
      {change !== undefined && !loading && (
        <div className="mt-4 flex items-center">
          <span
            className={`text-sm font-medium ${
              trend === 'up'
                ? 'text-green-600 dark:text-green-400'
                : 'text-red-600 dark:text-red-400'
            }`}
          >
            {change}
          </span>
          <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
            from previous period
          </span>
        </div>
      )}
    </div>
  );
};