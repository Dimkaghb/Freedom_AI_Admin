import React from 'react'
import './index.css'
import { Dashboard } from '@/modules/dashboard'
import { Route , Router, Routes } from 'react-router-dom'
import { AuthPage } from '@/modules/auth'

function App() {
  return (
    <Routes >
      <Route path="/" element={<AuthPage />} />
      <Route path="/dashboard" element={<Dashboard />} />
    
    </Routes>
  )
}

export default App