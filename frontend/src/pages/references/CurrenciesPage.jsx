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
  FormControlLabel,
  Switch,
  CircularProgress,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { currenciesAPI } from '../../services/api'
import { useForm, Controller } from 'react-hook-form'

function CurrenciesPage() {
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const [currencies, setCurrencies] = useState([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingCurrency, setEditingCurrency] = useState(null)
  const { control, handleSubmit, reset, formState: { errors } } = useForm()

  useEffect(() => {
    loadCurrencies()
  }, [])

  const loadCurrencies = async () => {
    try {
      setLoading(true)
      const response = await currenciesAPI.getAll()
      setCurrencies(response.data.results || response.data)
    } catch (err) {
      console.error('Ошибка загрузки валют:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingCurrency(null)
    reset({ code: '', name: '', symbol: '', is_active: true })
    setOpenDialog(true)
  }

  const handleEdit = (currency) => {
    setEditingCurrency(currency)
    reset(currency)
    setOpenDialog(true)
  }

  const onSubmit = async (data) => {
    try {
      if (editingCurrency) {
        await currenciesAPI.update(editingCurrency.id, data)
      } else {
        await currenciesAPI.create(data)
      }
      setOpenDialog(false)
      loadCurrencies()
    } catch (err) {
      console.error('Ошибка сохранения:', err)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
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
            onClick={() => navigate('/references')}
            sx={{ 
              mb: { xs: 0.5, sm: 1 },
              minHeight: { xs: '44px', sm: '36px' },
              fontSize: { xs: '0.9rem', sm: '0.875rem' },
            }}
          >
            Назад к справочникам
          </Button>
          <Typography 
            variant="h4"
            sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}
          >
            Валюты
          </Typography>
        </Box>
        <Button 
          variant="contained" 
          startIcon={<AddIcon />} 
          onClick={handleCreate}
          sx={{
            minHeight: { xs: '44px', sm: '36px' },
            fontSize: { xs: '0.9rem', sm: '0.875rem' },
            width: { xs: '100%', sm: 'auto' },
          }}
        >
          Добавить валюту
        </Button>
      </Box>
      <TableContainer 
        component={Paper}
        sx={{
          maxWidth: '100%',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <Table 
          sx={{ 
            minWidth: { xs: 500, sm: 'auto' },
            '& .MuiTableCell-root': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              padding: { xs: '8px', sm: '16px' },
            },
          }}
        >
          <TableHead>
            <TableRow>
              <TableCell>Код</TableCell>
              <TableCell>Название</TableCell>
              <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>Символ</TableCell>
              <TableCell>Активна</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currencies.map((currency) => (
              <TableRow key={currency.id}>
                <TableCell>{currency.code}</TableCell>
                <TableCell>{currency.name}</TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  {currency.symbol}
                </TableCell>
                <TableCell>{currency.is_active ? 'Да' : 'Нет'}</TableCell>
                <TableCell align="right">
                  <IconButton 
                    size="small" 
                    onClick={() => handleEdit(currency)}
                    sx={{ 
                      minWidth: { xs: '44px', sm: 'auto' },
                      minHeight: { xs: '44px', sm: 'auto' },
                    }}
                  >
                    <EditIcon fontSize={isMobile ? 'medium' : 'small'} />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog 
        open={openDialog} 
        onClose={() => setOpenDialog(false)} 
        maxWidth="sm" 
        fullWidth
        fullScreen={isMobile}
        sx={{
          '& .MuiDialog-paper': {
            m: { xs: 0, sm: 2 },
            maxHeight: { xs: '100vh', sm: '90vh' },
          },
        }}
      >
        <DialogTitle>
          {editingCurrency ? 'Редактирование валюты' : 'Создание валюты'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <Controller
              name="code"
              control={control}
              rules={{ required: 'Код обязателен' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Код валюты"
                  margin="normal"
                  error={!!errors.code}
                  helperText={errors.code?.message}
                />
              )}
            />
            <Controller
              name="name"
              control={control}
              rules={{ required: 'Название обязательно' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Название"
                  margin="normal"
                  error={!!errors.name}
                  helperText={errors.name?.message}
                />
              )}
            />
            <Controller
              name="symbol"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Символ"
                  margin="normal"
                />
              )}
            />
            <Controller
              name="is_active"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Switch {...field} checked={field.value} />}
                  label="Активна"
                  sx={{ mt: 2 }}
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: { xs: 2, sm: 3 } }}>
          <Button 
            onClick={() => setOpenDialog(false)}
            sx={{ 
              minHeight: { xs: '44px', sm: 'auto' },
              fontSize: { xs: '0.9rem', sm: '0.875rem' },
            }}
          >
            Отмена
          </Button>
          <Button 
            onClick={handleSubmit(onSubmit)} 
            variant="contained"
            sx={{ 
              minHeight: { xs: '44px', sm: 'auto' },
              fontSize: { xs: '0.9rem', sm: '0.875rem' },
            }}
          >
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CurrenciesPage

