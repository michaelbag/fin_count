import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
} from '@mui/material'
import {
  AttachMoney as CurrencyIcon,
  AccountBalance as CashRegisterIcon,
  People as EmployeeIcon,
  Category as IncomeExpenseItemIcon,
  CurrencyExchange as CurrencyRateIcon,
} from '@mui/icons-material'

const referenceTypes = [
  {
    id: 'currencies',
    title: 'Валюты',
    description: 'Управление валютами системы',
    icon: <CurrencyIcon sx={{ fontSize: 48 }} />,
    path: '/references/currencies',
    color: '#2e7d32',
  },
  {
    id: 'cash-registers',
    title: 'Кассы',
    description: 'Управление кассами и их остатками',
    icon: <CashRegisterIcon sx={{ fontSize: 48 }} />,
    path: '/references/cash-registers',
    color: '#1976d2',
  },
  {
    id: 'employees',
    title: 'Сотрудники',
    description: 'Управление сотрудниками организации',
    icon: <EmployeeIcon sx={{ fontSize: 48 }} />,
    path: '/references/employees',
    color: '#ed6c02',
  },
  {
    id: 'income-expense-items',
    title: 'Статьи доходов/расходов',
    description: 'Управление статьями доходов и расходов',
    icon: <IncomeExpenseItemIcon sx={{ fontSize: 48 }} />,
    path: '/references/income-expense-items',
    color: '#9c27b0',
  },
  {
    id: 'currency-rates',
    title: 'Курсы валют',
    description: 'Управление курсами валют',
    icon: <CurrencyRateIcon sx={{ fontSize: 48 }} />,
    path: '/references/currency-rates',
    color: '#0288d1',
  },
]

function ReferencesPage() {
  const navigate = useNavigate()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Справочники
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Выберите справочник для просмотра и редактирования
      </Typography>
      <Grid container spacing={3}>
        {referenceTypes.map((refType) => (
          <Grid item xs={12} sm={6} md={4} key={refType.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(refType.path)}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                <Box sx={{ color: refType.color, mb: 2 }}>
                  {refType.icon}
                </Box>
                <Typography variant="h6" gutterBottom>
                  {refType.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {refType.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                <Button
                  size="small"
                  variant="contained"
                  onClick={(e) => {
                    e.stopPropagation()
                    navigate(refType.path)
                  }}
                >
                  Открыть
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default ReferencesPage
