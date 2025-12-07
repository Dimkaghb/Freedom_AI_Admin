"use client"

import type React from "react"
import { useState, useEffect, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { CheckCircle, XCircle, Clock, RefreshCw, UserCheck, UserX, Trash2, AlertCircle, UserPlus, Link2, ArrowLeft } from "lucide-react"
import { CreateRegistrationLinkForm } from '@/components/CreateRegistrationLinkForm'
import { AddUserForm } from './addUser'
import { listUsers, listPendingUsers, approvePendingUser, rejectPendingUser, deleteUser } from "@/services/user.api"
import type { UserResponse, PendingUserResponse } from "@/services/user.api"
import { listCompanies } from "@/services/company.api"
import { listDepartments } from "@/services/department.api"
import { listHoldings } from "@/services/holding.api"
import type { CompanyResponse } from "@/services/company.api"
import type { DepartmentResponse } from "@/services/department.api"
import type { HoldingResponse } from "@/services/holding.api"

/**
 * UsersManagement component with enhanced layout:
 * - Top row: Add User form (left) + Pending Users list (right)
 * - Bottom row: Comprehensive users table
 */
export function UsersManagement() {
  // Users state
  const [users, setUsers] = useState<UserResponse[]>([])
  const [pendingUsers, setPendingUsers] = useState<PendingUserResponse[]>([])
  const [loadingUsers, setLoadingUsers] = useState(false)
  const [loadingPending, setLoadingPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null)
  const [addUserMethod, setAddUserMethod] = useState<'link' | 'manual' | null>(null)

  // Organization data for lookups
  const [companies, setCompanies] = useState<CompanyResponse[]>([])
  const [departments, setDepartments] = useState<DepartmentResponse[]>([])
  const [holdings, setHoldings] = useState<HoldingResponse[]>([])
  const [organizationsLoaded, setOrganizationsLoaded] = useState(false)

  /**
   * Fetch all users
   */
  const fetchUsers = useCallback(async () => {
    setLoadingUsers(true)
    setError(null)
    try {
      const activeUsers = await listUsers('active')
      setUsers(activeUsers)
    } catch (err: any) {
      setError(err.message || 'Failed to load users')
    } finally {
      setLoadingUsers(false)
    }
  }, [])

  /**
   * Fetch pending users
   */
  const fetchPendingUsers = useCallback(async () => {
    setLoadingPending(true)
    try {
      const pending = await listPendingUsers()
      setPendingUsers(pending)
    } catch (err: any) {
      console.error('Failed to load pending users:', err)
    } finally {
      setLoadingPending(false)
    }
  }, [])

  /**
   * Handle approve pending user
   */
  const handleApprove = useCallback(async (userId: string) => {
    try {
      await approvePendingUser(userId)
      // Refresh both lists
      await Promise.all([fetchPendingUsers(), fetchUsers()])
    } catch (err: any) {
      setError(err.message || 'Failed to approve user')
    }
  }, [fetchPendingUsers, fetchUsers])

  /**
   * Handle reject pending user
   */
  const handleReject = useCallback(async (userId: string) => {
    try {
      await rejectPendingUser(userId)
      // Refresh pending list
      await fetchPendingUsers()
    } catch (err: any) {
      setError(err.message || 'Failed to reject user')
    }
  }, [fetchPendingUsers])

  /**
   * Handle delete user with confirmation
   */
  const handleDelete = useCallback(async (userId: string, userEmail: string) => {
    // Show confirmation dialog
    const confirmed = window.confirm(
      `Вы уверены, что хотите удалить пользователя ${userEmail}?\n\nЭто действие необратимо и приведет к:\n- Удалению пользователя из системы\n- Удалению из должностей администратора компании или менеджера отдела\n- Удалению всех связанных данных`
    )

    if (!confirmed) {
      return
    }

    setDeletingUserId(userId)
    setError(null)
    setSuccessMessage(null)

    try {
      const result = await deleteUser(userId)
      setSuccessMessage(`Пользователь ${result.email} успешно удален`)
      // Refresh users list
      await fetchUsers()

      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000)
    } catch (err: any) {
      setError(err.message || 'Failed to delete user')
    } finally {
      setDeletingUserId(null)
    }
  }, [fetchUsers])

  /**
   * Load organizations data for lookups
   */
  const fetchOrganizations = useCallback(async () => {
    try {
      const [companiesData, departmentsData, holdingsData] = await Promise.all([
        listCompanies(),
        listDepartments(),
        listHoldings(),
      ])
      setCompanies(companiesData)
      setDepartments(departmentsData)
      setHoldings(holdingsData)
      setOrganizationsLoaded(true)
    } catch (err: any) {
      console.error('Failed to load organizations:', err)
      setOrganizationsLoaded(true) // Set to true anyway to prevent infinite loading
    }
  }, [])

  /**
   * Get company name by ID
   */
  const getCompanyName = useCallback((companyId?: string) => {
    if (!companyId) return null
    const company = companies.find(c => c.id === companyId)
    return company?.name || companyId
  }, [companies])

  /**
   * Get department name by ID
   */
  const getDepartmentName = useCallback((departmentId?: string) => {
    if (!departmentId) return null
    const department = departments.find(d => d.id === departmentId)
    return department?.name || departmentId
  }, [departments])

  /**
   * Get holding name by ID
   */
  const getHoldingName = useCallback((holdingId?: string) => {
    if (!holdingId) return null
    const holding = holdings.find(h => h.id === holdingId)
    return holding?.name || holdingId
  }, [holdings])

  /**
   * Load data on mount
   */
  useEffect(() => {
    fetchOrganizations()
    fetchUsers()
    fetchPendingUsers()
  }, [fetchOrganizations, fetchUsers, fetchPendingUsers])

  /**
   * Get status badge
   */
  const getStatusBadge = (isActive: boolean) => {
    return isActive ? (
      <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
        <CheckCircle className="h-3 w-3 mr-1" />
        Активный
      </Badge>
    ) : (
      <Badge variant="destructive">
        <XCircle className="h-3 w-3 mr-1" />
        Заблокирован
      </Badge>
    )
  }

  /**
   * Get role badge
   */
  const getRoleBadge = (role: string) => {
    const roleColors: Record<string, string> = {
      superadmin: 'bg-purple-100 text-purple-700',
      admin: 'bg-blue-100 text-blue-700',
      director: 'bg-indigo-100 text-indigo-700',
      user: 'bg-gray-100 text-gray-700',
    }

    const roleNames: Record<string, string> = {
      superadmin: 'Суперадмин',
      admin: 'Администратор',
      director: 'Директор',
      user: 'Пользователь',
    }

    return (
      <Badge className={`${roleColors[role] || roleColors.user} hover:${roleColors[role]}`}>
        {roleNames[role] || role}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      {/* Top Row: Add User + Pending Users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Add User Section */}
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
              {addUserMethod && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAddUserMethod(null)}
                  className="h-8 w-8 p-0"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
              )}
              {!addUserMethod && "Добавить пользователя"}
              {addUserMethod === 'link' && "Создать ссылку регистрации"}
              {addUserMethod === 'manual' && "Добавить пользователя вручную"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Method Selection Buttons */}
            {!addUserMethod && (
              <div className="space-y-3">
                <Button
                  onClick={() => setAddUserMethod('link')}
                  variant="outline"
                  className="w-full h-auto py-4 px-4 flex items-start gap-3 hover:bg-gray-50 border-2"
                >
                  <Link2 className="h-5 w-5 mt-0.5 shrink-0" />
                  <div className="text-left flex-1">
                    <div className="font-semibold text-sm mb-1">Сгенерировать ссылку регистрации</div>
                    <div className="text-xs text-gray-600 font-normal">
                      Пользователь самостоятельно заполнит данные
                    </div>
                  </div>
                </Button>

                <Button
                  onClick={() => setAddUserMethod('manual')}
                  variant="outline"
                  className="w-full h-auto py-4 px-4 flex items-start gap-3 hover:bg-gray-50 border-2"
                >
                  <UserPlus className="h-5 w-5 mt-0.5 shrink-0" />
                  <div className="text-left flex-1">
                    <div className="font-semibold text-sm mb-1">Добавить вручную</div>
                    <div className="text-xs text-gray-600 font-normal">
                      Заполните данные и создайте временный пароль
                    </div>
                  </div>
                </Button>
              </div>
            )}

            {/* Registration Link Form */}
            {addUserMethod === 'link' && (
              <CreateRegistrationLinkForm
                onSuccess={() => {
                  fetchUsers()
                  fetchPendingUsers()
                }}
                onCancel={() => setAddUserMethod(null)}
              />
            )}

            {/* Manual Add Form */}
            {addUserMethod === 'manual' && (
              <AddUserForm
                onUserCreated={() => {
                  fetchUsers()
                  setAddUserMethod(null)
                }}
              />
            )}
          </CardContent>
        </Card>

        {/* Pending Users Section */}
        <Card className="border border-gray-200 shadow-sm">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg font-semibold text-gray-900">
                Ожидают подтверждения
              </CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchPendingUsers}
                disabled={loadingPending}
              >
                <RefreshCw className={`h-4 w-4 ${loadingPending ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {loadingPending ? (
                <div className="flex items-center justify-center py-8">
                  <RefreshCw className="h-6 w-6 animate-spin text-gray-400" />
                </div>
              ) : pendingUsers.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Clock className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                  <p className="text-sm">Нет ожидающих пользователей</p>
                </div>
              ) : (
                pendingUsers.map((user) => (
                  <div
                    key={user.id}
                    className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg"
                  >
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900">
                        {user.firstName} {user.lastName}
                      </p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                      <div className="mt-1">
                        {getRoleBadge(user.role)}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-green-600 hover:text-green-700 hover:bg-green-50"
                        onClick={() => handleApprove(user.id)}
                      >
                        <UserCheck className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => handleReject(user.id)}
                      >
                        <UserX className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bottom Row: Users Table */}
      <Card className="border border-gray-200 shadow-sm">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-gray-900">
              Все пользователи
            </CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchUsers}
              disabled={loadingUsers}
            >
              <RefreshCw className={`h-4 w-4 ${loadingUsers ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Success Message */}
          {successMessage && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-900">Успешно</p>
                  <p className="text-sm text-green-700 mt-1">{successMessage}</p>
                </div>
              </div>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">Ошибка</p>
                  <p className="text-sm text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {loadingUsers ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="text-center py-8 text-red-600">
              <p className="text-sm">{error}</p>
            </div>
          ) : users.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p className="text-sm">Пользователи не найдены</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">№</TableHead>
                    <TableHead>Имя</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Статус</TableHead>
                    <TableHead>Холдинг</TableHead>
                    <TableHead>Компания</TableHead>
                    <TableHead>Отдел</TableHead>
                    <TableHead>Роль</TableHead>
                    <TableHead className="w-24">Действия</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {users.map((user, index) => (
                    <TableRow key={user.id} className="hover:bg-gray-50">
                      <TableCell className="font-medium text-gray-500">{index + 1}</TableCell>
                      <TableCell className="font-medium">
                        {user.firstName && user.lastName
                          ? `${user.firstName} ${user.lastName}`
                          : user.email.split('@')[0]}
                      </TableCell>
                      <TableCell className="text-gray-600">{user.email}</TableCell>
                      <TableCell>{getStatusBadge(user.is_active)}</TableCell>
                      <TableCell className="text-gray-600">
                        {getHoldingName(user.holding_id) || <span className="text-gray-400 italic">—</span>}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {getCompanyName(user.company_id) || <span className="text-gray-400 italic">—</span>}
                      </TableCell>
                      <TableCell className="text-gray-600">
                        {getDepartmentName(user.department_id) || <span className="text-gray-400 italic">—</span>}
                      </TableCell>
                      <TableCell>{getRoleBadge(user.role)}</TableCell>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDelete(user.id, user.email)}
                          disabled={deletingUserId === user.id}
                        >
                          {deletingUserId === user.id ? (
                            <RefreshCw className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default UsersManagement
