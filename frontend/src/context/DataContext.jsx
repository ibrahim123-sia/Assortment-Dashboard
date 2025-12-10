import React, { createContext, useContext, useState } from 'react';

const DataContext = createContext();

export const useData = () => useContext(DataContext);

export const DataProvider = ({ children }) => {
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);

  // Upload data file
  const uploadData = async (file, datasetName) => {
    setProcessing(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 200);

    // Mock processing
    await new Promise(resolve => setTimeout(resolve, 2000));
    clearInterval(interval);
    
    const newDataset = {
      id: Date.now().toString(),
      name: datasetName || `Dataset_${datasets.length + 1}`,
      filename: file.name,
      size: file.size,
      uploadDate: new Date().toISOString(),
      rows: Math.floor(Math.random() * 10000) + 1000,
      columns: Math.floor(Math.random() * 20) + 5,
      status: 'processed',
      format: file.name.split('.').pop().toUpperCase()
    };

    setDatasets(prev => [newDataset, ...prev]);
    setActiveDataset(newDataset.id);
    setProcessing(false);
    setUploadProgress(0);
    
    return { success: true, dataset: newDataset };
  };

  // Process dataset with algorithm
  const processDataset = async (datasetId, algorithm, params) => {
    setProcessing(true);
    
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    setProcessing(false);
    return {
      success: true,
      algorithm,
      params,
      results: {
        frequentItemsets: 150,
        associationRules: 85,
        clusters: 6,
        executionTime: '3.2s'
      }
    };
  };

  // Delete dataset
  const deleteDataset = async (datasetId) => {
    setDatasets(prev => prev.filter(d => d.id !== datasetId));
    if (activeDataset === datasetId) {
      setActiveDataset(datasets.length > 1 ? datasets[1].id : null);
    }
    return { success: true };
  };

  const value = {
    datasets,
    activeDataset,
    uploadProgress,
    processing,
    uploadData,
    processDataset,
    deleteDataset,
    setActiveDataset
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};