import client from './axiosClient';

const get = (path, params) => client.get(`/analytics${path}`, { params }).then((r) => r.data);

export const fetchSummary = (params) => get('/summary', params);
export const fetchAssociationRules = (params) => get('/association_rules', params);
export const fetchProductBundles = (params) => get('/product_bundles_filtered', params);
export const fetchSeasonalData = (params) => get('/seasonal_data', params);
export const fetchSeasonalProductAnalysis = (params) => get('/seasonal_product_analysis', params);
export const fetchRevenueByCountry = (params) => get('/revenue_by_country', params);
export const fetchFrequentItemsets = (params) => get('/frequent_itemsets', params);
export const fetchTopProducts = (params) => get('/top_products', params);
export const fetchFilters = (params) => get('/filters', params);
export const fetchProductStats = (params) => get('/product_stats', params);
export const fetchAnalyticsHealth = (params) => get('/health', params);
