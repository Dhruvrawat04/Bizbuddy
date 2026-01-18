import axios from 'axios';

// Use environment variable for API URL in production
const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const auth = {
  login: (credentials) => api.post('/auth/login', credentials),
};

export const products = {
  getAll: (page = 1, pageSize = 50) => api.get(`/products?page=${page}&page_size=${pageSize}`),
  add: (product) => api.post('/products', product),
  updateStock: (productId, quantity) => 
    api.put(`/products/${productId}/stock`, { product_id: productId, quantity }),
};

export const categories = {
  getAll: (page = 1, pageSize = 12) => api.get(`/categories?page=${page}&page_size=${pageSize}`),
  add: (category) => api.post('/categories', category),
  update: (categoryId, category) => api.put(`/categories/${categoryId}`, category),
  delete: (categoryId) => api.delete(`/categories/${categoryId}`),
};

export const suppliers = {
  getAll: (page = 1, pageSize = 12) => api.get(`/suppliers?page=${page}&page_size=${pageSize}`),
  add: (supplier) => api.post('/suppliers', supplier),
  update: (supplierId, supplier) => api.put(`/suppliers/${supplierId}`, supplier),
  delete: (supplierId) => api.delete(`/suppliers/${supplierId}`),
};

export const sales = {
  getAll: (page = 1, pageSize = 50) => api.get(`/sales?page=${page}&page_size=${pageSize}`),
  getDetails: (saleId) => api.get(`/sales/${saleId}`),
  create: (sale) => api.post('/sales', sale),
};

export const customers = {
  getAll: (page = 1, pageSize = 50) => api.get(`/customers?page=${page}&page_size=${pageSize}`),
  add: (customer) => api.post('/customers', customer),
};

export const employees = {
  getAll: (page = 1, pageSize = 50) => api.get(`/employees?page=${page}&page_size=${pageSize}`),
  add: (employee) => api.post('/employees', employee),
};

export const dashboard = {
  getStats: () => api.get('/dashboard/stats'),
};

// OPTIMIZED: Combined analytics endpoints into one request
export const reports = {
  // Get all dashboard analytics in one request (was 4 separate API calls)
  getDashboardData: (days = 7) => api.get(`/reports/dashboard?days=${days}`),
  
  // Individual endpoints still available for specific use cases
  getSalesByDate: (days = 7) => api.get(`/reports/sales-by-date?days=${days}`),
  getCategorySales: () => api.get('/reports/category-sales'),
  getTopProducts: (limit = 5) => api.get(`/reports/top-products?limit=${limit}`),
  getAllTimeAnalysis: () => api.get('/reports/all-time-analysis'),
};



export const notifications = {
  getAll: (page = 1, pageSize = 50) => api.get(`/notifications?page=${page}&page_size=${pageSize}`),
  update: (notificationId, status) => api.put(`/notifications/${notificationId}`, { status }),
};

export const purchaseOrders = {
  getAll: (page = 1, pageSize = 30) => api.get(`/purchase-orders?page=${page}&page_size=${pageSize}`),
  getDetails: (orderId) => api.get(`/purchase-orders/${orderId}`),
  create: (order) => api.post('/purchase-orders', order),
  receive: (orderId) => api.put(`/purchase-orders/${orderId}/receive`),
};

export default api;
