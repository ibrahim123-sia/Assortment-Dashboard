import React from 'react';
import {
  Database,
  Trash2,
  Play,
  BarChart3,
  Calendar,
  FileText,
  MoreVertical,
  CheckCircle,
  Clock,
  AlertCircle
} from 'lucide-react';
import { useData } from '../../context/DataContext';

const DatasetManager = () => {
  const { datasets, activeDataset, setActiveDataset, deleteDataset, processDataset, processing } = useData();

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'processed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'processing':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const handleProcess = async (datasetId) => {
    const result = await processDataset(datasetId, 'fp-growth', {
      minSupport: 0.1,
      minConfidence: 0.5
    });
    console.log('Processing result:', result);
  };

  if (datasets.length === 0) {
    return (
      <div className="text-center py-12">
        <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Datasets Found</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Upload your transaction data to get started with market basket analysis
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Datasets</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage and analyze your uploaded transaction data
          </p>
        </div>
        <div className="text-sm text-gray-500 dark:text-gray-400">
          {datasets.length} dataset{datasets.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Dataset Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {datasets.map((dataset) => (
          <div
            key={dataset.id}
            className={`
              bg-white dark:bg-gray-800 rounded-xl border-2 p-6 transition-all
              ${activeDataset === dataset.id
                ? 'border-blue-500 ring-2 ring-blue-100 dark:ring-blue-900/30'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }
            `}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                  <Database className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 dark:text-white truncate max-w-[180px]">
                    {dataset.name}
                  </h3>
                  <div className="flex items-center space-x-2 mt-1">
                    {getStatusIcon(dataset.status)}
                    <span className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                      {dataset.status}
                    </span>
                  </div>
                </div>
              </div>
              <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg">
                <MoreVertical className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Dataset Info */}
            <div className="space-y-3 mb-6">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Format</span>
                <span className="font-medium text-gray-900 dark:text-white">{dataset.format}</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Size</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatFileSize(dataset.size)}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Rows × Columns</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {dataset.rows.toLocaleString()} × {dataset.columns}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Uploaded</span>
                <span className="font-medium text-gray-900 dark:text-white">
                  {formatDate(dataset.uploadDate)}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setActiveDataset(dataset.id)}
                className={`
                  flex-1 px-4 py-2 rounded-lg flex items-center justify-center space-x-2
                  ${activeDataset === dataset.id
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  }
                `}
              >
                <BarChart3 className="w-4 h-4" />
                <span className="text-sm font-medium">Analyze</span>
              </button>
              
              <button
                onClick={() => handleProcess(dataset.id)}
                disabled={processing}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span className="text-sm font-medium">Process</span>
              </button>
              
              <button
                onClick={() => deleteDataset(dataset.id)}
                className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Quick Stats */}
      {datasets.length > 0 && (
        <div className="bg-gradient-to-r from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Dataset Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-white dark:bg-gray-800/50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {datasets.length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Datasets</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800/50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {datasets.reduce((sum, d) => sum + d.rows, 0).toLocaleString()}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Rows</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800/50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {datasets.filter(d => d.status === 'processed').length}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Processed</div>
            </div>
            <div className="text-center p-4 bg-white dark:bg-gray-800/50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900 dark:text-white">
                {formatFileSize(datasets.reduce((sum, d) => sum + d.size, 0))}
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">Total Size</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatasetManager;