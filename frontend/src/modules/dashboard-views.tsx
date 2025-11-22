/**
 * Role-Specific Dashboard Views
 *
 * Separate components for each user role's dashboard view.
 * Each component displays data relevant to the user's permissions.
 */

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Building,
  Building2,
  Layers,
  Users,
  TrendingUp,
  Plus,
  ArrowRight,
  UserCheck,
  Clock,
} from 'lucide-react';
import type {
  SuperadminDashboardResponse,
  AdminDashboardResponse,
  DirectorDashboardResponse,
  UserDashboardResponse,
} from '@/types/dashboard';
import { formatRelativeTime, getUserFullName, getStatusColor, getStatusText } from '@/types/dashboard';

// ============================================================================
// Superadmin Dashboard View
// ============================================================================

export const SuperadminDashboardView: React.FC<{
  data: SuperadminDashboardResponse;
  onCreateHolding?: () => void;
  onCreateCompany?: () => void;
  onCreateDepartment?: () => void;
}> = ({ data, onCreateHolding, onCreateCompany, onCreateDepartment }) => {
  return (
    <div className="space-y-6">
      {/* Holdings Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Холдинги</CardTitle>
              <CardDescription>
                Всего: {data.holdings.length}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onCreateHolding}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить холдинг
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.holdings.map((holding) => (
              <Card key={holding.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <Building className="h-5 w-5 text-gray-500" />
                    <Badge variant="outline" className="text-xs">
                      {holding.companies_count} компаний
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">{holding.name}</CardTitle>
                  {holding.description && (
                    <CardDescription className="text-sm">
                      {holding.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="flex items-center justify-between text-xs text-gray-500">
                    <span>{formatRelativeTime(holding.created_at)}</span>
                    <Button variant="ghost" size="sm" className="h-7 px-2">
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Companies */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Недавние компании</CardTitle>
              <CardDescription>
                Последние {data.recent_companies.length} добавленных компаний
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onCreateCompany}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить компанию
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {data.recent_companies.map((company) => (
              <div
                key={company.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100">
                    <Building2 className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{company.name}</p>
                    <p className="text-xs text-gray-500">
                      {company.holding_name} • {company.departments_count} отделов • {company.users_count} пользователей
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500">{formatRelativeTime(company.created_at)}</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Departments & Users */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Departments */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">Недавние отделы</CardTitle>
              <Button variant="outline" size="sm" onClick={onCreateDepartment}>
                <Plus className="h-4 w-4 mr-2" />
                Добавить отдел
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.recent_departments.slice(0, 5).map((dept) => (
                <div key={dept.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium">{dept.name}</p>
                      <p className="text-xs text-gray-500">{dept.company_name}</p>
                    </div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {dept.users_count} чел.
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Users */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Новые пользователи</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.recent_users.slice(0, 5).map((user) => (
                <div key={user.id} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                  <div className="flex items-center gap-2">
                    <UserCheck className="h-4 w-4 text-gray-400" />
                    <div>
                      <p className="text-sm font-medium">{getUserFullName(user)}</p>
                      <p className="text-xs text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <Badge className={getStatusColor(user.is_active)}>
                    {getStatusText(user.is_active)}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============================================================================
// Admin Dashboard View
// ============================================================================

export const AdminDashboardView: React.FC<{
  data: AdminDashboardResponse;
  onCreateDepartment?: () => void;
}> = ({ data, onCreateDepartment }) => {
  return (
    <div className="space-y-6">
      {/* Company Overview */}
      {data.company && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-lg">Ваша компания</CardTitle>
                <CardDescription>{data.company.name}</CardDescription>
              </div>
              <Building2 className="h-8 w-8 text-gray-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-gray-500">Холдинг</p>
                <p className="text-sm font-medium">{data.company.holding_name || '—'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-gray-500">Отделов</p>
                <p className="text-sm font-medium">{data.company.departments_count}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-gray-500">Сотрудников</p>
                <p className="text-sm font-medium">{data.company.users_count}</p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-gray-500">Создана</p>
                <p className="text-sm font-medium">{formatRelativeTime(data.company.created_at)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Departments List */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Отделы компании</CardTitle>
              <CardDescription>
                Всего: {data.departments.length}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={onCreateDepartment}>
              <Plus className="h-4 w-4 mr-2" />
              Добавить отдел
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.departments.map((dept) => (
              <Card key={dept.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <Layers className="h-5 w-5 text-gray-500" />
                    <Badge variant="outline" className="text-xs">
                      {dept.users_count} чел.
                    </Badge>
                  </div>
                  <CardTitle className="text-base mt-2">{dept.name}</CardTitle>
                  {dept.description && (
                    <CardDescription className="text-sm">
                      {dept.description}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="pt-0">
                  <div className="space-y-1">
                    {dept.manager_name && (
                      <p className="text-xs text-gray-500">
                        Руководитель: {dept.manager_name}
                      </p>
                    )}
                    <p className="text-xs text-gray-500">
                      Создан: {formatRelativeTime(dept.created_at)}
                    </p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recent Users */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Недавние сотрудники</CardTitle>
          <CardDescription>
            Последние {data.recent_users.length} добавленных в компанию
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.recent_users.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                    <Users className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{getUserFullName(user)}</p>
                    <p className="text-xs text-gray-500">
                      {user.email} • {user.department_name || 'Без отдела'}
                    </p>
                  </div>
                </div>
                <Badge className={getStatusColor(user.is_active)}>
                  {getStatusText(user.is_active)}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ============================================================================
// Director Dashboard View
// ============================================================================

export const DirectorDashboardView: React.FC<{
  data: DirectorDashboardResponse;
}> = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Department & Company Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Department Card */}
        {data.department && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Ваш отдел</CardTitle>
                  <CardDescription>{data.department.name}</CardDescription>
                </div>
                <Layers className="h-8 w-8 text-gray-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.department.description && (
                  <p className="text-sm text-gray-600">{data.department.description}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500">Сотрудников</p>
                    <p className="text-xl font-semibold">{data.department.users_count}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500">Создан</p>
                    <p className="text-sm">{formatRelativeTime(data.department.created_at)}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Company Card */}
        {data.company && (
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Компания</CardTitle>
                  <CardDescription>{data.company.name}</CardDescription>
                </div>
                <Building2 className="h-8 w-8 text-gray-400" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.company.description && (
                  <p className="text-sm text-gray-600">{data.company.description}</p>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500">Всего отделов</p>
                    <p className="text-xl font-semibold">{data.company.departments_count}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500">Всего сотрудников</p>
                    <p className="text-xl font-semibold">{data.company.users_count}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Department Team */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Команда отдела</CardTitle>
              <CardDescription>
                Всего сотрудников: {data.users.length}
              </CardDescription>
            </div>
            <Button variant="outline" size="sm">
              <Plus className="h-4 w-4 mr-2" />
              Пригласить
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.users.map((user) => (
              <div
                key={user.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                    <Users className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{getUserFullName(user)}</p>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">
                    {user.role}
                  </Badge>
                  <Badge className={getStatusColor(user.is_active)}>
                    {getStatusText(user.is_active)}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// ============================================================================
// User Dashboard View (Read-only)
// ============================================================================

export const UserDashboardView: React.FC<{
  data: UserDashboardResponse;
}> = ({ data }) => {
  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <Card className="border-blue-200 bg-blue-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <Clock className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-blue-900">Информационная панель</h3>
              <p className="text-sm text-blue-700 mt-1">
                Вы можете просматривать информацию о вашем отделе и коллегах.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Department & Company Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Department Card */}
        {data.department && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Ваш отдел</CardTitle>
              <CardDescription>{data.department.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.department.description && (
                  <p className="text-sm text-gray-600">{data.department.description}</p>
                )}
                <div className="space-y-2">
                  {data.department.manager_name && (
                    <div>
                      <p className="text-xs text-gray-500">Руководитель</p>
                      <p className="text-sm font-medium">{data.department.manager_name}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500">Сотрудников в отделе</p>
                    <p className="text-sm font-medium">{data.department.users_count}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Company Card */}
        {data.company && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Компания</CardTitle>
              <CardDescription>{data.company.name}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {data.company.description && (
                  <p className="text-sm text-gray-600">{data.company.description}</p>
                )}
                <div className="space-y-2">
                  <div>
                    <p className="text-xs text-gray-500">Всего отделов</p>
                    <p className="text-sm font-medium">{data.company.departments_count}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Всего сотрудников</p>
                    <p className="text-sm font-medium">{data.company.users_count}</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Colleagues */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Коллеги по отделу</CardTitle>
          <CardDescription>
            Сотрудников: {data.colleagues.length}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {data.colleagues.map((colleague) => (
              <div
                key={colleague.id}
                className="flex items-center justify-between p-3 rounded-lg border"
              >
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gray-100">
                    <Users className="h-5 w-5 text-gray-600" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{getUserFullName(colleague)}</p>
                    <p className="text-xs text-gray-500">{colleague.email}</p>
                  </div>
                </div>
                <Badge variant="outline" className="text-xs">
                  {colleague.role}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
