import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Важно для сессионной аутентификации и CSRF
})

// CSRF токен больше не требуется, так как мы отключили CSRF проверку для API endpoints
// через middleware DisableCSRFForAPI

// Interceptor для обработки ошибок
let onUnauthorized = null

export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Вызываем обработчик неавторизованного доступа
      if (onUnauthorized) {
        onUnauthorized()
      }
    }
    return Promise.reject(error)
  }
)

export default api

// API методы для документов
export const advancePaymentsAPI = {
  getAll: (params) => api.get('/advance-payments/', { params }),
  getById: (id) => api.get(`/advance-payments/${id}/`),
  create: (data) => api.post('/advance-payments/', data),
  update: (id, data) => api.put(`/advance-payments/${id}/`, data),
  delete: (id) => api.delete(`/advance-payments/${id}/`),
  getUnreportedBalance: (id) => api.get(`/advance-payments/${id}/unreported_balance/`),
}

export const incomeDocumentsAPI = {
  getAll: (params) => api.get('/income-documents/', { params }),
  getById: (id) => api.get(`/income-documents/${id}/`),
  create: (data) => api.post('/income-documents/', data),
  update: (id, data) => api.put(`/income-documents/${id}/`, data),
  delete: (id) => api.delete(`/income-documents/${id}/`),
}

// API методы для справочников
export const currenciesAPI = {
  getAll: (params) => api.get('/currencies/', { params }),
  getById: (id) => api.get(`/currencies/${id}/`),
  create: (data) => api.post('/currencies/', data),
  update: (id, data) => api.put(`/currencies/${id}/`, data),
  delete: (id) => api.delete(`/currencies/${id}/`),
}

export const cashRegistersAPI = {
  getAll: (params) => api.get('/cash-registers/', { params }),
  getById: (id) => api.get(`/cash-registers/${id}/`),
  create: (data) => api.post('/cash-registers/', data),
  update: (id, data) => api.put(`/cash-registers/${id}/`, data),
  delete: (id) => api.delete(`/cash-registers/${id}/`),
}

export const employeesAPI = {
  getAll: (params) => api.get('/employees/', { params }),
  getById: (id) => api.get(`/employees/${id}/`),
  create: (data) => api.post('/employees/', data),
  update: (id, data) => api.put(`/employees/${id}/`, data),
  delete: (id) => api.delete(`/employees/${id}/`),
}

export const incomeExpenseItemsAPI = {
  getAll: (params) => api.get('/income-expense-items/', { params }),
  getById: (id) => api.get(`/income-expense-items/${id}/`),
  create: (data) => api.post('/income-expense-items/', data),
  update: (id, data) => api.put(`/income-expense-items/${id}/`, data),
  delete: (id) => api.delete(`/income-expense-items/${id}/`),
}

export const currencyRatesAPI = {
  getAll: (params) => api.get('/currency-rates/', { params }),
  getById: (id) => api.get(`/currency-rates/${id}/`),
  create: (data) => api.post('/currency-rates/', data),
  update: (id, data) => api.put(`/currency-rates/${id}/`, data),
  delete: (id) => api.delete(`/currency-rates/${id}/`),
}

// API методы для аутентификации
export const authAPI = {
  login: (username, password) => api.post('/auth/login/', { username, password }),
  logout: () => api.post('/auth/logout/'),
  getCurrentUser: () => api.get('/auth/current-user/'),
}
