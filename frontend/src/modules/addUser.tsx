"use client"

import type React from "react"
import { useState, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckIcon, XIcon, UserPlusIcon, AlertCircleIcon, CopyIcon, RefreshCwIcon } from "lucide-react"
import { createUser } from "@/services/user.api"
import { listCompanies, type CompanyResponse } from "@/services/company.api"
import { listDepartments, type DepartmentResponse } from "@/services/department.api"
import { listHoldings, type HoldingResponse } from "@/services/holding.api"
import { useAuth } from "@/shared/stores/authstore"

// Types and interfaces for better type safety
interface UserFormData {
  firstName: string
  lastName: string
  email: string
  role: string
  holding_id?: string
  company_id?: string
  department_id?: string
}

interface FormErrors {
  firstName?: string
  lastName?: string
  email?: string
  role?: string
  holding_id?: string
  company_id?: string
  department_id?: string
}

interface AddUserFormProps {
  onAddUser?: (user: UserFormData) => void
  onUserCreated?: () => void
  isLoading?: boolean
}

// Role options with proper typing
const ROLE_OPTIONS = [
  { value: "admin", label: "Администратор" },
  { value: "director", label: "Директор" },
  { value: "user", label: "Пользователь" },
] as const

/**
 * AddUserForm component for creating new users with comprehensive validation and accessibility
 * @param onAddUser - Callback function to handle user creation
 * @param onUserCreated - Callback to refresh parent component after user creation
 * @param isLoading - Loading state for form submission
 */
