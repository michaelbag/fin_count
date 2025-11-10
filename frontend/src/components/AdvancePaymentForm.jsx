import React from 'react'
import { useForm, Controller } from 'react-hook-form'
import {
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Button,
  Box,
} from '@mui/material'
import { format } from 'date-fns'

function AdvancePaymentForm({ payment, references, onSave, onCancel }) {
  const { control, handleSubmit, formState: { errors } } = useForm({
    defaultValues: payment
      ? {
          number: payment.number || '',
          date: payment.date ? format(new Date(payment.date), 'yyyy-MM-dd') : '',
          employee: payment.employee || '',
          cash_register: payment.cash_register || '',
          currency: payment.currency || '',
          amount: payment.amount || '',
          expense_item: payment.expense_item || '',
          purpose: payment.purpose || '',
          is_closed: payment.is_closed || false,
        }
      : {
          date: format(new Date(), 'yyyy-MM-dd'),
          amount: '',
          is_closed: false,
        },
  })

  const onSubmit = (data) => {
    onSave(data)
  }

  return (
    <Box component="form" onSubmit={handleSubmit(onSubmit)} sx={{ mt: 2 }}>
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <Controller
            name="number"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label="Номер документа"
                error={!!errors.number}
                helperText={errors.number?.message}
              />
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="date"
            control={control}
            rules={{ required: 'Дата обязательна' }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                type="date"
                label="Дата"
                InputLabelProps={{ shrink: true }}
                error={!!errors.date}
                helperText={errors.date?.message}
              />
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="employee"
            control={control}
            rules={{ required: 'Сотрудник обязателен' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.employee}>
                <InputLabel>Сотрудник</InputLabel>
                <Select {...field} label="Сотрудник">
                  {references.employees.map((emp) => (
                    <MenuItem key={emp.id} value={emp.id}>
                      {emp.full_name || `${emp.last_name} ${emp.first_name}`}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="cash_register"
            control={control}
            rules={{ required: 'Касса обязательна' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.cash_register}>
                <InputLabel>Касса</InputLabel>
                <Select {...field} label="Касса">
                  {references.cashRegisters.map((reg) => (
                    <MenuItem key={reg.id} value={reg.id}>
                      {reg.name} {reg.code ? `(${reg.code})` : ''}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="currency"
            control={control}
            rules={{ required: 'Валюта обязательна' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.currency}>
                <InputLabel>Валюта</InputLabel>
                <Select {...field} label="Валюта">
                  {references.currencies.map((curr) => (
                    <MenuItem key={curr.id} value={curr.id}>
                      {curr.code} - {curr.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="amount"
            control={control}
            rules={{
              required: 'Сумма обязательна',
              min: { value: 0.01, message: 'Сумма должна быть больше 0' },
            }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                type="number"
                label="Сумма"
                inputProps={{ step: '0.01', min: '0.01' }}
                error={!!errors.amount}
                helperText={errors.amount?.message}
              />
            )}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Controller
            name="expense_item"
            control={control}
            rules={{ required: 'Статья расходов обязательна' }}
            render={({ field }) => (
              <FormControl fullWidth error={!!errors.expense_item}>
                <InputLabel>Статья расходов</InputLabel>
                <Select {...field} label="Статья расходов">
                  {references.expenseItems.map((item) => (
                    <MenuItem key={item.id} value={item.id}>
                      {item.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
          />
        </Grid>
        <Grid item xs={12}>
          <Controller
            name="purpose"
            control={control}
            rules={{ required: 'Цель выдачи обязательна' }}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                multiline
                rows={3}
                label="Цель выдачи"
                error={!!errors.purpose}
                helperText={errors.purpose?.message}
              />
            )}
          />
        </Grid>
      </Grid>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mt: 3 }}>
        <Button onClick={onCancel}>Отмена</Button>
        <Button type="submit" variant="contained">
          Сохранить
        </Button>
      </Box>
    </Box>
  )
}

export default AdvancePaymentForm

