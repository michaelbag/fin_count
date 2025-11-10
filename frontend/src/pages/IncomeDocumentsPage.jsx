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
  Chip,
  CircularProgress,
  Alert,
  Pagination,
  Grid,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { format } from 'date-fns'
import { incomeDocumentsAPI, cashRegistersAPI, currenciesAPI } from '../services/api'

function IncomeDocumentsPage() {
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)
  const [cashRegisters, setCashRegisters] = useState([])
  const [currencies, setCurrencies] = useState([])
  
  // Фильтры
  const [filters, setFilters] = useState({
    cash_register: '',
    currency: '',
    date_from: '',
    date_to: '',
  })

  useEffect(() => {
    loadReferences()
  }, [])

  useEffect(() => {
    loadDocuments()
  }, [page, filters.cash_register, filters.currency, filters.date_from, filters.date_to])

  const loadDocuments = async () => {
    try {
      setLoading(true)
      setError(null)
      const params = {
        page,
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, v]) => v !== '')
        ),
      }
      const response = await incomeDocumentsAPI.getAll(params)
      const data = response.data.results || response.data
      setDocuments(Array.isArray(data) ? data : [])
      const totalCount = response.data.count || (Array.isArray(data) ? data.length : 0)
      setCount(Math.ceil(totalCount / 50) || 1)
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Неизвестная ошибка'
      setError('Ошибка загрузки данных: ' + errorMessage)
      setDocuments([])
      setCount(0)
    } finally {
      setLoading(false)
    }
  }

  const loadReferences = async () => {
    try {
      const [cashRegistersRes, currenciesRes] = await Promise.all([
        cashRegistersAPI.getAll({ is_active: 'true' }),
        currenciesAPI.getAll({ is_active: 'true' }),
      ])
      setCashRegisters(cashRegistersRes.data.results || cashRegistersRes.data || [])
      setCurrencies(currenciesRes.data.results || currenciesRes.data || [])
    } catch (err) {
      console.error('Ошибка загрузки справочников:', err)
      setCashRegisters([])
      setCurrencies([])
    }
  }

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({ ...prev, [field]: value }))
    setPage(1) // Сбрасываем на первую страницу при изменении фильтра
  }

  const handleDelete = async (id) => {
    if (window.confirm('Вы уверены, что хотите удалить этот документ?')) {
      try {
        await incomeDocumentsAPI.delete(id)
        loadDocuments()
      } catch (err) {
        setError('Ошибка удаления: ' + (err.response?.data?.detail || err.message))
      }
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    try {
      return format(new Date(dateString), 'dd.MM.yyyy')
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
      <Box 
        sx={{ 
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          justifyContent: 'space-between', 
          alignItems: { xs: 'stretch', sm: 'flex-start' },
          mb: { xs: 2, sm: 3 },
          gap: { xs: 2, sm: 0 },
        }}
      >
        <Box sx={{ flex: 1 }}>
          <Button
            variant="text"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/documents')}
            sx={{ 
              mb: { xs: 0.5, sm: 1 },
              minHeight: { xs: '44px', sm: '36px' },
              fontSize: { xs: '0.9rem', sm: '0.875rem' },
            }}
          >
            Назад к документам
          </Button>
          <Typography 
            variant="h4"
            sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}
          >
            Приход денежных средств
          </Typography>
        </Box>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />}
          sx={{ 
            minHeight: { xs: '44px', sm: '36px' },
            fontSize: { xs: '0.9rem', sm: '0.875rem' },
            width: { xs: '100%', sm: 'auto' },
          }}
        >
          Создать
        </Button>
      </Box>

      {/* Фильтры */}
      <Paper sx={{ p: { xs: 1.5, sm: 2 }, mb: { xs: 2, sm: 3 } }}>
        <Typography 
          variant="h6" 
          gutterBottom
          sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
        >
          Фильтры
        </Typography>
        <Grid container spacing={{ xs: 1.5, sm: 2 }}>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Касса</InputLabel>
              <Select
                value={filters.cash_register}
                label="Касса"
                onChange={(e) => handleFilterChange('cash_register', e.target.value)}
                sx={{ 
                  '& .MuiSelect-select': { 
                    minHeight: { xs: '44px', sm: 'auto' },
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                  } 
                }}
              >
                <MenuItem value="">Все кассы</MenuItem>
                {cashRegisters.map((reg) => (
                  <MenuItem key={reg.id} value={reg.id}>
                    {reg.name} {reg.code ? `(${reg.code})` : ''}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Валюта</InputLabel>
              <Select
                value={filters.currency}
                label="Валюта"
                onChange={(e) => handleFilterChange('currency', e.target.value)}
                sx={{ 
                  '& .MuiSelect-select': { 
                    minHeight: { xs: '44px', sm: 'auto' },
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                  } 
                }}
              >
                <MenuItem value="">Все валюты</MenuItem>
                {currencies.map((curr) => (
                  <MenuItem key={curr.id} value={curr.id}>
                    {curr.code} - {curr.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="date"
              label="Дата от"
              InputLabelProps={{ shrink: true }}
              value={filters.date_from}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              sx={{ 
                '& .MuiInputBase-input': { 
                  minHeight: { xs: '44px', sm: 'auto' },
                  fontSize: { xs: '0.9rem', sm: '1rem' },
                } 
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <TextField
              fullWidth
              type="date"
              label="Дата до"
              InputLabelProps={{ shrink: true }}
              value={filters.date_to}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              sx={{ 
                '& .MuiInputBase-input': { 
                  minHeight: { xs: '44px', sm: 'auto' },
                  fontSize: { xs: '0.9rem', sm: '1rem' },
                } 
              }}
            />
          </Grid>
        </Grid>
      </Paper>

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
          <TableContainer 
            component={Paper}
            sx={{
              maxWidth: '100%',
              overflowX: 'auto',
              // Улучшенная прокрутка на мобильных
              WebkitOverflowScrolling: 'touch',
              '&::-webkit-scrollbar': {
                height: { xs: '8px', sm: '12px' },
              },
            }}
          >
            <Table 
              sx={{ 
                minWidth: { xs: 800, sm: 'auto' }, // Минимальная ширина для горизонтальной прокрутки
                '& .MuiTableCell-root': {
                  fontSize: { xs: '0.75rem', sm: '0.875rem' },
                  padding: { xs: '8px', sm: '16px' },
                  whiteSpace: { xs: 'nowrap', sm: 'normal' },
                },
              }}
            >
              <TableHead>
                <TableRow>
                  <TableCell>№</TableCell>
                  <TableCell>Дата</TableCell>
                  <TableCell>Касса</TableCell>
                  <TableCell>Валюта</TableCell>
                  <TableCell>Сумма</TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>Статья дохода</TableCell>
                  <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>Описание</TableCell>
                  <TableCell>Статус</TableCell>
                  <TableCell align="right">Действия</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {documents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={9} align="center">
                      Нет данных
                    </TableCell>
                  </TableRow>
                ) : (
                  documents.map((doc) => (
                    <TableRow key={doc.id} hover>
                      <TableCell>{doc.number || '-'}</TableCell>
                      <TableCell>{formatDate(doc.date)}</TableCell>
                      <TableCell>{doc.cash_register_name || doc.cash_register || '-'}</TableCell>
                      <TableCell>{doc.currency_code || doc.currency || '-'}</TableCell>
                      <TableCell>{formatAmount(doc.amount)}</TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                        {doc.item_name || doc.item || '-'}
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                        {doc.description || '-'}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {doc.is_posted && (
                            <Chip label="Проведен" color="success" size="small" />
                          )}
                          {doc.is_deleted && (
                            <Chip label="Удален" color="error" size="small" />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          onClick={() => {}}
                          color="primary"
                          sx={{ 
                            minWidth: { xs: '44px', sm: 'auto' },
                            minHeight: { xs: '44px', sm: 'auto' },
                          }}
                        >
                          <EditIcon fontSize={isMobile ? 'medium' : 'small'} />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleDelete(doc.id)}
                          color="error"
                          sx={{ 
                            minWidth: { xs: '44px', sm: 'auto' },
                            minHeight: { xs: '44px', sm: 'auto' },
                          }}
                        >
                          <DeleteIcon fontSize={isMobile ? 'medium' : 'small'} />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          {count > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: { xs: 2, sm: 3 } }}>
              <Pagination
                count={count}
                page={page}
                onChange={(e, value) => setPage(value)}
                color="primary"
                size={isMobile ? 'small' : 'medium'}
                sx={{
                  '& .MuiPaginationItem-root': {
                    minWidth: { xs: '36px', sm: '40px' },
                    minHeight: { xs: '36px', sm: '40px' },
                    fontSize: { xs: '0.875rem', sm: '1rem' },
                  },
                }}
              />
            </Box>
          )}
        </>
      )}
    </Box>
  )
}

export default IncomeDocumentsPage

