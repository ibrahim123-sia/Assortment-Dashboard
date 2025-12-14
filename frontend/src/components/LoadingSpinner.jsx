export const LoadingSpinner = ({ size = 'md', text = 'Loading...' }) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  };

  return (
    <div className="flex flex-col items-center justify-center p-8">
      <div className="relative">
        <div
          className={`${sizeClasses[size]} rounded-full border-2 border-gray-200 dark:border-gray-700`}
        ></div>
        <div
          className={`${sizeClasses[size]} absolute top-0 left-0 rounded-full border-2 border-primary-600 border-t-transparent animate-spin`}
        ></div>
      </div>
      {text && (
        <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">{text}</p>
      )}
    </div>
  );
};