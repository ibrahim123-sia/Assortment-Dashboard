import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import axios from 'axios'
import './index.css'
import App from './App.jsx'
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './api/axiosClient'

const ANALYTICS_ENDPOINTS = new Set([
  'summary', 'association_rules', 'product_bundles_filtered', 'seasonal_data',
  'seasonal_product_analysis', 'revenue_by_country', 'frequent_itemsets',
  'top_products', 'filters', 'product_stats', 'health',
]);

const ANALYTICS_PATH_REGEX = new RegExp(`^/api/(${[...ANALYTICS_ENDPOINTS].join('|')})(/|\\?|$)`);

axios.interceptors.request.use((config) => {
  const url = config.url || '';
  if (ANALYTICS_PATH_REGEX.test(url)) {
    config.url = url.replace('/api/', '/api/analytics/');
  }
  const token = getAccessToken();
  if (token && !config.headers.Authorization) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let isRefreshing = false;
let queue = [];

axios.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (!error.response || original?._retry) return Promise.reject(error);
    if (error.response.status === 401 && getRefreshToken()) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          queue.push((t) => {
            original.headers.Authorization = `Bearer ${t}`;
            resolve(axios(original));
          });
        });
      }
      original._retry = true;
      isRefreshing = true;
      try {
        const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
        const res = await axios.post(`${base}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${getRefreshToken()}` },
        });
        const newAccess = res.data.access_token;
        setTokens({ access_token: newAccess });
        queue.forEach((cb) => cb(newAccess));
        queue = [];
        original.headers.Authorization = `Bearer ${newAccess}`;
        return axios(original);
      } catch (err) {
        clearTokens();
        if (window.location.pathname !== '/login') window.location.href = '/login';
        return Promise.reject(err);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
