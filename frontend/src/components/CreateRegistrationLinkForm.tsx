"use client"

import type React from "react"
import { useState, useEffect, useCallback } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { CheckIcon, CopyIcon, RefreshCwIcon, Link2Icon, MailIcon, AlertCircleIcon } from "lucide-react"
import { createRegistrationLink, sendRegistrationInvite } from "@/services/user.api"
import { listCompanies } from "@/services/company.api"
import { listDepartments } from "@/services/department.api"
import type { CreateRegistrationLinkRequest, RegistrationLinkResponse } from "@/services/user.api"
import type { CompanyResponse } from "@/services/company.api"
import type { DepartmentResponse } from "@/services/department.api"

interface CreateRegistrationLinkFormProps {
  onSuccess?: () => void
  onCancel?: () => void
}

/**
 * CreateRegistrationLinkForm component for generating user registration links
 */
export function CreateRegistrationLinkForm({ onSuccess, onCancel }: CreateRegistrationLinkFormProps) {
  // Data state
  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [allDepartments, setAllDepartments] = useState<DepartmentResponse[]>([])

  // Form state
  const [selectedCompany, setSelectedCompany] = useState<string>("")
  const [selectedDepartment, setSelectedDepartment] = useState<string>("")
  const [selectedRole, setSelectedRole] = useState<string>("")
  const [sendEmail, setSendEmail] = useState(false)
  const [recipientEmail, setRecipientEmail] = useState("")

  // UI state
  const [isLoading, setIsLoading] = useState(false)
  const [loadingData, setLoadingData] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [generatedLink, setGeneratedLink] = useState<RegistrationLinkResponse | null>(null)
  const [copied, setCopied] = useState(false)
  const [emailSent, setEmailSent] = useState(false)

  /**
   * Load companies and departments on mount
   */
  useEffect(() => {
    const loadData = async () => {
      setLoadingData(true)
      try {
        const [companiesData, departmentsData] = await Promise.all([
          listCompanies(),
          listDepartments(),
        ])
        setCompanies(companiesData)
        setAllDepartments(departmentsData)
      } catch (err: any) {
        setError(err.message || 'Не удалось загрузить данные')
      } finally {
        setLoadingData(false)
      }
    }
    loadData()
  }, [])

  /**
   * Filter departments when company changes
   */
  useEffect(() => {
    if (selectedCompany) {
      const filtered = allDepartments.filter(dept => dept.company_id === selectedCompany)
      setDepartments(filtered)
      // Reset department and role when company changes
      setSelectedDepartment("")
      setSelectedRole("")
    } else {
      setDepartments([])
      setSelectedDepartment("")
      setSelectedRole("")
    }
  }, [selectedCompany, allDepartments])

  /**
   * Determine available roles based on department selection
   */
  const availableRoles = useCallback(() => {
    if (!selectedDepartment) {
      // Company-level: only admin role
      return [{ value: "admin", label: "Администратор компании" }]
    } else {
      // Department-level: director or user
      return [
        { value: "director", label: "Директор отдела" },
        { value: "user", label: "Пользователь" },
      ]
    }
  }, [selectedDepartment])

  /**
   * Reset role when available roles change
   */
  useEffect(() => {
    setSelectedRole("")
  }, [selectedDepartment])

  /**
   * Handle form submission
   */
  const handleGenerateLink = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setEmailSent(false)

    // Validation
    if (!selectedCompany) {
      setError("Выберите компанию")
      return
    }
    if (!selectedRole) {
      setError("Выберите роль")
      return
    }
    if (sendEmail && !recipientEmail) {
      setError("Введите email получателя")
      return
    }

    setIsLoading(true)

    try {
      // Create registration link
      const linkData: CreateRegistrationLinkRequest = {
        company_id: selectedCompany,
        role: selectedRole as 'admin' | 'director' | 'user',
      }

      if (selectedDepartment) {
        linkData.department_id = selectedDepartment
      }

      const response = await createRegistrationLink(linkData)
      setGeneratedLink(response)

      // Send email if requested
      if (sendEmail && recipientEmail) {
        try {
          const company = companies.find(c => c.id === selectedCompany)
          const department = departments.find(d => d.id === selectedDepartment)

          await sendRegistrationInvite(
            recipientEmail,
            response.registration_url,
            company?.name || "Unknown Company",
            response.role,
            department?.name
          )
          setEmailSent(true)
        } catch (emailErr: any) {
          console.error('Email sending failed:', emailErr)
          // Don't fail the entire operation, just show a warning
          setError(`Ссылка создана, но не удалось отправить email: ${emailErr.message || 'Проверьте настройки SMTP'}`)
        }
      }

      // Call success callback
      if (onSuccess) {
        onSuccess()
      }
    } catch (err: any) {
      setError(err.message || 'Не удалось создать ссылку регистрации')
    } finally {
      setIsLoading(false)
    }
  }, [selectedCompany, selectedDepartment, selectedRole, sendEmail, recipientEmail, companies, departments, onSuccess])

  /**
   * Copy link to clipboard
   */
  const handleCopyLink = useCallback(() => {
    if (generatedLink) {
      navigator.clipboard.writeText(generatedLink.registration_url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }, [generatedLink])

  /**
   * Get expiry information
   */
  const getExpiryInfo = useCallback(() => {
    if (!generatedLink) return ""

    const expiryDate = new Date(generatedLink.expires_at)
    const now = new Date()
    const hoursLeft = Math.round((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60))

    return `Истекает через ${hoursLeft} часов`
  }, [generatedLink])

  if (loadingData) {
    return (
      <div className="flex items-center justify-center py-12">
        <RefreshCwIcon className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  // Success state - show generated link
  if (generatedLink) {
    return (
      <div className="space-y-6">
        <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-start gap-3">
            <CheckIcon className="h-5 w-5 text-gray-900 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Ссылка регистрации создана!</p>
              {emailSent && (
                <p className="text-sm text-gray-600 mt-1">
                  Приглашение отправлено на {recipientEmail}
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-3">
          <Label className="text-sm font-medium text-gray-700">Ссылка регистрации</Label>
          <div className="flex items-center gap-2">
            <Input
              value={generatedLink.registration_url}
              readOnly
              className="flex-1 font-mono text-sm"
            />
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCopyLink}
              className="shrink-0"
            >
              {copied ? <CheckIcon className="h-4 w-4" /> : <CopyIcon className="h-4 w-4" />}
            </Button>
          </div>
          <p className="text-xs text-gray-600">
            {getExpiryInfo()}
          </p>
        </div>

        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-xs text-gray-700">
            <strong>Информация:</strong> Ссылка действительна в течение 24 часов.
            Пользователь сможет зарегистрироваться и создать заявку на подтверждение.
          </p>
        </div>

        <div className="flex gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setGeneratedLink(null)
              setSelectedCompany("")
              setSelectedDepartment("")
              setSelectedRole("")
              setSendEmail(false)
              setRecipientEmail("")
              setEmailSent(false)
            }}
            className="flex-1"
          >
            Создать еще одну ссылку
          </Button>
          {onCancel && (
            <Button
              type="button"
              onClick={onCancel}
              className="flex-1"
            >
              Закрыть
            </Button>
          )}
        </div>
      </div>
    )
  }

  // Form state - generate link
  return (
    <div>
      {error && (
        <div className="mb-6 p-4 bg-gray-50 border border-gray-300 rounded-lg">
          <div className="flex items-start gap-3">
            <AlertCircleIcon className="h-5 w-5 text-gray-900 mt-0.5" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">Ошибка</p>
              <p className="text-sm text-gray-700 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleGenerateLink} className="space-y-6">
        {/* Company Selection */}
        <div className="space-y-2">
          <Label htmlFor="company" className="text-sm font-medium text-gray-700">
            Компания *
          </Label>
          <Select
            value={selectedCompany}
            onValueChange={setSelectedCompany}
            disabled={isLoading}
          >
            <SelectTrigger id="company">
              <SelectValue placeholder="Выберите компанию" />
            </SelectTrigger>
            <SelectContent>
              {companies.map((company) => (
                <SelectItem key={company.id} value={company.id}>
                  {company.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Department Selection */}
        <div className="space-y-2">
          <Label htmlFor="department" className="text-sm font-medium text-gray-700">
            Отдел (опционально)
          </Label>
          <Select
            value={selectedDepartment}
            onValueChange={setSelectedDepartment}
            disabled={isLoading || !selectedCompany || departments.length === 0}
          >
            <SelectTrigger id="department">
              <SelectValue placeholder={
                !selectedCompany
                  ? "Сначала выберите компанию"
                  : departments.length === 0
                  ? "Нет доступных отделов"
                  : "Выберите отдел (или оставьте пустым для уровня компании)"
              } />
            </SelectTrigger>
            <SelectContent>
              {departments.map((department) => (
                <SelectItem key={department.id} value={department.id}>
                  {department.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-600">
            {!selectedDepartment
              ? "Для создания администратора компании оставьте это поле пустым"
              : "Для создания директора или пользователя отдела"}
          </p>
        </div>

        {/* Role Selection */}
        <div className="space-y-2">
          <Label htmlFor="role" className="text-sm font-medium text-gray-700">
            Роль *
          </Label>
          <Select
            value={selectedRole}
            onValueChange={setSelectedRole}
            disabled={isLoading || !selectedCompany}
          >
            <SelectTrigger id="role">
              <SelectValue placeholder="Выберите роль" />
            </SelectTrigger>
            <SelectContent>
              {availableRoles().map((role) => (
                <SelectItem key={role.value} value={role.value}>
                  {role.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Email Sending Option */}
        <div className="space-y-3 p-4 bg-gray-50 border border-gray-200 rounded-lg">
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="sendEmail"
              checked={sendEmail}
              onChange={(e) => setSendEmail(e.target.checked)}
              disabled={isLoading}
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="sendEmail" className="text-sm font-medium text-gray-700 cursor-pointer">
              Отправить приглашение по email
            </Label>
          </div>

          {sendEmail && (
            <div className="space-y-2 pl-6">
              <Label htmlFor="recipientEmail" className="text-sm text-gray-700">
                Email получателя
              </Label>
              <Input
                id="recipientEmail"
                type="email"
                placeholder="user@example.com"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                disabled={isLoading}
              />
            </div>
          )}
        </div>

        {/* Info Box */}
        <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
          <p className="text-xs text-gray-700">
            <strong>Примечание:</strong> Ссылка будет действительна в течение 24 часов.
            Пользователь сможет зарегистрироваться, после чего его заявка потребует вашего подтверждения.
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex gap-3">
          {onCancel && (
            <Button
              type="button"
              variant="outline"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1"
            >
              Отмена
            </Button>
          )}
          <Button
            type="submit"
            disabled={isLoading || !selectedCompany || !selectedRole}
            className="flex-1"
          >
            {isLoading ? (
              <>
                <RefreshCwIcon className="h-4 w-4 animate-spin mr-2" />
                Генерация ссылки...
              </>
            ) : (
              <>
                <Link2Icon className="h-4 w-4 mr-2" />
                Создать ссылку
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
