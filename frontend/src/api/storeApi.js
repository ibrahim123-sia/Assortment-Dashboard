import client from './axiosClient';

export const getProfileApi = () => client.get('/store/profile');
export const updateProfileApi = (data) => client.patch('/store/profile', data);
export const listDatasetsApi = () => client.get('/store/datasets');
export const uploadDatasetApi = (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post('/store/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress,
  });
};
export const activateDatasetApi = (id) => client.post(`/store/datasets/${id}/activate`);
export const deleteDatasetApi = (id) => client.delete(`/store/datasets/${id}`);
export const getScheduledJobApi = () => client.get('/store/scheduled-job');
export const updateScheduledJobApi = (data) => client.put('/store/scheduled-job', data);
export const exportPdfApi = (sections) => client.post('/store/exports/pdf', { sections });
export const exportCsvUrl = (type) => {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
  return `${base}/store/exports/csv?type=${type}`;
};
