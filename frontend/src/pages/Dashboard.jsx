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
      <Typography variant="h4" gutterBottom>
        Главная
      </Typography>
      <Grid container spacing={3} sx={{ mt: 2 }}>
        {cards.map((card) => (
          <Grid item xs={12} md={4} key={card.title}>
            <Paper
              sx={{
                p: 3,
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
              onClick={() => navigate(card.path)}
            >
              <Box sx={{ color: card.color, mb: 2 }}>{card.icon}</Box>
              <Typography variant="h6" gutterBottom>
                {card.title}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {card.description}
              </Typography>
              <Button variant="contained" color="primary">
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

