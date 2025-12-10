// In any component file
import LoadingSpinner from '../components/Common/LoadingSpinner';
import SkeletonLoader from '../components/Common/SkeletonLoader';

const MyComponent = () => {
  const { loading, data } = useApi();

  if (loading) {
    return (
      <div className="space-y-6">
        <SkeletonLoader type="stats" />
        <SkeletonLoader type="card" count={3} />
      </div>
    );
  }

  return (
    <div>
      {/* Your content here */}
    </div>
  );
};

// Or for inline loading
const AnotherComponent = () => {
  const { processing } = useData();

  return (
    <div>
      <button disabled={processing}>
        {processing ? (
          <div className="flex items-center space-x-2">
            <LoadingSpinner size="sm" type="dots" />
            <span>Processing...</span>
          </div>
        ) : (
          'Submit'
        )}
      </button>
    </div>
  );
};