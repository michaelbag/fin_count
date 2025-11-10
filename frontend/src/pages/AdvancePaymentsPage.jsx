import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  CircularProgress,
  Alert,
  Pagination,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { advancePaymentsAPI, currenciesAPI, cashRegistersAPI, employeesAPI, incomeExpenseItemsAPI } from '../services/api'
import AdvancePaymentForm from '../components/AdvancePaymentForm'

function AdvancePaymentsPage() {
  const navigate = useNavigate()
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingPayment, setEditingPayment] = useState(null)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [references, setReferences] = useState({
    currencies: [],
    cashRegisters: [],
    employees: [],
    expenseItems: [],
  })

  useEffect(() => {
    loadPayments()
    loadReferences()
  }, [page])

  const loadPayments = async () => {
    try {
      setLoading(true)
      const response = await advancePaymentsAPI.getAll({ page })
      setPayments(response.data.results || response.data)
      setCount(Math.ceil((response.data.count || response.data.length) / 50))
    } catch (err) {
      setError('Ошибка загрузки данных: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const loadReferences = async () => {
    try {
      const [currenciesRes, cashRegistersRes, employeesRes, expenseItemsRes] = await Promise.all([
        currenciesAPI.getAll({ is_active: 'true' }),
        cashRegistersAPI.getAll({ is_active: 'true' }),
        employeesAPI.getAll({ is_active: 'true' }),
        incomeExpenseItemsAPI.getAll({ type: 'expense', is_active: 'true' }),
      ])
      setReferences({
        currencies: currenciesRes.data.results || currenciesRes.data,
        cashRegisters: cashRegistersRes.data.results || cashRegistersRes.data,
        employees: employeesRes.data.results || employeesRes.data,
        expenseItems: expenseItemsRes.data.results || expenseItemsRes.data,
      })
    } catch (err) {
      console.error('Ошибка загрузки справочников:', err)
    }
  }

  const handleCreate = () => {
    setEditingPayment(null)
    setOpenDialog(true)
  }

  const handleEdit = (payment) => {
    setEditingPayment(payment)
    setOpenDialog(true)
  }

  const handleDelete = async (id) => {
    if (window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      try {
        await advancePaymentsAPI.delete(id)
        loadPayments()
      } catch (err) {
        setError('Ошибка удаления: ' + (err.response?.data?.detail || err.message))
      }
    }
  }

  const handleSave = async (data) => {
    try {
      if (editingPayment) {
        await advancePaymentsAPI.update(editingPayment.id, data)
      } else {
        await advancePaymentsAPI.create(data)
      }
      setOpenDialog(false)
      loadPayments()
    } catch (err) {
      setError('Ошибка сохранения: ' + (err.response?.data?.detail || err.message))
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    try {
      return format(new Date(dateString), 'dd.MM.yyyy', { locale: ru })
    } catch {
      return dateString
    }
  }

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(amount)
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Button
            variant="text"
            onClick={() => navigate('/documents')}
            sx={{ mb: 1 }}
          >
            ← Назад к документам
          </Button>
          <Typography variant="h4">Выдачи подотчетных средств</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Создать
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>Сотрудник</TableCell>
                  <TableCell>Касса</TableCell>
                  <TableCell>Валюта</TableCell>
                  <TableCell>Сумма</TableCell>
                  <TableCell>Статья расходов</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {payments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      Нет данных
                    </TableCell>
                  </TableRow>
                ) : (
                  payments.map((payment) => (
                    <TableRow key={payment.id} hover>
                      <TableCell>{payment.number || '-'}</TableCell>
                      <TableCell>{formatDate(payment.date)}</TableCell>
                      <TableCell>{payment.employee_name || payment.employee || '-'}</TableCell>
                      <TableCell>{payment.cash_register_name || payment.cash_register || '-'}</TableCell>
                      <TableCell>{payment.currency_code || payment.currency || '-'}</TableCell>
                      <TableCell>{formatAmount(payment.amount)}</TableCell>
                      <TableCell>{payment.expense_item_name || payment.expense_item || '-'}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {payment.is_posted && (
                            <Chip label="Проведен" color="success" size="small" />
                          )}
                          {payment.is_closed && (
                            <Chip label="Закрыт" color="info" size="small" />
                          )}
                          {payment.is_deleted && (
                            <Chip label="Удален" color="error" size="small" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => handleEdit(payment)}
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(payment.id)}
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {count > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
              <Pagination
                count={count}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
              />
            </Box>
          )}
        </>
      )}

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPayment ? 'Редактирование выдачи' : 'Создание выдачи'}
        </DialogTitle>
        <DialogContent>
          <AdvancePaymentForm
            payment={editingPayment}
            references={references}
            onSave={handleSave}
            onCancel={() => setOpenDialog(false)}
          />
        </DialogContent>
      </Dialog>
    </Box>
  )
}

export default AdvancePaymentsPage

