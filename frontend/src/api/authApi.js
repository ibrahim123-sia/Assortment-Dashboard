import client from './axiosClient';

export const loginApi = (email, password) => client.post('/auth/login', { email, password });
export const meApi = () => client.get('/auth/me');
export const logoutApi = () => client.post('/auth/logout');
export const changePasswordApi = (current_password, new_password) =>
  client.post('/auth/change-password', { current_password, new_password });
export const forgotPasswordApi = (email) => client.post('/auth/forgot-password', { email });
export const resetPasswordApi = (token, new_password) =>
  client.post('/auth/reset-password', { token, new_password });
