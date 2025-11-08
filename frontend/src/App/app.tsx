import React from 'react'
import './index.css'
import { Dashboard } from '@/modules/dashboard'
import { Route, Routes, Navigate } from 'react-router-dom'
import { AuthPage } from '@/modules/auth'
import { RegisterPage } from '@/modules/register'
import { AuthProvider, useAuth } from '@/shared/stores/authstore'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { HoldiingAdminDashboard } from '@/modules/holdingAdminDashboard'
import { AddUserPage } from '@/modules/AddUserPage'

// Redirect to dashboard if already authenticated
function AuthPageWrapper() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></div>
          <p className="mt-2 text-sm text-gray-600">Загрузка...</p>
        </div>
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <AuthPage />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<AuthPageWrapper />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/hadmin"
        element={
          <ProtectedRoute>
            <HoldiingAdminDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/adduser"
        element={
          <ProtectedRoute>
            <AddUserPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App