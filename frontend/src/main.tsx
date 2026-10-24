import '@fontsource/poppins/latin-400.css'
import '@fontsource/poppins/latin-500.css'
import '@fontsource/poppins/latin-600.css'
import '@fontsource/poppins/latin-700.css'
import './global.css'

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import HomeRoute from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <HomeRoute />
  </StrictMode>,
)
