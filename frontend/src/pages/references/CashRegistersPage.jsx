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
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import EditIcon from '@mui/icons-material/Edit'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { cashRegistersAPI } from '../../services/api'
import { useForm, Controller } from 'react-hook-form'

function CashRegistersPage() {
  const navigate = useNavigate()
  const [cashRegisters, setCashRegisters] = useState([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingCashRegister, setEditingCashRegister] = useState(null)
  const { control, handleSubmit, reset, formState: { errors } } = useForm()

  useEffect(() => {
    loadCashRegisters()
  }, [])

  const loadCashRegisters = async () => {
    try {
      setLoading(true)
      const response = await cashRegistersAPI.getAll()
      setCashRegisters(response.data.results || response.data)
    } catch (err) {
      console.error('Ошибка загрузки касс:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingCashRegister(null)
    reset({ name: '', code: '', description: '', is_active: true })
    setOpenDialog(true)
  }

  const handleEdit = (cashRegister) => {
    setEditingCashRegister(cashRegister)
    reset(cashRegister)
    setOpenDialog(true)
  }

  const onSubmit = async (data) => {
    try {
      if (editingCashRegister) {
        await cashRegistersAPI.update(editingCashRegister.id, data)
      } else {
        await cashRegistersAPI.create(data)
      }
      setOpenDialog(false)
      loadCashRegisters()
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Box>
          <Button
            variant="text"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/references')}
            sx={{ mb: 1 }}
          >
            Назад к справочникам
          </Button>
          <Typography variant="h4">Кассы</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Добавить кассу
        </Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Код</TableCell>
              <TableCell>Название</TableCell>
              <TableCell>Описание</TableCell>
              <TableCell>Активна</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {cashRegisters.map((cashRegister) => (
              <TableRow key={cashRegister.id}>
                <TableCell>{cashRegister.code || '-'}</TableCell>
                <TableCell>{cashRegister.name}</TableCell>
                <TableCell>{cashRegister.description || '-'}</TableCell>
                <TableCell>{cashRegister.is_active ? 'Да' : 'Нет'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEdit(cashRegister)}>
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
          {editingCashRegister ? 'Редактирование кассы' : 'Создание кассы'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
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
              name="code"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Код"
                  margin="normal"
                />
              )}
            />
            <Controller
              name="description"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  multiline
                  rows={3}
                  label="Описание"
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

export default CashRegistersPage

