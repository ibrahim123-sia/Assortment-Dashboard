import client from './axiosClient';

export const listStoresApi = (params = {}) => client.get('/admin/stores', { params });
export const getStoreApi = (id) => client.get(`/admin/stores/${id}`);
export const createStoreApi = (data) => client.post('/admin/stores', data);
export const updateStoreApi = (id, data) => client.patch(`/admin/stores/${id}`, data);
export const disableStoreApi = (id, reason) => client.post(`/admin/stores/${id}/disable`, { reason });
export const enableStoreApi = (id) => client.post(`/admin/stores/${id}/enable`);
export const resetManagerPasswordApi = (id) => client.post(`/admin/stores/${id}/reset-manager-password`);
export const auditLogApi = (params = {}) => client.get('/admin/audit-log', { params });
export const adminStatsApi = () => client.get('/admin/stats');
