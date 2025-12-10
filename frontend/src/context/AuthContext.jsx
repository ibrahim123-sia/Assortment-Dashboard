import React, { createContext, useContext, useState } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('mba_user');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const login = async (email, password) => {
    setLoading(true);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const userData = {
      id: '1',
      email,
      name: 'Analytics User',
      company: 'Retail Corp',
      plan: 'premium',
      joinDate: new Date().toISOString()
    };
    
    localStorage.setItem('mba_user', JSON.stringify(userData));
    setUser(userData);
    setLoading(false);
    return { success: true, user: userData };
  };

  const register = async (userData) => {
    setLoading(true);
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    const newUser = {
      id: '2',
      ...userData,
      plan: 'free',
      joinDate: new Date().toISOString()
    };
    
    localStorage.setItem('mba_user', JSON.stringify(newUser));
    setUser(newUser);
    setLoading(false);
    return { success: true, user: newUser };
  };

  const logout = () => {
    localStorage.removeItem('mba_user');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};