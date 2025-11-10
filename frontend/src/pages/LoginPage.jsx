import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useAuth } from '../contexts/AuthContext'
import { authAPI } from '../services/api'

function LoginPage() {
  const navigate = useNavigate()
  const { login, isAuthenticated, loading } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Если уже авторизован, перенаправляем на главную
  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate('/')
    }
  }, [isAuthenticated, loading, navigate])


  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)

    if (!username || !password) {
      setError('Введите имя пользователя и пароль')
      setSubmitting(false)
      return
    }

    const result = await login(username, password)
    
    if (result.success) {
      navigate('/')
    } else {
      setError(result.error || 'Ошибка авторизации')
    }
    
    setSubmitting(false)
  }

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            maxWidth: 400,
          }}
        >
          <Typography
            variant="h4"
            component="h1"
            gutterBottom
            align="center"
            sx={{ mb: 3, fontSize: { xs: '1.5rem', sm: '2.125rem' } }}
          >
            Вход в систему
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Имя пользователя"
              variant="outlined"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              margin="normal"
              required
              autoFocus
              disabled={submitting}
              sx={{
                '& .MuiInputBase-input': {
                  minHeight: { xs: '44px', sm: 'auto' },
                },
              }}
            />
            <TextField
              fullWidth
              label="Пароль"
              type="password"
              variant="outlined"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              margin="normal"
              required
              disabled={submitting}
              sx={{
                '& .MuiInputBase-input': {
                  minHeight: { xs: '44px', sm: 'auto' },
                },
              }}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              color="primary"
              size="large"
              disabled={submitting}
              sx={{
                mt: 3,
                mb: 2,
                minHeight: { xs: '44px', sm: '48px' },
                fontSize: { xs: '0.9rem', sm: '1rem' },
              }}
            >
              {submitting ? <CircularProgress size={24} /> : 'Войти'}
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  )
}

export default LoginPage

