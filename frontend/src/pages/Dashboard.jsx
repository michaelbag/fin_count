import React from 'react'
import { Typography, Box, Grid, Paper, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import DescriptionIcon from '@mui/icons-material/Description'
import FolderIcon from '@mui/icons-material/Folder'
import AssessmentIcon from '@mui/icons-material/Assessment'

function Dashboard() {
  const navigate = useNavigate()

  const cards = [
    {
      title: 'Документы',
      description: 'Просмотр и редактирование всех документов системы',
      icon: <DescriptionIcon sx={{ fontSize: 48 }} />,
      path: '/documents',
      color: '#1976d2',
    },
    {
      title: 'Справочники',
      description: 'Управление справочниками системы',
      icon: <FolderIcon sx={{ fontSize: 48 }} />,
      path: '/references',
      color: '#dc004e',
    },
    {
      title: 'Отчеты',
      description: 'Просмотр и экспорт отчетов',
      icon: <AssessmentIcon sx={{ fontSize: 48 }} />,
      path: '/reports',
      color: '#2e7d32',
    },
  ]

  return (
    <Box>
      <Typography 
        variant="h4" 
        gutterBottom
        sx={{ fontSize: { xs: '1.5rem', sm: '2.125rem' } }}
      >
        Главная
      </Typography>
      <Grid container spacing={{ xs: 2, sm: 3 }} sx={{ mt: { xs: 1, sm: 2 } }}>
        {cards.map((card) => (
          <Grid item xs={12} sm={6} md={4} key={card.title}>
            <Paper
              sx={{
                p: { xs: 2, sm: 3 },
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                '&:active': {
                  transform: 'scale(0.98)',
                },
                '&:hover': {
                  transform: { xs: 'none', sm: 'translateY(-4px)' },
                  boxShadow: { xs: 2, sm: 4 },
                },
              }}
              onClick={() => navigate(card.path)}
            >
              <Box sx={{ color: card.color, mb: { xs: 1.5, sm: 2 } }}>
                {React.cloneElement(card.icon, { 
                  sx: { fontSize: { xs: 40, sm: 48 } } 
                })}
              </Box>
              <Typography 
                variant="h6" 
                gutterBottom
                sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }}
              >
                {card.title}
              </Typography>
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mb: { xs: 1.5, sm: 2 }, fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
              >
                {card.description}
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                sx={{ 
                  minHeight: { xs: '44px', sm: '36px' }, // Touch-friendly размер
                  fontSize: { xs: '0.9rem', sm: '0.875rem' },
                  px: { xs: 3, sm: 2 },
                }}
              >
                Перейти
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>
    </Box>
  )
}

export default Dashboard

