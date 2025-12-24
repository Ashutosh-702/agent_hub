import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { Provider } from 'react-redux'
import { ThemeProvider } from 'novus'
import { store } from './store'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      {/* Novus ThemeProvider is a side-effect component (it does not render children). */}
      <ThemeProvider mode="light" />
      <App />
    </Provider>
  </StrictMode>,
)
