import { useState, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { apiClient } from "@/lib/axios"

interface RegistrationResponse {
  id: string
  email: string
  full_name: string
  status: string
  message?: string
}

export function RegisterForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [searchParams] = useSearchParams()
  const linkId = searchParams.get("link_id")

  const [formData, setFormData] = useState({
    email: "",
    firstName: "",
    lastName: "",
    password: "",
    password_confirm: "",
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Check if link_id exists
  useEffect(() => {
    if (!linkId) {
      setError("Недействительная ссылка регистрации. Пожалуйста, запросите новую ссылку у администратора.")
    }
  }, [linkId])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
    // Clear error when user starts typing
    if (error) setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (formData.password !== formData.password_confirm) {
      setError("Пароли не совпадают")
      return
    }

    if (formData.password.length < 8) {
      setError("Пароль должен содержать минимум 8 символов")
      return
    }

    if (!linkId) {
      setError("Недействительная ссылка регистрации")
      return
    }

    setIsLoading(true)

    try {
      const response = await apiClient.post<RegistrationResponse>("/users/register", {
        link_id: linkId,
        email: formData.email,
        firstName: formData.firstName,
        lastName: formData.lastName,
        password: formData.password,
        password_confirm: formData.password_confirm,
      })

      console.log("Registration successful:", response.data)
      setSuccess(true)
    } catch (err: any) {
      console.error("Registration error:", err)

      // Handle validation errors (array of error objects)
      let errorMessage = "Ошибка при регистрации. Пожалуйста, попробуйте позже."

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail

        // Check if detail is an array of validation errors
        if (Array.isArray(detail)) {
          errorMessage = detail.map((error: any) => error.msg || error.message || String(error)).join(', ')
        }
        // Check if detail is a string
        else if (typeof detail === 'string') {
          errorMessage = detail
        }
        // Check if detail is an object with msg
        else if (typeof detail === 'object' && detail.msg) {
          errorMessage = detail.msg
        }
      }

      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  // Success modal
  if (success) {
    return (
      <div className={cn("flex flex-col gap-6", className)} {...props}>
        <Card>
          <CardHeader>
            <CardTitle>Заявка отправлена</CardTitle>
            <CardDescription>
              Ваша заявка ожидает подтверждение админом
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 text-sm text-green-700 bg-green-50 border border-green-200 rounded-md">
              <p className="font-medium mb-2">Ваша регистрация успешно отправлена!</p>
              <p className="text-green-600">
                Администратор получил вашу заявку и рассмотрит её в ближайшее время.
                Вы получите уведомление по email после одобрения.
              </p>
            </div>
            <div className="flex flex-col gap-2">
              <p className="text-sm text-gray-600">Что дальше?</p>
              <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                <li>Администратор получит уведомление о новой заявке</li>
                <li>После одобрения вы сможете войти в систему</li>
                <li>Используйте те же учетные данные для входа</li>
              </ul>
            </div>
            <Button
              onClick={() => window.location.href = "/"}
              className="w-full"
            >
              Вернуться на страницу входа
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <Card>
        <CardHeader>
          <CardTitle>Регистрация нового пользователя</CardTitle>
          <CardDescription>
            Заполните форму ниже для создания аккаунта
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <FieldGroup>
              {error && (
                <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
                  {error}
                </div>
              )}

              <Field>
                <FieldLabel htmlFor="firstName">Имя</FieldLabel>
                <Input
                  id="firstName"
                  name="firstName"
                  type="text"
                  placeholder="Иван"
                  value={formData.firstName}
                  onChange={handleChange}
                  required
                  disabled={isLoading || !linkId}
                  autoComplete="given-name"
                />
              </Field>

              <Field>
                <FieldLabel htmlFor="lastName">Фамилия</FieldLabel>
                <Input
                  id="lastName"
                  name="lastName"
                  type="text"
                  placeholder="Иванов"
                  value={formData.lastName}
                  onChange={handleChange}
                  required
                  disabled={isLoading || !linkId}
                  autoComplete="family-name"
                />
              </Field>

              <Field>
                <FieldLabel htmlFor="email">Email</FieldLabel>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="ivan@example.com"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  disabled={isLoading || !linkId}
                  autoComplete="email"
                />
              </Field>

              <Field>
                <FieldLabel htmlFor="password">Пароль</FieldLabel>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Минимум 8 символов"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  disabled={isLoading || !linkId}
                  autoComplete="new-password"
                  minLength={8}
                />
                <FieldDescription>
                  Минимум 8 символов
                </FieldDescription>
              </Field>

              <Field>
                <FieldLabel htmlFor="password_confirm">Подтверждение пароля</FieldLabel>
                <Input
                  id="password_confirm"
                  name="password_confirm"
                  type="password"
                  placeholder="Повторите пароль"
                  value={formData.password_confirm}
                  onChange={handleChange}
                  required
                  disabled={isLoading || !linkId}
                  autoComplete="new-password"
                  minLength={8}
                />
              </Field>

              <Field>
                <Button
                  type="submit"
                  disabled={isLoading || !linkId}
                  className="w-full"
                >
                  {isLoading ? "Отправка заявки..." : "Отправить заявку"}
                </Button>
                <FieldDescription className="text-center">
                  Уже есть аккаунт?{" "}
                  <a href="/" className="underline">
                    Войти
                  </a>
                </FieldDescription>
              </Field>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