export function AddUserForm({ onAddUser, onUserCreated, isLoading: externalLoading = false }: AddUserFormProps) {
  // Get current user from auth context
  const { user: currentUser } = useAuth()

  // Form state management
  const [formData, setFormData] = useState<UserFormData>({
    firstName: "",
    lastName: "",
    email: "",
    role: "",
    holding_id: "",
    company_id: "",
    department_id: "",
  })

  // Organization data
  const [holdings, setHoldings] = useState<HoldingResponse[]>([])
  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [loadingOrganizations, setLoadingOrganizations] = useState(true)

  // Form validation and UI state
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<keyof UserFormData, boolean>>({
    firstName: false,
    lastName: false,
    email: false,
    role: false,
    holding_id: false,
    company_id: false,
    department_id: false,
  })

  // API state management
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [createdUserPassword, setCreatedUserPassword] = useState<string | null>(null)

  /**
   * Load organizations on component mount
   */
  useEffect(() => {
    const loadOrganizations = async () => {
      try {
        const [holdingsData, companiesData, departmentsData] = await Promise.all([
          listHoldings(),
          listCompanies(),
          listDepartments(),
        ])
        setHoldings(holdingsData)
        setCompanies(companiesData)
        setDepartments(departmentsData)
      } catch (error) {
        console.error('Failed to load organizations:', error)
      } finally {
        setLoadingOrganizations(false)
      }
    }
    loadOrganizations()
  }, [])

  /**
   * Validates email format using regex
   */
  const isValidEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return emailRegex.test(email)
  }

  /**
   * Get filtered companies based on selected holding
   */
  const getFilteredCompanies = useCallback(() => {
    if (!formData.holding_id) return companies
    return companies.filter(company => company.holding_id === formData.holding_id)
  }, [formData.holding_id, companies])

  /**
   * Get filtered departments based on selected company
   */
  const getFilteredDepartments = useCallback(() => {
    if (!formData.company_id) return []
    return departments.filter(dept => dept.company_id === formData.company_id)
  }, [formData.company_id, departments])

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

    // Organization validation based on current user's role and new user's role
    if (currentUser?.role === 'superadmin') {
      // Superadmin must select organization for new user
      if (formData.role === 'admin') {
        if (!formData.holding_id) {
          newErrors.holding_id = "Выберите холдинг"
        }
        if (!formData.company_id) {
          newErrors.company_id = "Выберите компанию"
        }
      } else if (formData.role === 'director' || formData.role === 'user') {
        if (!formData.holding_id) {
          newErrors.holding_id = "Выберите холдинг"
        }
        if (!formData.company_id) {
          newErrors.company_id = "Выберите компанию"
        }
        if (!formData.department_id) {
          newErrors.department_id = "Выберите отдел"
        }
      }
    } else if (currentUser?.role === 'admin') {
      // Admin only selects department (holding and company auto-assigned)
      if (formData.role === 'director' || formData.role === 'user') {
        if (!formData.department_id) {
          newErrors.department_id = "Выберите отдел"
        }
      }
    }

    return newErrors
  }, [formData, currentUser])

  /**
   * Handles input field changes with validation
   */
  const handleInputChange = useCallback((field: keyof UserFormData, value: string) => {
    setFormData(prev => {
      const newData = { ...prev, [field]: value }

      // Clear downstream fields when upstream ones change
      if (field === 'role') {
        newData.holding_id = ''
        newData.company_id = ''
        newData.department_id = ''
      }

      if (field === 'holding_id') {
        newData.company_id = ''
        newData.department_id = ''
      }

      if (field === 'company_id') {
        newData.department_id = ''
      }

      return newData
    })
    setTouched(prev => ({ ...prev, [field]: true }))

    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }))
    }
  }, [errors])

  /**
   * Handles form submission with validation
   */
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    const formErrors = validateForm()
    setErrors(formErrors)

    // Mark all fields as touched
    setTouched({
      firstName: true,
      lastName: true,
      email: true,
      role: true,
      holding_id: true,
      company_id: true,
      department_id: true,
    })

    if (Object.keys(formErrors).length === 0) {
      setIsLoading(true)
      setApiError(null)
      setSuccessMessage(null)

      try {
        // Determine organization IDs based on current user's role
        let holding_id = formData.holding_id || undefined
        let company_id = formData.company_id || undefined
        let department_id = formData.department_id || undefined

        // If current user is admin, auto-assign their holding and company
        if (currentUser?.role === 'admin') {
          holding_id = currentUser.holding_id
          company_id = currentUser.company_id
        }

        // Call API to create user (backend generates password)
        const response = await createUser({
          email: formData.email,
          role: formData.role as 'admin' | 'user' | 'director',
          firstName: formData.firstName,
          lastName: formData.lastName,
          holding_id: holding_id,
          company_id: company_id,
          department_id: department_id,
        })

        // Store the temporary password from backend
        setCreatedUserPassword(response.temporary_password)
        setSuccessMessage(`Пользователь ${response.email} успешно создан!`)

        // Call optional callbacks if provided
        if (onAddUser) {
          onAddUser(formData)
        }
        if (onUserCreated) {
          onUserCreated()
        }

        // Reset form after successful submission
        setFormData({
          firstName: "",
          lastName: "",
          email: "",
          role: "",
          holding_id: "",
          company_id: "",
          department_id: "",
        })
        setTouched({
          firstName: false,
          lastName: false,
          email: false,
          role: false,
          holding_id: false,
          company_id: false,
          department_id: false,
        })
        setErrors({})
      } catch (error: any) {
        setApiError(error.message || 'Не удалось создать пользователя')
      } finally {
        setIsLoading(false)
      }
    }
  }, [formData, validateForm, onAddUser, onUserCreated])

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
    <div>
      {/* Success Message */}
      {successMessage && createdUserPassword && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-start gap-3">
            <CheckIcon className="h-5 w-5 text-gray-900 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{successMessage}</p>
              <div className="mt-3 p-3 bg-white border border-gray-200 rounded">
                <p className="text-xs font-medium text-gray-700 mb-1">Временный пароль:</p>
                <div className="flex items-center gap-2">
                  <code className="flex-1 text-sm font-mono text-gray-900 bg-gray-50 px-2 py-1 rounded">
                    {createdUserPassword}
                  </code>
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard.writeText(createdUserPassword)
                    }}
                    className="shrink-0"
                  >
                    <CopyIcon className="h-3 w-3" />
                  </Button>
                </div>
                <p className="text-xs text-gray-600 mt-2">
                  Сохраните этот пароль в безопасном месте. Он больше не будет отображаться.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {apiError && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-300 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircleIcon className="h-5 w-5 text-gray-900 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Ошибка</p>
              <p className="text-sm text-gray-700 mt-1">{apiError}</p>
            </div>
          </div>
        </div>
      )}

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

        {/* Organization Fields - Different based on current user's role */}

        {/* SUPERADMIN creating users: show holding, company, department */}
        {currentUser?.role === 'superadmin' && formData.role && (
          <>
            {/* Holding Field */}
            <div className="space-y-2">
              <Label htmlFor="holding_id" className="text-sm font-medium text-gray-700">
                Холдинг *
              </Label>
              <Select
                value={formData.holding_id}
                onValueChange={(value) => handleInputChange("holding_id", value)}
                disabled={isLoading || loadingOrganizations}
              >
                <SelectTrigger
                  id="holding_id"
                  className={getInputClassName("holding_id")}
                  aria-invalid={touched.holding_id && !!errors.holding_id}
                  aria-describedby={errors.holding_id ? "holding_id-error" : undefined}
                >
                  <SelectValue placeholder={loadingOrganizations ? "Загрузка..." : "Выберите холдинг"} />
                </SelectTrigger>
                <SelectContent>
                  {holdings.map((holding) => (
                    <SelectItem key={holding.id} value={holding.id}>
                      {holding.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {touched.holding_id && errors.holding_id && (
                <p id="holding_id-error" className="text-sm text-red-600" role="alert">
                  {errors.holding_id}
                </p>
              )}
            </div>

            {/* Company Field */}
            {formData.holding_id && (
              <div className="space-y-2">
                <Label htmlFor="company_id" className="text-sm font-medium text-gray-700">
                  Компания *
                </Label>
                <Select
                  value={formData.company_id}
                  onValueChange={(value) => handleInputChange("company_id", value)}
                  disabled={isLoading || loadingOrganizations}
                >
                  <SelectTrigger
                    id="company_id"
                    className={getInputClassName("company_id")}
                    aria-invalid={touched.company_id && !!errors.company_id}
                    aria-describedby={errors.company_id ? "company_id-error" : undefined}
                  >
                    <SelectValue placeholder="Выберите компанию" />
                  </SelectTrigger>
                  <SelectContent>
                    {getFilteredCompanies().map((company) => (
                      <SelectItem key={company.id} value={company.id}>
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {touched.company_id && errors.company_id && (
                  <p id="company_id-error" className="text-sm text-red-600" role="alert">
                    {errors.company_id}
                  </p>
                )}
              </div>
            )}

            {/* Department Field - for director and user roles */}
            {(formData.role === 'director' || formData.role === 'user') && formData.company_id && (
              <div className="space-y-2">
                <Label htmlFor="department_id" className="text-sm font-medium text-gray-700">
                  Отдел *
                </Label>
                <Select
                  value={formData.department_id}
                  onValueChange={(value) => handleInputChange("department_id", value)}
                  disabled={isLoading || loadingOrganizations}
                >
                  <SelectTrigger
                    id="department_id"
                    className={getInputClassName("department_id")}
                    aria-invalid={touched.department_id && !!errors.department_id}
                    aria-describedby={errors.department_id ? "department_id-error" : undefined}
                  >
                    <SelectValue placeholder="Выберите отдел" />
                  </SelectTrigger>
                  <SelectContent>
                    {getFilteredDepartments().map((department) => (
                      <SelectItem key={department.id} value={department.id}>
                        {department.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {touched.department_id && errors.department_id && (
                  <p id="department_id-error" className="text-sm text-red-600" role="alert">
                    {errors.department_id}
                  </p>
                )}
              </div>
            )}
          </>
        )}

        {/* ADMIN creating users: only show department (holding and company auto-assigned) */}
        {currentUser?.role === 'admin' && formData.role && (formData.role === 'director' || formData.role === 'user') && (
          <div className="space-y-2">
            <Label htmlFor="department_id" className="text-sm font-medium text-gray-700">
              Отдел *
            </Label>
            <Select
              value={formData.department_id}
              onValueChange={(value) => handleInputChange("department_id", value)}
              disabled={isLoading || loadingOrganizations}
            >
              <SelectTrigger
                id="department_id"
                className={getInputClassName("department_id")}
                aria-invalid={touched.department_id && !!errors.department_id}
                aria-describedby={errors.department_id ? "department_id-error" : undefined}
              >
                <SelectValue placeholder={loadingOrganizations ? "Загрузка..." : "Выберите отдел"} />
              </SelectTrigger>
              <SelectContent>
                {departments.filter(dept => dept.company_id === currentUser.company_id).map((department) => (
                  <SelectItem key={department.id} value={department.id}>
                    {department.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {touched.department_id && errors.department_id && (
              <p id="department_id-error" className="text-sm text-red-600" role="alert">
                {errors.department_id}
              </p>
            )}
          </div>
        )}

        {/* Info about password generation */}
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-xs text-gray-700">
            <strong>Примечание:</strong> Безопасный временный пароль будет автоматически сгенерирован системой и отображен после создания пользователя.
          </p>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          className="w-full"
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
    </div>
  )
}

// Default export for compatibility with existing imports
export const AddUser = AddUserForm
