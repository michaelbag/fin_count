import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Box } from '@mui/material'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import DocumentsPage from './pages/DocumentsPage'
import AdvancePaymentsPage from './pages/AdvancePaymentsPage'
import IncomeDocumentsPage from './pages/IncomeDocumentsPage'
import ReferencesPage from './pages/ReferencesPage'
import CurrenciesPage from './pages/references/CurrenciesPage'
import CashRegistersPage from './pages/references/CashRegistersPage'
import EmployeesPage from './pages/references/EmployeesPage'
import ReportsPage from './pages/ReportsPage'

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
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
    </Box>
  )
}

export default App

