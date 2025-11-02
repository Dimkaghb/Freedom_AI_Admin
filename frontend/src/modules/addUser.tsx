"use client"

import type React from "react"
import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EyeIcon, EyeOffIcon, RefreshCwIcon, CheckIcon, XIcon, UserPlusIcon } from "lucide-react"

// Types and interfaces for better type safety
interface User {
  firstName: string
  lastName: string
  email: string
  role: string
  tempPassword: string
}

interface FormErrors {
  firstName?: string
  lastName?: string
  email?: string
  role?: string
  tempPassword?: string
}

interface AddUserFormProps {
  onAddUser: (user: User) => void
  isLoading?: boolean
}

// Role options with proper typing
const ROLE_OPTIONS = [
  { value: "admin", label: "Администратор" },
  { value: "manager", label: "Менеджер" },
  { value: "user", label: "Пользователь" },
  { value: "viewer", label: "Наблюдатель" },
] as const

/**
 * AddUserForm component for creating new users with comprehensive validation and accessibility
 * @param onAddUser - Callback function to handle user creation
 * @param isLoading - Loading state for form submission
 */
export function AddUserForm({ onAddUser, isLoading = false }: AddUserFormProps) {
  // Form state management
  const [formData, setFormData] = useState<User>({
    firstName: "",
    lastName: "",
    email: "",
    role: "",
    tempPassword: "",
  })

  // Form validation and UI state
  const [errors, setErrors] = useState<FormErrors>({})
  const [showPassword, setShowPassword] = useState(false)
  const [isGeneratingPassword, setIsGeneratingPassword] = useState(false)
  const [touched, setTouched] = useState<Record<keyof User, boolean>>({
    firstName: false,
    lastName: false,
    email: false,
    role: false,
    tempPassword: false,
  })

  /**
   * Validates email format using regex
   */
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  /**
   * Validates password strength
   */
  const isValidPassword = (password: string): boolean => {
    return password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /\d/.test(password)
  }

  /**
   * Comprehensive form validation
   */
  const validateForm = useCallback((): FormErrors => {
    const newErrors: FormErrors = {}

    // First name validation
    if (!formData.firstName.trim()) {
      newErrors.firstName = "Имя обязательно для заполнения"
    } else if (formData.firstName.trim().length < 2) {
      newErrors.firstName = "Имя должно содержать минимум 2 символа"
    }

    // Last name validation
    if (!formData.lastName.trim()) {
      newErrors.lastName = "Фамилия обязательна для заполнения"
    } else if (formData.lastName.trim().length < 2) {
      newErrors.lastName = "Фамилия должна содержать минимум 2 символа"
    }

    // Email validation
    if (!formData.email.trim()) {
      newErrors.email = "Email обязателен для заполнения"
    } else if (!isValidEmail(formData.email)) {
      newErrors.email = "Введите корректный email адрес"
    }

    // Role validation
    if (!formData.role) {
      newErrors.role = "Выберите роль пользователя"
    }

    // Password validation
    if (!formData.tempPassword) {
      newErrors.tempPassword = "Временный пароль обязателен"
    } else if (!isValidPassword(formData.tempPassword)) {
      newErrors.tempPassword = "Пароль должен содержать минимум 8 символов, включая заглавные и строчные буквы, цифры"
    }

    return newErrors
  }, [formData])

  /**
   * Generates a secure random password
   */
  const generatePassword = useCallback(async () => {
    setIsGeneratingPassword(true)
    
    // Simulate async password generation
    await new Promise(resolve => setTimeout(resolve, 500))
    
    const length = 12
    const uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    const lowercase = "abcdefghijklmnopqrstuvwxyz"
    const numbers = "0123456789"
    const symbols = "!@#$%^&*"
    const allChars = uppercase + lowercase + numbers + symbols
    
    let password = ""
    
    // Ensure at least one character from each category
    password += uppercase[Math.floor(Math.random() * uppercase.length)]
    password += lowercase[Math.floor(Math.random() * lowercase.length)]
    password += numbers[Math.floor(Math.random() * numbers.length)]
    password += symbols[Math.floor(Math.random() * symbols.length)]
    
    // Fill the rest randomly
    for (let i = 4; i < length; i++) {
      password += allChars[Math.floor(Math.random() * allChars.length)]
    }
    
    // Shuffle the password
    password = password.split('').sort(() => Math.random() - 0.5).join('')
    
    setFormData(prev => ({ ...prev, tempPassword: password }))
    setTouched(prev => ({ ...prev, tempPassword: true }))
    setIsGeneratingPassword(false)
  }, [])

  /**
   * Handles input field changes with validation
   */
  const handleInputChange = useCallback((field: keyof User, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    setTouched(prev => ({ ...prev, [field]: true }))
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }, [errors])

  /**
   * Handles form submission with validation
   */
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault()
    
    const formErrors = validateForm()
    setErrors(formErrors)
    
    // Mark all fields as touched
    setTouched({
      firstName: true,
      lastName: true,
      email: true,
      role: true,
      tempPassword: true,
    })
    
    if (Object.keys(formErrors).length === 0) {
      onAddUser(formData)
      
      // Reset form after successful submission
      setFormData({
        firstName: "",
        lastName: "",
        email: "",
        role: "",
        tempPassword: "",
      })
      setTouched({
        firstName: false,
        lastName: false,
        email: false,
        role: false,
        tempPassword: false,
      })
      setErrors({})
    }
  }, [formData, validateForm, onAddUser])

  /**
   * Gets input field styling based on validation state
   */
  const getInputClassName = (field: keyof User) => {
    const baseClass = "transition-colors duration-200"
    if (touched[field] && errors[field]) {
      return `${baseClass} border-red-500 focus-visible:border-red-500 focus-visible:ring-red-500/20`
    }
    if (touched[field] && !errors[field] && formData[field]) {
      return `${baseClass} border-green-500 focus-visible:border-green-500 focus-visible:ring-green-500/20`
    }
    return baseClass
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Add User Form */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <UserPlusIcon className="h-5 w-5" />
            Добавить вручную
          </CardTitle>
          <p className="text-sm text-gray-600">
            Заполните форму для создания нового пользователя
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            {/* Name Fields */}
            <div className="space-y-4">
              <Label className="text-sm font-medium text-gray-700">
                Имя и Фамилия пользователя *
              </Label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-2">
                  <div className="relative">
                    <Input
                      id="firstName"
                      type="text"
                      placeholder="Имя"
                      value={formData.firstName}
                      onChange={(e) => handleInputChange("firstName", e.target.value)}
                      className={getInputClassName("firstName")}
                      aria-invalid={touched.firstName && !!errors.firstName}
                      aria-describedby={errors.firstName ? "firstName-error" : undefined}
                      disabled={isLoading}
                      autoComplete="given-name"
                    />
                    {touched.firstName && !errors.firstName && formData.firstName && (
                      <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                    )}
                    {touched.firstName && errors.firstName && (
                      <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {touched.firstName && errors.firstName && (
                    <p id="firstName-error" className="text-sm text-red-600" role="alert">
                      {errors.firstName}
                    </p>
                  )}
                </div>
                
                <div className="space-y-2">
                  <div className="relative">
                    <Input
                      id="lastName"
                      type="text"
                      placeholder="Фамилия"
                      value={formData.lastName}
                      onChange={(e) => handleInputChange("lastName", e.target.value)}
                      className={getInputClassName("lastName")}
                      aria-invalid={touched.lastName && !!errors.lastName}
                      aria-describedby={errors.lastName ? "lastName-error" : undefined}
                      disabled={isLoading}
                      autoComplete="family-name"
                    />
                    {touched.lastName && !errors.lastName && formData.lastName && (
                      <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                    )}
                    {touched.lastName && errors.lastName && (
                      <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                    )}
                  </div>
                  {touched.lastName && errors.lastName && (
                    <p id="lastName-error" className="text-sm text-red-600" role="alert">
                      {errors.lastName}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Email Field */}
            <div className="space-y-2">
              <Label htmlFor="email" className="text-sm font-medium text-gray-700">
                Email *
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  placeholder="user@example.com"
                  value={formData.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  className={getInputClassName("email")}
                  aria-invalid={touched.email && !!errors.email}
                  aria-describedby={errors.email ? "email-error" : undefined}
                  disabled={isLoading}
                  autoComplete="email"
                />
                {touched.email && !errors.email && formData.email && (
                  <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                )}
                {touched.email && errors.email && (
                  <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                )}
              </div>
              {touched.email && errors.email && (
                <p id="email-error" className="text-sm text-red-600" role="alert">
                  {errors.email}
                </p>
              )}
            </div>

            {/* Role Field */}
            <div className="space-y-2">
              <Label htmlFor="role" className="text-sm font-medium text-gray-700">
                Роль *
              </Label>
              <Select 
                value={formData.role} 
                onValueChange={(value) => handleInputChange("role", value)}
                disabled={isLoading}
              >
                <SelectTrigger 
                  id="role" 
                  className={getInputClassName("role")}
                  aria-invalid={touched.role && !!errors.role}
                  aria-describedby={errors.role ? "role-error" : undefined}
                >
                  <SelectValue placeholder="Выберите роль" />
                </SelectTrigger>
                <SelectContent>
                  {ROLE_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {touched.role && errors.role && (
                <p id="role-error" className="text-sm text-red-600" role="alert">
                  {errors.role}
                </p>
              )}
            </div>

            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="tempPassword" className="text-sm font-medium text-gray-700">
                Временный пароль *
              </Label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Input
                    id="tempPassword"
                    type={showPassword ? "text" : "password"}
                    placeholder="Временный пароль"
                    value={formData.tempPassword}
                    onChange={(e) => handleInputChange("tempPassword", e.target.value)}
                    className={`${getInputClassName("tempPassword")} pr-10`}
                    aria-invalid={touched.tempPassword && !!errors.tempPassword}
                    aria-describedby={errors.tempPassword ? "tempPassword-error" : "tempPassword-help"}
                    disabled={isLoading}
                    autoComplete="new-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700"
                    aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <EyeOffIcon className="h-4 w-4" />
                    ) : (
                      <EyeIcon className="h-4 w-4" />
                    )}
                  </button>
                </div>
                <Button
                  type="button"
                  onClick={generatePassword}
                  disabled={isLoading || isGeneratingPassword}
                  variant="outline"
                  className="px-4 shrink-0"
                  aria-label="Генерировать безопасный пароль"
                >
                  {isGeneratingPassword ? (
                    <RefreshCwIcon className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCwIcon className="h-4 w-4" />
                  )}
                  <span className="hidden sm:inline ml-2">Генерировать</span>
                </Button>
              </div>
              {!errors.tempPassword && (
                <p id="tempPassword-help" className="text-xs text-gray-500">
                  Минимум 8 символов, включая заглавные и строчные буквы, цифры
                </p>
              )}
              {touched.tempPassword && errors.tempPassword && (
                <p id="tempPassword-error" className="text-sm text-red-600" role="alert">
                  {errors.tempPassword}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              className="w-full bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <RefreshCwIcon className="h-4 w-4 animate-spin mr-2" />
                  Добавление пользователя...
                </>
              ) : (
                <>
                  <UserPlusIcon className="h-4 w-4 mr-2" />
                  Добавить пользователя
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* User List Placeholder */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-gray-900">
            Список пользователей
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64 text-gray-500">
            <div className="text-center">
              <UserPlusIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-sm">Пользователи не добавлены</p>
              <p className="text-xs text-gray-400 mt-1">
                Добавьте первого пользователя, используя форму слева
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Default export for compatibility with existing imports
export const AddUser = AddUserForm
