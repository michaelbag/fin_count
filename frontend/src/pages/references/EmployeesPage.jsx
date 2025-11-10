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
import { employeesAPI } from '../../services/api'
import { useForm, Controller } from 'react-hook-form'

function EmployeesPage() {
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
  const [employees, setEmployees] = useState([])
  const [loading, setLoading] = useState(true)
  const [openDialog, setOpenDialog] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState(null)
  const { control, handleSubmit, reset, formState: { errors } } = useForm()

  useEffect(() => {
    loadEmployees()
  }, [])

  const loadEmployees = async () => {
    try {
      setLoading(true)
      const response = await employeesAPI.getAll()
      setEmployees(response.data.results || response.data)
    } catch (err) {
      console.error('Ошибка загрузки сотрудников:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingEmployee(null)
    reset({
      first_name: '',
      last_name: '',
      middle_name: '',
      position: '',
      is_active: true,
    })
    setOpenDialog(true)
  }

  const handleEdit = (employee) => {
    setEditingEmployee(employee)
    reset(employee)
    setOpenDialog(true)
  }

  const onSubmit = async (data) => {
    try {
      if (editingEmployee) {
        await employeesAPI.update(editingEmployee.id, data)
      } else {
        await employeesAPI.create(data)
      }
      setOpenDialog(false)
      loadEmployees()
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
          <Typography variant="h4">Сотрудники</Typography>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleCreate}>
          Добавить сотрудника
        </Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ФИО</TableCell>
              <TableCell>Должность</TableCell>
              <TableCell>Активен</TableCell>
              <TableCell align="right">Действия</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {employees.map((employee) => (
              <TableRow key={employee.id}>
                <TableCell>
                  {employee.full_name ||
                    `${employee.last_name || ''} ${employee.first_name || ''} ${employee.middle_name || ''}`.trim()}
                </TableCell>
                <TableCell>{employee.position || '-'}</TableCell>
                <TableCell>{employee.is_active ? 'Да' : 'Нет'}</TableCell>
                <TableCell align="right">
                  <IconButton size="small" onClick={() => handleEdit(employee)}>
                    <EditIcon />
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
          {editingEmployee ? 'Редактирование сотрудника' : 'Создание сотрудника'}
        </DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <Controller
              name="last_name"
              control={control}
              rules={{ required: 'Фамилия обязательна' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Фамилия"
                  margin="normal"
                  error={!!errors.last_name}
                  helperText={errors.last_name?.message}
                />
              )}
            />
            <Controller
              name="first_name"
              control={control}
              rules={{ required: 'Имя обязательно' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Имя"
                  margin="normal"
                  error={!!errors.first_name}
                  helperText={errors.first_name?.message}
                />
              )}
            />
            <Controller
              name="middle_name"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Отчество"
                  margin="normal"
                />
              )}
            />
            <Controller
              name="position"
              control={control}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Должность"
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
                  label="Активен"
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

export default EmployeesPage

