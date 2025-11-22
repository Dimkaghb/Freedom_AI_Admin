"use client"

import type React from "react"
import { useState, useCallback, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckIcon, XIcon, PlusIcon, AlertCircleIcon, RefreshCwIcon, Building2, ChevronDown } from "lucide-react"
import { createCompany } from "@/services/company.api"
import { listHoldings } from "@/services/holding.api"

// Types and interfaces for better type safety
interface Company {
  name: string
  holdingId: string
  adminId?: string
  description?: string
}

interface FormErrors {
  name?: string
  holdingId?: string
}

interface AddCompanyFormProps {
  onAddCompany?: (company: Company) => void
  isLoading?: boolean
  onClose?: () => void
}

/**
 * AddCompanyForm component for creating new companies with comprehensive validation and accessibility
 * @param onAddCompany - Callback function to handle company creation
 * @param isLoading - Loading state for form submission
 * @param onClose - Callback to close the modal
 */
export function AddCompanyForm({ onAddCompany, isLoading: externalLoading = false, onClose }: AddCompanyFormProps) {
  // Form state management
  const [formData, setFormData] = useState<Company>({
    name: "",
    holdingId: "",
    adminId: "",
    description: "",
  })

  // Form validation and UI state
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<keyof Company, boolean>>({
    name: false,
    holdingId: false,
    adminId: false,
    description: false,
  })

  // API state management
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Holdings list state
  const [holdings, setHoldings] = useState<Array<{ id: string; name: string }>>([])
  const [loadingHoldings, setLoadingHoldings] = useState(false)

  // Autocomplete state for holdings
  const [holdingSearchQuery, setHoldingSearchQuery] = useState("")
  const [selectedHoldingName, setSelectedHoldingName] = useState("")
  const [showHoldingDropdown, setShowHoldingDropdown] = useState(false)
  const holdingInputRef = useRef<HTMLInputElement>(null)
  const holdingDropdownRef = useRef<HTMLDivElement>(null)

  // Autocomplete state for admin
  const [adminSearchQuery, setAdminSearchQuery] = useState("")
  const [selectedAdminName, setSelectedAdminName] = useState("")
  const [showAdminDropdown, setShowAdminDropdown] = useState(false)
  const adminInputRef = useRef<HTMLInputElement>(null)
  const adminDropdownRef = useRef<HTMLDivElement>(null)

  // Admins list (to be populated from API)
  const admins: Array<{ id: string; name: string; email?: string }> = []

  // Load holdings on mount
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

    fetchHoldings()
  }, [])

  // Filter holdings based on search query
  const filteredHoldings = holdings.filter(holding =>
    holding.name.toLowerCase().includes(holdingSearchQuery.toLowerCase())
  )

  // Filter admins based on search query
  const filteredAdmins = admins.filter(admin =>
    admin.name.toLowerCase().includes(adminSearchQuery.toLowerCase())
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
        adminDropdownRef.current &&
        !adminDropdownRef.current.contains(event.target as Node) &&
        adminInputRef.current &&
        !adminInputRef.current.contains(event.target as Node)
      ) {
        setShowAdminDropdown(false)
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
    setFormData(prev => ({ ...prev, holdingId: holding.id }))
    setSelectedHoldingName(holding.name)
    setHoldingSearchQuery(holding.name)
    setShowHoldingDropdown(false)
    setTouched(prev => ({ ...prev, holdingId: true }))

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
      setFormData(prev => ({ ...prev, holdingId: "" }))
      setSelectedHoldingName("")
    }

    setTouched(prev => ({ ...prev, holdingId: true }))
  }, [selectedHoldingName])

  /**
   * Handle admin selection from dropdown
   */
  const handleSelectAdmin = useCallback((admin: { id: string; name: string }) => {
    setFormData(prev => ({ ...prev, adminId: admin.id }))
    setSelectedAdminName(admin.name)
    setAdminSearchQuery(admin.name)
    setShowAdminDropdown(false)
    setTouched(prev => ({ ...prev, adminId: true }))
  }, [])

  /**
   * Handle admin input change
   */
  const handleAdminInputChange = useCallback((value: string) => {
    setAdminSearchQuery(value)
    setShowAdminDropdown(true)

    // Clear selection if user modifies the input
    if (value !== selectedAdminName) {
      setFormData(prev => ({ ...prev, adminId: "" }))
      setSelectedAdminName("")
    }

    setTouched(prev => ({ ...prev, adminId: true }))
  }, [selectedAdminName])

  /**
   * Comprehensive form validation
   */
  const validateForm = useCallback((): FormErrors => {
    const newErrors: FormErrors = {}

    // Company name validation
    if (!formData.name.trim()) {
      newErrors.name = "Название компании обязательно для заполнения"
    } else if (formData.name.trim().length < 3) {
      newErrors.name = "Название должно содержать минимум 3 символа"
    }

    // Holding validation
    if (!formData.holdingId) {
      newErrors.holdingId = "Выберите холдинг"
    }

    return newErrors
  }, [formData])

  /**
   * Handles input field changes with validation
   */
  const handleInputChange = useCallback((field: keyof Company, value: string) => {
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
      adminId: true,
      description: true,
    })

    if (Object.keys(formErrors).length === 0) {
      setIsLoading(true)
      setApiError(null)
      setSuccessMessage(null)

      try {
        // Call API to create company
        const response = await createCompany({
          name: formData.name,
          holding_id: formData.holdingId,
          admin_id: formData.adminId,
          description: formData.description,
        })

        setSuccessMessage(`Компания "${response.name}" успешно создана!`)

        // Call optional callback if provided
        if (onAddCompany) {
          onAddCompany(formData)
        }

        // Reset form after successful submission
        setTimeout(() => {
          setFormData({
            name: "",
            holdingId: "",
            adminId: "",
            description: "",
          })
          setHoldingSearchQuery("")
          setSelectedHoldingName("")
          setAdminSearchQuery("")
          setSelectedAdminName("")
          setTouched({
            name: false,
            holdingId: false,
            adminId: false,
            description: false,
          })
          setErrors({})
          setSuccessMessage(null)
          if (onClose) {
            onClose()
          }
        }, 2000)
      } catch (error: any) {
        setApiError(error.message || 'Не удалось создать компанию')
      } finally {
        setIsLoading(false)
      }
    }
  }, [formData, validateForm, onAddCompany, onClose])

  /**
   * Gets input field styling based on validation state
   */
  const getInputClassName = (field: keyof Company) => {
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
    <div className="max-w-2xl mx-auto">
      {/* Add Company Form */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Создать компанию
          </CardTitle>
          <p className="text-sm text-gray-600">
            Заполните форму для создания новой компании
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
            {/* Company Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                Название компании *
              </Label>
              <div className="relative">
                <Input
                  id="name"
                  type="text"
                  placeholder="Например: TechCorp Inc"
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

            {/* Holding Field - Searchable Autocomplete */}
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

            {/* Admin Field - Searchable Autocomplete (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="adminId" className="text-sm font-medium text-gray-700">
                Администратор компании (необязательно)
              </Label>
              <div className="relative">
                <div className="relative">
                  <Input
                    ref={adminInputRef}
                    id="adminId"
                    type="text"
                    placeholder="Начните вводить имя администратора..."
                    value={adminSearchQuery}
                    onChange={(e) => handleAdminInputChange(e.target.value)}
                    onFocus={() => setShowAdminDropdown(true)}
                    className="transition-colors duration-200"
                    disabled={isLoading}
                    autoComplete="off"
                  />
                </div>

                {/* Dropdown with filtered results */}
                {showAdminDropdown && adminSearchQuery && (
                  <div
                    ref={adminDropdownRef}
                    className="absolute z-50 w-full mt-1 bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
                  >
                    {filteredAdmins.length > 0 ? (
                      <div className="py-1">
                        {filteredAdmins.map((admin) => (
                          <button
                            key={admin.id}
                            type="button"
                            onClick={() => handleSelectAdmin(admin)}
                            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 focus:bg-gray-100 focus:outline-none transition-colors"
                          >
                            <div className="font-medium text-gray-900">{admin.name}</div>
                            {admin.email && (
                              <div className="text-xs text-gray-500">{admin.email}</div>
                            )}
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="px-4 py-3 text-sm text-gray-500 text-center">
                        Администраторы не найдены
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Description Field (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                Описание (необязательно)
              </Label>
              <textarea
                id="description"
                placeholder="Краткое описание компании..."
                value={formData.description}
                onChange={(e) => handleInputChange("description", e.target.value)}
                className={`flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${getInputClassName("description")}`}
                disabled={isLoading}
                rows={3}
              />
            </div>

            {/* Info note */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-xs text-blue-900">
                <strong>Примечание:</strong> После создания компании вы сможете добавить отделы и настроить дополнительные параметры.
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
                    Создать компанию
                  </>
                )}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

// Default export for compatibility with existing imports
export const AddCompany = AddCompanyForm
