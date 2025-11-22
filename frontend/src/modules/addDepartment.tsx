"use client"

import type React from "react"
import { useState, useCallback, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckIcon, XIcon, PlusIcon, AlertCircleIcon, RefreshCwIcon, UserPlusIcon, Layers, ChevronDown } from "lucide-react"
import { createDepartment } from "@/services/department.api"
import { listHoldings } from "@/services/holding.api"
import { listCompanies } from "@/services/company.api"
import { listUsers, type UserResponse } from "@/services/user.api"
import { useAuth } from "@/shared/stores/authstore"

// Types and interfaces for better type safety
interface Department {
  name: string
  holdingId: string
  companyId: string
  directorId: string
  description?: string
}

interface FormErrors {
  name?: string
  holdingId?: string
  companyId?: string
  directorId?: string
}

interface AddDepartmentFormProps {
  onAddDepartment?: (department: Department) => void
  isLoading?: boolean
  onClose?: () => void
}

/**
 * AddDepartmentForm component for creating new departments with comprehensive validation and accessibility
 * @param onAddDepartment - Callback function to handle department creation
 * @param isLoading - Loading state for form submission
 * @param onClose - Callback to close the modal
 */
export function AddDepartmentForm({ onAddDepartment, isLoading: externalLoading = false, onClose }: AddDepartmentFormProps) {
  // Get current user to check role
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin' || user?.role === 'company_admin';
  const isSuperAdmin = user?.role === 'superadmin' || user?.role === 'holding_admin';

  // Form state management
  const [formData, setFormData] = useState<Department>({
    name: "",
    holdingId: "",
    companyId: "",
    directorId: "",
    description: "",
  })

  // Users list state (to be populated from API in the future)
  const [addedUsers, setAddedUsers] = useState<Array<{ id: string; name: string; email: string }>>([])

  // Form validation and UI state
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<keyof Department, boolean>>({
    name: false,
    holdingId: false,
    companyId: false,
    directorId: false,
    description: false,
  })

  // API state management
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Holdings and Companies state
  const [holdings, setHoldings] = useState<Array<{ id: string; name: string }>>([])
  const [companies, setCompanies] = useState<Array<{ id: string; name: string }>>([])
  const [loadingHoldings, setLoadingHoldings] = useState(false)
  const [loadingCompanies, setLoadingCompanies] = useState(false)

  // Users list state
  const [users, setUsers] = useState<UserResponse[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)

  // Map users to directors format for display
  const directors = users.map(user => ({
    id: user.id,
    name: `${user.firstName || ''} ${user.lastName || ''}`.trim() || user.email,
    email: user.email
  }))

  // Autocomplete state for holding
  const [holdingSearchQuery, setHoldingSearchQuery] = useState("")
  const [selectedHoldingName, setSelectedHoldingName] = useState("")
  const [showHoldingDropdown, setShowHoldingDropdown] = useState(false)
  const holdingInputRef = useRef<HTMLInputElement>(null)
  const holdingDropdownRef = useRef<HTMLDivElement>(null)

  // Autocomplete state for company
  const [companySearchQuery, setCompanySearchQuery] = useState("")
  const [selectedCompanyName, setSelectedCompanyName] = useState("")
  const [showCompanyDropdown, setShowCompanyDropdown] = useState(false)
  const companyInputRef = useRef<HTMLInputElement>(null)
  const companyDropdownRef = useRef<HTMLDivElement>(null)

  // Autocomplete state for director
  const [directorSearchQuery, setDirectorSearchQuery] = useState("")
  const [selectedDirectorName, setSelectedDirectorName] = useState("")
  const [showDirectorDropdown, setShowDirectorDropdown] = useState(false)
  const directorInputRef = useRef<HTMLInputElement>(null)
  const directorDropdownRef = useRef<HTMLDivElement>(null)

  // Load holdings and users on mount
  useEffect(() => {
    const fetchHoldings = async () => {
      setLoadingHoldings(true)
      try {
        const holdingsData = await listHoldings()
        setHoldings(holdingsData.map(h => ({ id: h.id, name: h.name })))
      } catch (error) {
        console.error('Failed to load holdings:', error)
      } finally {
        setLoadingHoldings(false)
      }
    }

    const fetchUsers = async () => {
      setLoadingUsers(true)
      try {
        const usersData = await listUsers('active')
        setUsers(usersData)
      } catch (error) {
        console.error('Failed to load users:', error)
      } finally {
        setLoadingUsers(false)
      }
    }

    fetchHoldings()
    fetchUsers()
  }, [])

  // Load companies when holding is selected
  useEffect(() => {
    const fetchCompanies = async () => {
      if (!formData.holdingId) {
        setCompanies([])
        return
      }

      setLoadingCompanies(true)
      try {
        const companiesData = await listCompanies(formData.holdingId)
        setCompanies(companiesData.map(c => ({ id: c.id, name: c.name })))
      } catch (error) {
        console.error('Failed to load companies:', error)
        setCompanies([])
      } finally {
        setLoadingCompanies(false)
      }
    }

    fetchCompanies()
  }, [formData.holdingId])

  // Filter holdings based on search query
  const filteredHoldings = holdings.filter(holding =>
    holding.name.toLowerCase().includes(holdingSearchQuery.toLowerCase())
  )

  // Filter companies based on search query
  const filteredCompanies = companies.filter(company =>
    company.name.toLowerCase().includes(companySearchQuery.toLowerCase())
  )

  // Filter directors based on search query (search by name or email)
  const filteredDirectors = directors.filter(director =>
    director.name.toLowerCase().includes(directorSearchQuery.toLowerCase()) ||
    director.email?.toLowerCase().includes(directorSearchQuery.toLowerCase())
  )

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        holdingDropdownRef.current &&
        !holdingDropdownRef.current.contains(event.target as Node) &&
        holdingInputRef.current &&
        !holdingInputRef.current.contains(event.target as Node)
      ) {
        setShowHoldingDropdown(false)
      }
      if (
        companyDropdownRef.current &&
        !companyDropdownRef.current.contains(event.target as Node) &&
        companyInputRef.current &&
        !companyInputRef.current.contains(event.target as Node)
      ) {
        setShowCompanyDropdown(false)
      }
      if (
        directorDropdownRef.current &&
        !directorDropdownRef.current.contains(event.target as Node) &&
        directorInputRef.current &&
        !directorInputRef.current.contains(event.target as Node)
      ) {
        setShowDirectorDropdown(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [])

  /**
   * Handle holding selection from dropdown
   */
  const handleSelectHolding = useCallback((holding: { id: string; name: string }) => {
    setFormData(prev => ({ ...prev, holdingId: holding.id, companyId: "", directorId: "" }))
    setSelectedHoldingName(holding.name)
    setHoldingSearchQuery(holding.name)
    setShowHoldingDropdown(false)
    setTouched(prev => ({ ...prev, holdingId: true }))

    // Reset company and director when holding changes
    setCompanySearchQuery("")
    setSelectedCompanyName("")
    setDirectorSearchQuery("")
    setSelectedDirectorName("")

    if (errors.holdingId) {
      setErrors(prev => ({ ...prev, holdingId: undefined }))
    }
  }, [errors.holdingId])

  /**
   * Handle holding input change
   */
  const handleHoldingInputChange = useCallback((value: string) => {
    setHoldingSearchQuery(value)
    setShowHoldingDropdown(true)

    // Clear selection if user modifies the input
    if (value !== selectedHoldingName) {
      setFormData(prev => ({ ...prev, holdingId: "", companyId: "", directorId: "" }))
      setSelectedHoldingName("")
      setCompanySearchQuery("")
      setSelectedCompanyName("")
      setDirectorSearchQuery("")
      setSelectedDirectorName("")
    }

    setTouched(prev => ({ ...prev, holdingId: true }))
  }, [selectedHoldingName])

  /**
   * Handle company selection from dropdown
   */
  const handleSelectCompany = useCallback((company: { id: string; name: string }) => {
    setFormData(prev => ({ ...prev, companyId: company.id }))
    setSelectedCompanyName(company.name)
    setCompanySearchQuery(company.name)
    setShowCompanyDropdown(false)
    setTouched(prev => ({ ...prev, companyId: true }))

    if (errors.companyId) {
      setErrors(prev => ({ ...prev, companyId: undefined }))
    }
  }, [errors.companyId])

  /**
   * Handle company input change
   */
  const handleCompanyInputChange = useCallback((value: string) => {
    setCompanySearchQuery(value)
    setShowCompanyDropdown(true)

    // Clear selection if user modifies the input
    if (value !== selectedCompanyName) {
      setFormData(prev => ({ ...prev, companyId: "" }))
      setSelectedCompanyName("")
    }

    setTouched(prev => ({ ...prev, companyId: true }))
  }, [selectedCompanyName])

  /**
   * Handle director selection from dropdown
   */
  const handleSelectDirector = useCallback((director: { id: string; name: string }) => {
    setFormData(prev => ({ ...prev, directorId: director.id }))
    setSelectedDirectorName(director.name)
    setDirectorSearchQuery(director.name)
    setShowDirectorDropdown(false)
    setTouched(prev => ({ ...prev, directorId: true }))

    if (errors.directorId) {
      setErrors(prev => ({ ...prev, directorId: undefined }))
    }
  }, [errors.directorId])

  /**
   * Handle director input change
   */
  const handleDirectorInputChange = useCallback((value: string) => {
    setDirectorSearchQuery(value)
    setShowDirectorDropdown(true)

    // Clear selection if user modifies the input
    if (value !== selectedDirectorName) {
      setFormData(prev => ({ ...prev, directorId: "" }))
      setSelectedDirectorName("")
    }

    setTouched(prev => ({ ...prev, directorId: true }))
  }, [selectedDirectorName])

  /**
   * Comprehensive form validation
   */
  const validateForm = useCallback((): FormErrors => {
    const newErrors: FormErrors = {}

    // Holding validation (only for superadmin)
    if (isSuperAdmin && !formData.holdingId) {
      newErrors.holdingId = "Выберите холдинг"
    }

    // Company validation (only for superadmin)
    if (isSuperAdmin && !formData.companyId) {
      newErrors.companyId = "Выберите компанию"
    }

    // Department name validation
    if (!formData.name.trim()) {
      newErrors.name = "Название отдела обязательно для заполнения"
    } else if (formData.name.trim().length < 3) {
      newErrors.name = "Название должно содержать минимум 3 символа"
    }

    // Director validation
    if (!formData.directorId) {
      newErrors.directorId = "Выберите руководителя отдела"
    }

    return newErrors
  }, [formData, isAdmin, isSuperAdmin])

  /**
   * Handles input field changes with validation
   */
  const handleInputChange = useCallback((field: keyof Department, value: string) => {
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
  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()

    const formErrors = validateForm()
    setErrors(formErrors)

    // Mark all fields as touched
    setTouched({
      name: true,
      holdingId: true,
      companyId: true,
      directorId: true,
      description: true,
    })

    if (Object.keys(formErrors).length === 0) {
      setIsLoading(true)
      setApiError(null)
      setSuccessMessage(null)

      try {
        // Call API to create department
        // For admins, company_id is auto-set on backend, so we don't send it
        const response = await createDepartment({
          name: formData.name,
          company_id: isAdmin ? undefined : formData.companyId,
          manager_id: formData.directorId,
          description: formData.description,
        })

        setSuccessMessage(`Отдел "${response.name}" успешно создан!`)

        // Call optional callback if provided
        if (onAddDepartment) {
          onAddDepartment(formData)
        }

        // Reset form after successful submission
        setTimeout(() => {
          setFormData({
            name: "",
            holdingId: "",
            companyId: "",
            directorId: "",
            description: "",
          })
          setAddedUsers([])
          setHoldingSearchQuery("")
          setSelectedHoldingName("")
          setCompanySearchQuery("")
          setSelectedCompanyName("")
          setDirectorSearchQuery("")
          setSelectedDirectorName("")
          setTouched({
            name: false,
            holdingId: false,
            companyId: false,
            directorId: false,
            description: false,
          })
          setErrors({})
          setSuccessMessage(null)
          if (onClose) {
            onClose()
          }
        }, 2000)
      } catch (error: any) {
        setApiError(error.message || 'Не удалось создать отдел')
      } finally {
        setIsLoading(false)
      }
    }
  }, [formData, validateForm, onAddDepartment, onClose])

  /**
   * Gets input field styling based on validation state
   */
  const getInputClassName = (field: keyof Department) => {
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
      {/* Add Department Form */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Создать отдел
          </CardTitle>
          <p className="text-sm text-gray-600">
            Заполните форму для создания нового отдела
          </p>
        </CardHeader>
        <CardContent>
          {/* Success Message */}
          {successMessage && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start gap-3">
                <CheckIcon className="h-5 w-5 text-green-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">{successMessage}</p>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {apiError && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircleIcon className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">Ошибка</p>
                  <p className="text-sm text-red-700 mt-1">{apiError}</p>
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            {/* Info message for admin users */}
            {isAdmin && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-xs text-blue-900">
                  <strong>Примечание:</strong> Отдел будет создан в вашей компании автоматически.
                </p>
              </div>
            )}

            {/* Holding Field - Searchable Autocomplete (only for superadmin) */}
            {isSuperAdmin && (
            <div className="space-y-2">
              <Label htmlFor="holdingId" className="text-sm font-medium text-gray-700">
                Холдинг *
              </Label>
              <div className="relative">
                <div className="relative">
                  <Input
                    ref={holdingInputRef}
                    id="holdingId"
                    type="text"
                    placeholder={loadingHoldings ? "Загрузка..." : "Начните вводить название холдинга..."}
                    value={holdingSearchQuery}
                    onChange={(e) => handleHoldingInputChange(e.target.value)}
                    onFocus={() => setShowHoldingDropdown(true)}
                    className={getInputClassName("holdingId")}
                    aria-invalid={touched.holdingId && !!errors.holdingId}
                    aria-describedby={errors.holdingId ? "holdingId-error" : undefined}
                    disabled={isLoading || loadingHoldings}
                    autoComplete="off"
                  />
                  {touched.holdingId && !errors.holdingId && formData.holdingId && (
                    <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                  )}
                  {touched.holdingId && errors.holdingId && (
                    <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                  )}
                </div>

                {/* Dropdown with filtered results */}
                {showHoldingDropdown && holdingSearchQuery && (
                  <div
                    ref={holdingDropdownRef}
                    className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    {filteredHoldings.length > 0 ? (
                      <div className="py-1">
                        {filteredHoldings.map((holding) => (
                          <button
                            key={holding.id}
                            type="button"
                            onClick={() => handleSelectHolding(holding)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors"
                          >
                            <div className="font-medium text-gray-900">{holding.name}</div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-4 py-3 text-sm text-gray-500 text-center">
                        {loadingHoldings ? "Загрузка холдингов..." : "Холдинги не найдены"}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {touched.holdingId && errors.holdingId && (
                <p id="holdingId-error" className="text-sm text-red-600" role="alert">
                  {errors.holdingId}
                </p>
              )}
            </div>
            )}

            {/* Company Field - Searchable Autocomplete (only for superadmin) */}
            {isSuperAdmin && (
            <div className="space-y-2">
              <Label htmlFor="companyId" className="text-sm font-medium text-gray-700">
                Компания *
              </Label>
              <div className="relative">
                <div className="relative">
                  <Input
                    ref={companyInputRef}
                    id="companyId"
                    type="text"
                    placeholder={!formData.holdingId ? "Сначала выберите холдинг" : loadingCompanies ? "Загрузка..." : "Начните вводить название компании..."}
                    value={companySearchQuery}
                    onChange={(e) => handleCompanyInputChange(e.target.value)}
                    onFocus={() => setShowCompanyDropdown(true)}
                    className={getInputClassName("companyId")}
                    aria-invalid={touched.companyId && !!errors.companyId}
                    aria-describedby={errors.companyId ? "companyId-error" : undefined}
                    disabled={isLoading || !formData.holdingId || loadingCompanies}
                    autoComplete="off"
                  />
                  {touched.companyId && !errors.companyId && formData.companyId && (
                    <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                  )}
                  {touched.companyId && errors.companyId && (
                    <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                  )}
                </div>

                {/* Dropdown with filtered results */}
                {showCompanyDropdown && companySearchQuery && formData.holdingId && (
                  <div
                    ref={companyDropdownRef}
                    className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    {filteredCompanies.length > 0 ? (
                      <div className="py-1">
                        {filteredCompanies.map((company) => (
                          <button
                            key={company.id}
                            type="button"
                            onClick={() => handleSelectCompany(company)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors"
                          >
                            <div className="font-medium text-gray-900">{company.name}</div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-4 py-3 text-sm text-gray-500 text-center">
                        {loadingCompanies ? "Загрузка компаний..." : "Компании не найдены"}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {touched.companyId && errors.companyId && (
                <p id="companyId-error" className="text-sm text-red-600" role="alert">
                  {errors.companyId}
                </p>
              )}
            </div>
            )}

            {/* Department Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                Название отдела *
              </Label>
              <div className="relative">
                <Input
                  id="name"
                  type="text"
                  placeholder="Например: IT отдел"
                  value={formData.name}
                  onChange={(e) => handleInputChange("name", e.target.value)}
                  className={getInputClassName("name")}
                  aria-invalid={touched.name && !!errors.name}
                  aria-describedby={errors.name ? "name-error" : undefined}
                  disabled={isLoading}
                />
                {touched.name && !errors.name && formData.name && (
                  <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                )}
                {touched.name && errors.name && (
                  <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                )}
              </div>
              {touched.name && errors.name && (
                <p id="name-error" className="text-sm text-red-600" role="alert">
                  {errors.name}
                </p>
              )}
            </div>

            {/* Director Field - Searchable Autocomplete */}
            <div className="space-y-2">
              <Label htmlFor="directorId" className="text-sm font-medium text-gray-700">
                Руководитель отдела *
              </Label>
              <div className="relative">
                <div className="relative">
                  <Input
                    ref={directorInputRef}
                    id="directorId"
                    type="text"
                    placeholder="Начните вводить имя или email..."
                    value={directorSearchQuery}
                    onChange={(e) => handleDirectorInputChange(e.target.value)}
                    onFocus={() => setShowDirectorDropdown(true)}
                    className={getInputClassName("directorId")}
                    aria-invalid={touched.directorId && !!errors.directorId}
                    aria-describedby={errors.directorId ? "directorId-error" : undefined}
                    disabled={isLoading || loadingUsers}
                    autoComplete="off"
                  />
                  {touched.directorId && !errors.directorId && formData.directorId && (
                    <CheckIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-green-500" />
                  )}
                  {touched.directorId && errors.directorId && (
                    <XIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-red-500" />
                  )}
                </div>

                {/* Dropdown with filtered results */}
                {showDirectorDropdown && directorSearchQuery && (
                  <div
                    ref={directorDropdownRef}
                    className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    {filteredDirectors.length > 0 ? (
                      <div className="py-1">
                        {filteredDirectors.map((director) => (
                          <button
                            key={director.id}
                            type="button"
                            onClick={() => handleSelectDirector(director)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors"
                          >
                            <div className="font-medium text-gray-900">{director.name}</div>
                            {director.email && (
                              <div className="text-xs text-gray-500">{director.email}</div>
                            )}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-4 py-3 text-sm text-gray-500 text-center">
                        {loadingUsers ? "Загрузка пользователей..." : "Пользователи не найдены"}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {touched.directorId && errors.directorId && (
                <p id="directorId-error" className="text-sm text-red-600" role="alert">
                  {errors.directorId}
                </p>
              )}
            </div>

            {/* Description Field (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                Описание (необязательно)
              </Label>
              <textarea
                id="description"
                placeholder="Краткое описание отдела..."
                value={formData.description}
                onChange={(e) => handleInputChange("description", e.target.value)}
                className={`flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${getInputClassName("description")}`}
                disabled={isLoading}
                rows={3}
              />
            </div>

            {/* User List Section */}
            <div className="space-y-2">
              <Label className="text-sm font-medium text-gray-700">
                Список пользователей
              </Label>
              <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-gray-600">
                    Добавлено: {addedUsers.length}
                  </span>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={true}
                    className="text-xs"
                  >
                    <UserPlusIcon className="h-3 w-3 mr-1" />
                    Добавить пользователя
                  </Button>
                </div>

                {addedUsers.length === 0 ? (
                  <div className="text-center py-6">
                    <p className="text-xs text-gray-400">
                      Функционал будет реализован позже
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {addedUsers.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center justify-between p-2 bg-white border border-gray-200 rounded"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-900">{user.name}</p>
                          <p className="text-xs text-gray-500">{user.email}</p>
                        </div>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => setAddedUsers(users => users.filter(u => u.id !== user.id))}
                          className="h-7 w-7 p-0"
                        >
                          <XIcon className="h-4 w-4 text-gray-500" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Info note */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-900">
                <strong>Примечание:</strong> После создания отдела вы сможете добавить пользователей и настроить дополнительные параметры.
              </p>
            </div>

            {/* Submit Button */}
            <div className="flex gap-3">
              {onClose && (
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={onClose}
                  disabled={isLoading}
                >
                  Отмена
                </Button>
              )}
              <Button
                type="submit"
                className="flex-1 bg-gray-900 hover:bg-gray-800 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <RefreshCwIcon className="h-4 w-4 animate-spin mr-2" />
                    Создание...
                  </>
                ) : (
                  <>
                    <PlusIcon className="h-4 w-4 mr-2" />
                    Создать отдел
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Added Users List */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="text-xl font-semibold text-gray-900">
            Добавленные пользователи
          </CardTitle>
        </CardHeader>
        <CardContent>
          {addedUsers.length === 0 ? (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <div className="text-center">
                <UserPlusIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                <p className="text-sm">Пользователи не добавлены</p>
                <p className="text-xs text-gray-400 mt-1">
                  Функционал добавления пользователей будет реализован позже
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {addedUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
                >
                  <div>
                    <p className="text-sm font-medium text-gray-900">{user.name}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => setAddedUsers(users => users.filter(u => u.id !== user.id))}
                  >
                    <XIcon className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// Default export for compatibility with existing imports
export const AddDepartment = AddDepartmentForm
