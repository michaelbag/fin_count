import React from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  Card,
  CardContent,
  CardActions,
} from '@mui/material'
import {
  AccountBalanceWallet as IncomeIcon,
  Payment as ExpenseIcon,
  AccountBalance as AdvancePaymentIcon,
  Description as AdvanceReportIcon,
  Reply as ReturnIcon,
  AddCircle as AdditionalIcon,
  SwapHoriz as TransferIcon,
  CurrencyExchange as ConversionIcon,
} from '@mui/icons-material'

const documentTypes = [
  {
    id: 'income',
    title: 'Приход денежных средств',
    description: 'Документы поступления денежных средств в кассу',
    icon: <IncomeIcon sx={{ fontSize: 48 }} />,
    path: '/documents/income',
    color: '#2e7d32',
  },
  {
    id: 'expense',
    title: 'Расход денежных средств',
    description: 'Документы выдачи денежных средств из кассы',
    icon: <ExpenseIcon sx={{ fontSize: 48 }} />,
    path: '/documents/expense',
    color: '#d32f2f',
  },
  {
    id: 'advance-payment',
    title: 'Выдача подотчетных средств',
    description: 'Документы выдачи денег подотчетным лицам',
    icon: <AdvancePaymentIcon sx={{ fontSize: 48 }} />,
    path: '/documents/advance-payment',
    color: '#1976d2',
  },
  {
    id: 'advance-report',
    title: 'Авансовый отчет',
    description: 'Документы подтверждения расходов подотчетных средств',
    icon: <AdvanceReportIcon sx={{ fontSize: 48 }} />,
    path: '/documents/advance-report',
    color: '#ed6c02',
  },
  {
    id: 'advance-return',
    title: 'Возврат подотчетных средств',
    description: 'Документы возврата неиспользованных подотчетных средств',
    icon: <ReturnIcon sx={{ fontSize: 48 }} />,
    path: '/documents/advance-return',
    color: '#9c27b0',
  },
  {
    id: 'additional-advance-payment',
    title: 'Дополнительная выдача',
    description: 'Документы дополнительной выдачи подотчетных средств',
    icon: <AdditionalIcon sx={{ fontSize: 48 }} />,
    path: '/documents/additional-advance-payment',
    color: '#0288d1',
  },
  {
    id: 'cash-transfer',
    title: 'Перевод между кассами',
    description: 'Документы перевода денежных средств между кассами',
    icon: <TransferIcon sx={{ fontSize: 48 }} />,
    path: '/documents/cash-transfer',
    color: '#00796b',
  },
  {
    id: 'currency-conversion',
    title: 'Конвертация валют',
    description: 'Документы конвертации валют в кассе',
    icon: <ConversionIcon sx={{ fontSize: 48 }} />,
    path: '/documents/currency-conversion',
    color: '#f57c00',
  },
]

function DocumentsPage() {
  const navigate = useNavigate()

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Документы
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Выберите тип документа для просмотра и редактирования
      </Typography>
      <Grid container spacing={3}>
        {documentTypes.map((docType) => (
          <Grid item xs={12} sm={6} md={4} key={docType.id}>
            <Card
              sx={{
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                cursor: 'pointer',
                transition: 'transform 0.2s, box-shadow 0.2s',
                '&:active': {
                  transform: 'scale(0.98)',
                },
                '&:hover': {
                  transform: { xs: 'none', sm: 'translateY(-4px)' },
                  boxShadow: { xs: 2, sm: 4 },
                },
              }}
              onClick={() => navigate(docType.path)}
            >
              <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: { xs: 2, sm: 3 } }}>
                <Box sx={{ color: docType.color, mb: { xs: 1.5, sm: 2 } }}>
                  {React.cloneElement(docType.icon, { 
                    sx: { fontSize: { xs: 40, sm: 48 } } 
                  })}
                </Box>
                <Typography 
                  variant="h6" 
                  gutterBottom
                  sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
                >
                  {docType.title}
                </Typography>
                <Typography 
                  variant="body2" 
                  color="text.secondary"
                  sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
                >
                  {docType.description}
                </Typography>
              </CardContent>
              <CardActions sx={{ justifyContent: 'center', pb: { xs: 1.5, sm: 2 } }}>
                <Button
                  size="small"
                  variant="contained"
                  onClick={(e) => {
                    e.stopPropagation()
                    navigate(docType.path)
                  }}
                  sx={{
                    minHeight: { xs: '44px', sm: 'auto' },
                    fontSize: { xs: '0.9rem', sm: '0.875rem' },
                    px: { xs: 3, sm: 2 },
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

export default DocumentsPage

