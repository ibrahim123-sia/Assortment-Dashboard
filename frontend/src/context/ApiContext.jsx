import React, { createContext, useContext, useState } from 'react';

const ApiContext = createContext();

export const useApi = () => useContext(ApiContext);

export const ApiProvider = ({ children }) => {
  // Mock data for development
  const [loading, setLoading] = useState(false);
  
  // Market Basket Analysis API functions
  const getFrequentItemsets = async (params) => {
    setLoading(true);
    // TODO: Replace with actual API call
    const mockData = {
      itemsets: [
        { items: ['Milk', 'Bread'], support: 0.45 },
        { items: ['Butter', 'Bread'], support: 0.32 },
        { items: ['Coffee', 'Sugar'], support: 0.28 },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const getAssociationRules = async (params) => {
    setLoading(true);
    const mockData = {
      rules: [
        { antecedent: 'Milk', consequent: 'Bread', support: 0.3, confidence: 0.85, lift: 2.1 },
        { antecedent: 'Butter', consequent: 'Bread', support: 0.25, confidence: 0.78, lift: 1.9 },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const getSuggestedBundles = async (params) => {
    setLoading(true);
    const mockData = {
      bundles: [
        { id: 1, products: ['Milk', 'Bread', 'Eggs'], lift: 2.5, confidence: 0.9, projectedUplift: '15%' },
        { id: 2, products: ['Coffee', 'Sugar', 'Cream'], lift: 2.1, confidence: 0.85, projectedUplift: '12%' },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const getRevenueAnalysis = async (params) => {
    setLoading(true);
    const mockData = {
      analysis: [
        { bundle: 'Bundle A', currentRevenue: 15000, projectedRevenue: 17250, uplift: 2250 },
        { bundle: 'Bundle B', currentRevenue: 12000, projectedRevenue: 13440, uplift: 1440 },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const getSeasonalAnalysis = async (params) => {
    setLoading(true);
    const mockData = {
      seasonal: [
        { product: 'Ice Cream', summerSales: 80, winterSales: 20 },
        { product: 'Hot Chocolate', summerSales: 15, winterSales: 85 },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const getProductClusters = async (params) => {
    setLoading(true);
    const mockData = {
      clusters: [
        { cluster: 1, products: ['Milk', 'Bread', 'Eggs'], size: 150 },
        { cluster: 2, products: ['Coffee', 'Tea', 'Sugar'], size: 120 },
      ],
      timestamp: new Date().toISOString()
    };
    await new Promise(resolve => setTimeout(resolve, 500));
    setLoading(false);
    return mockData;
  };

  const applyFilters = async (filters) => {
    setLoading(true);
    // TODO: Apply filters to all API calls
    await new Promise(resolve => setTimeout(resolve, 300));
    setLoading(false);
    return { success: true, filters };
  };

  const value = {
    loading,
    getFrequentItemsets,
    getAssociationRules,
    getSuggestedBundles,
    getRevenueAnalysis,
    getSeasonalAnalysis,
    getProductClusters,
    applyFilters
  };

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
};