"use client"

import type React from "react"
import { useState, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { CheckIcon, XIcon, PlusIcon, AlertCircleIcon, RefreshCwIcon, Building } from "lucide-react"
import { createHolding } from "@/services/holding.api"

// Types and interfaces for better type safety
interface Holding {
  name: string
  description?: string
}

interface FormErrors {
  name?: string
}

interface AddHoldingFormProps {
  onAddHolding?: (holding: Holding) => void
  isLoading?: boolean
  onClose?: () => void
}

/**
 * AddHoldingForm component for creating new holdings with comprehensive validation and accessibility
 * @param onAddHolding - Callback function to handle holding creation
 * @param isLoading - Loading state for form submission
 * @param onClose - Callback to close the modal
 */
export function AddHoldingForm({ onAddHolding, isLoading: externalLoading = false, onClose }: AddHoldingFormProps) {
  // Form state management
  const [formData, setFormData] = useState<Holding>({
    name: "",
    description: "",
  })

  // Form validation and UI state
  const [errors, setErrors] = useState<FormErrors>({})
  const [touched, setTouched] = useState<Record<keyof Holding, boolean>>({
    name: false,
    description: false,
  })

  // API state management
  const [isLoading, setIsLoading] = useState(false)
  const [apiError, setApiError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  /**
   * Comprehensive form validation
   */
  const validateForm = useCallback((): FormErrors => {
    const newErrors: FormErrors = {}

    // Holding name validation
    if (!formData.name.trim()) {
      newErrors.name = "Название холдинга обязательно для заполнения"
    } else if (formData.name.trim().length < 3) {
      newErrors.name = "Название должно содержать минимум 3 символа"
    }

    return newErrors
  }, [formData])

  /**
   * Handles input field changes with validation
   */
  const handleInputChange = useCallback((field: keyof Holding, value: string) => {
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
      description: true,
    })

    if (Object.keys(formErrors).length === 0) {
      setIsLoading(true)
      setApiError(null)
      setSuccessMessage(null)

      try {
        // Call API to create holding
        const response = await createHolding({
          name: formData.name,
          description: formData.description,
        })

        setSuccessMessage(`Холдинг "${response.name}" успешно создан!`)

        // Call optional callback if provided
        if (onAddHolding) {
          onAddHolding(formData)
        }

        // Reset form after successful submission
        setTimeout(() => {
          setFormData({
            name: "",
            description: "",
          })
          setTouched({
            name: false,
            description: false,
          })
          setErrors({})
          setSuccessMessage(null)
          if (onClose) {
            onClose()
          }
        }, 2000)
      } catch (error: any) {
        setApiError(error.message || 'Не удалось создать холдинг')
      } finally {
        setIsLoading(false)
      }
    }
  }, [formData, validateForm, onAddHolding, onClose])

  /**
   * Gets input field styling based on validation state
   */
  const getInputClassName = (field: keyof Holding) => {
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
      {/* Add Holding Form */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader className="space-y-1">
          <CardTitle className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Building className="h-5 w-5" />
            Создать холдинг
          </CardTitle>
          <p className="text-sm text-gray-600">
            Заполните форму для создания нового холдинга
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
            {/* Holding Name Field */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                Название холдинга *
              </Label>
              <div className="relative">
                <Input
                  id="name"
                  type="text"
                  placeholder="Например: TechCorp Holdings"
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

            {/* Description Field (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-sm font-medium text-gray-700">
                Описание (необязательно)
              </Label>
              <textarea
                id="description"
                placeholder="Краткое описание холдинга..."
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
                <strong>Примечание:</strong> После создания холдинга вы сможете добавить компании и настроить дополнительные параметры.
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
                    Создать холдинг
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
export const AddHolding = AddHoldingForm
