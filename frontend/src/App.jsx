import React, { useEffect } from 'react'
import { Routes, Route, useNavigate } from 'react-router-dom'
import { Box } from '@mui/material'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import DocumentsPage from './pages/DocumentsPage'
import AdvancePaymentsPage from './pages/AdvancePaymentsPage'
import IncomeDocumentsPage from './pages/IncomeDocumentsPage'
import ReferencesPage from './pages/ReferencesPage'
import CurrenciesPage from './pages/references/CurrenciesPage'
import CashRegistersPage from './pages/references/CashRegistersPage'
import EmployeesPage from './pages/references/EmployeesPage'
import ReportsPage from './pages/ReportsPage'
import { setUnauthorizedHandler } from './services/api'

// Компонент для настройки обработчика неавторизованного доступа
function AuthHandler() {
  const navigate = useNavigate()
  const { logout } = useAuth()

  useEffect(() => {
    setUnauthorizedHandler(() => {
      logout()
      navigate('/login')
    })
  }, [navigate, logout])

  return null
}

function AppRoutes() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <AuthHandler />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <Layout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/documents" element={<DocumentsPage />} />
                  <Route path="/documents/advance-payment" element={<AdvancePaymentsPage />} />
                  <Route path="/documents/income" element={<IncomeDocumentsPage />} />
                  <Route path="/advance-payments" element={<AdvancePaymentsPage />} />
                  <Route path="/references" element={<ReferencesPage />} />
                  <Route path="/references/currencies" element={<CurrenciesPage />} />
                  <Route path="/references/cash-registers" element={<CashRegistersPage />} />
                  <Route path="/references/employees" element={<EmployeesPage />} />
                  <Route path="/reports" element={<ReportsPage />} />
                </Routes>
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Box>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App

