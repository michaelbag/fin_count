import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import App from './App'

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  components: {
    // Глобальные настройки для мобильных устройств
    MuiButton: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            minHeight: '44px', // Touch-friendly размер для iOS
          },
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            minWidth: '44px',
            minHeight: '44px',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '@media (max-width: 600px)': {
            '& .MuiInputBase-input': {
              minHeight: '44px',
            },
          },
        },
      },
    },
  },
})

// Добавляем глобальные стили для поддержки safe area на iPhone
const globalStyles = `
  @supports (padding: max(0px)) {
    body {
      padding-left: env(safe-area-inset-left);
      padding-right: env(safe-area-inset-right);
    }
    
    /* Для фиксированных элементов */
    .MuiAppBar-root {
      padding-left: env(safe-area-inset-left);
      padding-right: env(safe-area-inset-right);
    }
  }
  
  /* Улучшенная прокрутка на iOS */
  * {
    -webkit-overflow-scrolling: touch;
  }
  
  /* Предотвращение выделения текста при двойном тапе на мобильных */
  @media (max-width: 600px) {
    button, a {
      -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
    }
  }
`

// Добавляем стили в head
const styleSheet = document.createElement('style')
styleSheet.type = 'text/css'
styleSheet.innerText = globalStyles
document.head.appendChild(styleSheet)

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <App />
      </ThemeProvider>
    </BrowserRouter>
  </React.StrictMode>,
)

