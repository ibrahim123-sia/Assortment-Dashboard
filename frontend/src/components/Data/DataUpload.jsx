import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Database, X, AlertCircle, CheckCircle, Settings } from 'lucide-react';
import { useData } from '../../context/DataContext';

const DataUpload = () => {
  const { uploadData, processing, uploadProgress } = useData();
  const [datasetName, setDatasetName] = useState('');
  const [file, setFile] = useState(null);
  const [algorithm, setAlgorithm] = useState('fp-growth');
  const [minSupport, setMinSupport] = useState(0.1);
  const [minConfidence, setMinConfidence] = useState(0.5);

  const onDrop = useCallback((acceptedFiles) => {
    const selectedFile = acceptedFiles[0];
    if (selectedFile) {
      setFile(selectedFile);
      if (!datasetName) {
        setDatasetName(selectedFile.name.split('.')[0]);
      }
    }
  }, [datasetName]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json']
    },
    multiple: false
  });

  const handleUpload = async () => {
    if (!file) return;
    
    const result = await uploadData(file, datasetName);
    if (result.success) {
      // Reset form
      setFile(null);
      setDatasetName('');
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
    setDatasetName('');
  };

  const supportedFormats = [
    { format: 'CSV', desc: 'Comma separated values', icon: '📊' },
    { format: 'Excel', desc: 'XLSX, XLS formats', icon: '📈' },
    { format: 'JSON', desc: 'JavaScript Object Notation', icon: '📋' },
    { format: 'Transaction', desc: 'Transaction logs', icon: '🛒' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Upload Transaction Data</h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Upload your store transaction data to start market basket analysis
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-500 dark:text-gray-400">
          <Database className="w-4 h-4" />
          <span>Supported: CSV, Excel, JSON</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Upload Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* Upload Zone */}
          <div
            {...getRootProps()}
            className={`
              relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
              transition-all duration-300 hover:border-blue-500 hover:bg-blue-50/50
              dark:hover:bg-blue-900/10
              ${isDragActive 
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                : 'border-gray-300 dark:border-gray-700'
              }
            `}
          >
            <input {...getInputProps()} />
            
            <div className="space-y-4">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800">
                <Upload className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {isDragActive ? 'Drop your file here' : 'Drag & drop your file'}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  or click to browse (CSV, Excel, JSON)
                </p>
              </div>

              <div className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                <FileText className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span className="text-sm font-medium">Max file size: 100MB</span>
              </div>
            </div>
          </div>

          {/* File Preview */}
          {file && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center">
                    <FileText className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-gray-900 dark:text-white">{file.name}</h4>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB • {file.type || 'Unknown type'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Dataset Name
                  </label>
                  <input
                    type="text"
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                    className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="Enter a descriptive name for your dataset"
                  />
                </div>

                {/* Progress Bar */}
                {processing && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">Uploading...</span>
                      <span className="font-medium">{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Upload Button */}
          {file && (
            <button
              onClick={handleUpload}
              disabled={processing || !datasetName}
              className="w-full px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
            >
              {processing ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Processing Data...</span>
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  <span>Upload & Process Dataset</span>
                </>
              )}
            </button>
          )}
        </div>

        {/* Right Column - Settings */}
        <div className="space-y-6">
          {/* Algorithm Settings */}
          <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                <Settings className="w-5 h-5 mr-2" />
                Analysis Settings
              </h3>
              <span className="px-3 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300 rounded-full text-sm font-medium">
                Recommended
              </span>
            </div>

            <div className="space-y-6">
              {/* Algorithm Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Algorithm
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setAlgorithm('fp-growth')}
                    className={`p-3 rounded-lg border-2 text-center transition-all ${
                      algorithm === 'fp-growth'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-gray-900 dark:text-white">FP-Growth</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Fast & Efficient</div>
                  </button>
                  <button
                    onClick={() => setAlgorithm('apriori')}
                    className={`p-3 rounded-lg border-2 text-center transition-all ${
                      algorithm === 'apriori'
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <div className="font-medium text-gray-900 dark:text-white">Apriori</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">Classic</div>
                  </button>
                </div>
              </div>

              {/* Parameters */}
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <label className="font-medium text-gray-700 dark:text-gray-300">
                      Minimum Support: {minSupport.toFixed(2)}
                    </label>
                    <span className="text-gray-500">(0.01 - 1.00)</span>
                  </div>
                  <input
                    type="range"
                    min="0.01"
                    max="1"
                    step="0.01"
                    value={minSupport}
                    onChange={(e) => setMinSupport(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  />
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <label className="font-medium text-gray-700 dark:text-gray-300">
                      Minimum Confidence: {minConfidence.toFixed(2)}
                    </label>
                    <span className="text-gray-500">(0.1 - 1.0)</span>
                  </div>
                  <input
                    type="range"
                    min="0.1"
                    max="1"
                    step="0.05"
                    value={minConfidence}
                    onChange={(e) => setMinConfidence(parseFloat(e.target.value))}
                    className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Supported Formats */}
          <div className="bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-800 dark:to-blue-900/20 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Supported Formats
            </h3>
            <div className="space-y-3">
              {supportedFormats.map((format) => (
                <div
                  key={format.format}
                  className="flex items-center justify-between p-3 bg-white/50 dark:bg-gray-800/50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{format.icon}</span>
                    <div>
                      <div className="font-medium text-gray-900 dark:text-white">{format.format}</div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">{format.desc}</div>
                    </div>
                  </div>
                  <CheckCircle className="w-5 h-5 text-green-500" />
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800 p-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="font-semibold text-yellow-800 dark:text-yellow-300">Data Requirements</h4>
                <ul className="mt-2 space-y-1 text-sm text-yellow-700 dark:text-yellow-400">
                  <li>• CSV should have headers</li>
                  <li>• Transaction ID column required</li>
                  <li>• Product names in separate columns</li>
                  <li>• Remove duplicate transactions</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataUpload;