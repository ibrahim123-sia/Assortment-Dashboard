import client from './axiosClient';

const get = (path, params) => client.get(`/analytics${path}`, { params }).then((r) => r.data);
const post = (path, body) => client.post(`/analytics${path}`, body).then((r) => r.data);

export const fetchRecommendations = (product, limit = 10) =>
  get('/recommendations', { product, limit });
export const fetchCustomerSegments = () => get('/customer_segments');
export const fetchPeriodComparison = (period_days = 30) =>
  get('/period_comparison', { period_days });
export const fetchCohortRetention = (max_periods = 12) =>
  get('/cohort_retention', { max_periods });
export const simulateBundle = (products, discount_pct = 10) =>
  post('/bundle_simulator', { products, discount_pct });
