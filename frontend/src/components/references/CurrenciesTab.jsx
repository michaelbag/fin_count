import React, { useState, useEffect } from 'react'
import {
  Box,
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
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import { currenciesAPI } from '../../services/api'
import { useForm, Controller } from 'react-hook-form'

function CurrenciesTab() {
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
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Добавить валюту
        </Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Код</TableCell>
              <TableCell>Название</TableCell>
              <TableCell>Символ</TableCell>
              <TableCell>Активна</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {currencies.map((currency) => (
              <TableRow key={currency.id}>
                <TableCell>{currency.code}</TableCell>
                <TableCell>{currency.name}</TableCell>
                <TableCell>{currency.symbol}</TableCell>
                <TableCell>{currency.is_active ? 'Да' : 'Нет'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEdit(currency)}>
                    <EditIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
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
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Отмена</Button>
          <Button onClick={handleSubmit(onSubmit)} variant="contained">
            Сохранить
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default CurrenciesTab

