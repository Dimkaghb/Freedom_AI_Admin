

"use client"

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import { 
  Users, 
  Building2, 
  FileText, 
  Plus, 
  Activity, 
  TrendingUp,
  Settings,
  UserPlus,
  Link,
  CheckCircle,
  Clock,
  AlertCircle,
  ArrowUpRight, 
  ArrowDownRight, 
  MoreHorizontal, 
  Search, 
  Layers,
  Building
} from "lucide-react";
import { VisitorsAreaChart } from "@/components/charts/VisitorsAreaChart";

// Enhanced type definitions for dashboard components
interface StatCardProps {
  /** Заголовок, отображаемый на карточке статистики */
  title: string;
  /** Основное значение/число для отображения */
  value: string | number;
  /** Необязательное процентное изменение с предыдущего периода */
  change?: number;
  /** Направление тренда для визуальных индикаторов */
  trend?: "up" | "down" | "neutral";
  /** Необязательный текст описания под значением */
  description?: string;
  /** Необязательный компонент иконки для отображения */
  icon?: React.ReactNode;
  /** Необязательный className для пользовательского стиля */
  className?: string;
}

interface Request {
  /** Уникальный идентификатор запроса */
  id: string;
  /** Название/заголовок запроса */
  title: string;
  /** Тип/категория запроса */
  type: string;
  /** Текущий статус запроса */
  status: "Выполнено" | "В процессе" | "Ожидает";
  /** Лицо, назначенное для обработки запроса */
  assignee: string;
  /** Дата создания или последнего обновления запроса */
  date: string;
}

interface ChartDataPoint {
  /** Метка даты для точки графика */
  date: string;
  /** Количество посетителей на эту дату */
  visitors: number;
  /** Значение для графика производительности */
  value?: number;
}

interface DashboardStats {
  /** Количество холдингов */
  holdings: number;
  /** Количество зарегистрированных компаний */
  companies: number;
  /** Общее количество пользователей */
  totalUsers: number;
  /** Количество заявок */
  requests: number;
}

/**
 * Structure Management Component
 * Компонент для управления структурами организации
 */
function StructureManagement() {
  return (
    <Card className="w-full border-gray-200 bg-white">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold text-gray-900">Управление структурами</CardTitle>
            <CardDescription className="text-sm text-gray-600">
              Управление холдингами и компаниями
            </CardDescription>
          </div>
          <Button className="w-full sm:w-auto bg-gray-900 text-white hover:bg-gray-800 border-gray-900">
            <Settings className="h-4 w-4 mr-2" />
            Настройки
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-900">Холдинги</h4>
                <Building className="h-4 w-4 text-gray-500" />
              </div>
              <p className="text-2xl font-bold text-gray-900">3</p>
              <p className="text-xs text-gray-500">Активных структур</p>
            </div>
            <div className="p-4 border border-gray-200 rounded-lg bg-gray-50">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-medium text-gray-900">Компании</h4>
                <Building2 className="h-4 w-4 text-gray-500" />
              </div>
              <p className="text-2xl font-bold text-gray-900">12</p>
              <p className="text-xs text-gray-500">В составе холдингов</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-2">
            <Button variant="outline" className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-50">
              <Plus className="h-4 w-4 mr-2" />
              Добавить холдинг
            </Button>
            <Button variant="outline" className="flex-1 border-gray-300 text-gray-700 hover:bg-gray-50">
              <UserPlus className="h-4 w-4 mr-2" />
              Добавить компанию
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * StatCard Component - Отображает ключевые метрики с дополнительными индикаторами трендов
 * Адаптивный дизайн с правильными точками останова для мобильных/настольных устройств
 */
function StatCard({ 
  title, 
  value, 
  change, 
  trend = "neutral", 
  description, 
  icon,
  className = ""
}: StatCardProps) {
  const getTrendColor = (trend: StatCardProps['trend']): string => {
    switch (trend) {
      case "up": return "text-gray-900";
      case "down": return "text-gray-600";
      default: return "text-gray-500";
    }
  };

  const getTrendIcon = (trend: StatCardProps['trend']): React.ReactNode => {
    switch (trend) {
      case "up": return <ArrowUpRight className="h-3 w-3" />;
      case "down": return <ArrowDownRight className="h-3 w-3" />;
      default: return null;
    }
  };

  return (
    <Card className={`transition-all duration-200 hover:shadow-sm border-gray-200 bg-white ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-gray-600">
          {title}
        </CardTitle>
        {icon && (
          <div className="h-4 w-4 text-gray-500">
            {icon}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-1">
        <div className="text-2xl font-bold tracking-tight text-gray-900">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        <div className="flex items-center space-x-1 text-xs">
          {change !== undefined && (
            <>
              <span className={`flex items-center ${getTrendColor(trend)}`}>
                {getTrendIcon(trend)}
                <span className="ml-1">
                  {change > 0 ? '+' : ''}{change}%
                </span>
              </span>
              <span className="text-gray-500">с прошлого месяца</span>
            </>
          )}
          {description && !change && (
            <span className="text-gray-500">{description}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Recent Requests Table Component
 * Отображает недавнюю активность с адаптивным дизайном и правильной мобильной версткой
 * Включает значки статуса, действия и оптимизированную для мобильных устройств структуру таблицы
 */
function RecentRequestsTable() {
  // Пустой массив запросов - данные должны загружаться из API
  const requests: Request[] = [];

  const getStatusBadge = (status: Request['status']) => {
    const variants = {
      'Выполнено': 'default',
      'В процессе': 'secondary',
      'Ожидает': 'outline'
    } as const;

    const colors = {
      'Выполнено': 'bg-gray-100 text-gray-800 hover:bg-gray-100 border-gray-300',
      'В процессе': 'bg-gray-50 text-gray-700 hover:bg-gray-50 border-gray-200',
      'Ожидает': 'bg-white text-gray-600 hover:bg-gray-50 border-gray-300'
    };

    return (
      <Badge 
        variant={variants[status]} 
        className={`${colors[status]} text-xs font-medium`}
      >
        {status}
      </Badge>
    );
  };

  return (
    <Card className="w-full border-gray-200 bg-white">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg font-semibold text-gray-900">Недавние запросы</CardTitle>
            <CardDescription className="text-sm text-gray-600">
              Последняя активность вашей команды
            </CardDescription>
          </div>
          <Button className="w-full sm:w-auto bg-gray-900 text-white hover:bg-gray-800 border-gray-900">
            <Plus className="h-4 w-4 mr-2" />
            Новый запрос
          </Button>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        {/* Mobile-first responsive table */}
        <div className="overflow-x-auto">
          {requests.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500 text-sm">Нет данных для отображения</p>
              <p className="text-gray-400 text-xs mt-1">Запросы будут отображаться здесь после загрузки</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-200">
                  <TableHead className="text-xs font-medium text-gray-600">Название</TableHead>
                  <TableHead className="hidden sm:table-cell text-xs font-medium text-gray-600">Тип</TableHead>
                  <TableHead className="text-xs font-medium text-gray-600">Статус</TableHead>
                  <TableHead className="hidden md:table-cell text-xs font-medium text-gray-600">Исполнитель</TableHead>
                  <TableHead className="hidden lg:table-cell text-xs font-medium text-gray-600">Дата</TableHead>
                  <TableHead className="w-10"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((request) => (
                  <TableRow key={request.id} className="border-gray-200 hover:bg-gray-50">
                    <TableCell className="py-3">
                      <div className="space-y-1">
                        <p className="text-sm font-medium text-gray-900">{request.title}</p>
                        <p className="text-xs text-gray-500 sm:hidden">{request.type}</p>
                      </div>
                    </TableCell>
                    <TableCell className="hidden sm:table-cell py-3">
                      <span className="text-sm text-gray-600">{request.type}</span>
                    </TableCell>
                    <TableCell className="py-3">
                      {getStatusBadge(request.status)}
                    </TableCell>
                    <TableCell className="hidden md:table-cell py-3">
                      <span className="text-sm text-gray-900">{request.assignee}</span>
                    </TableCell>
                    <TableCell className="hidden lg:table-cell py-3">
                      <span className="text-sm text-gray-500">{request.date}</span>
                    </TableCell>
                    <TableCell className="py-3">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0 hover:bg-gray-100">
                        <MoreHorizontal className="h-4 w-4 text-gray-500" />
                        <span className="sr-only">Открыть меню</span>
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Main Dashboard Component
 * Адаптивная компоновка с мобильным подходом
 * Реализует правильные отступы, типографику и стандарты доступности
 */
export const Dashboard = () => {
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('Последние 3 месяца');

  // Пустые данные - должны загружаться из API
  const dashboardStats: DashboardStats = {
    holdings: 3,
    companies: 12,
    totalUsers: 240,
    requests: 4
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
        {/* Header Section - Responsive layout */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              Dashboard
            </h1>
            <p className="text-sm text-muted-foreground">
              Welcome back! Here's what's happening with your projects.
            </p>
          </div>
          
          {/* Search Bar - Mobile responsive */}
          <div className="relative w-full sm:w-auto sm:min-w-[300px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="pl-9 w-full"
              aria-label="Search dashboard"
            />
          </div>
        </div>

        {/* Statistics Cards - Responsive grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
          <StatCard
            title="Холдинги"
            value={dashboardStats.holdings}
            change={0}
            trend="neutral"
            description="Данные загружаются"
            icon={<Building className="h-4 w-4" />}
          />
          <StatCard
            title="Компании"
            value={dashboardStats.companies}
            change={0}
            trend="neutral"
            description="Данные загружаются"
            icon={<Building2 className="h-4 w-4" />}
          />
          <StatCard
            title="Пользователи"
            value={dashboardStats.totalUsers}
            change={0}
            trend="neutral"
            description="Данные загружаются"
            icon={<Users className="h-4 w-4" />}
          />
          <StatCard
            title="Заявки"
            value={dashboardStats.requests}
            change={0}
            trend="neutral"
            description="Данные загружаются"
            icon={<FileText className="h-4 w-4" />}
          />
        </div>

        {/* Charts Section - Full width */}
        <div className="w-full">
          <VisitorsAreaChart />
        </div>

        {/* Bottom Section - Recent Requests and Structure Management */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Requests Table */}
          <div className="lg:col-span-1">
            <RecentRequestsTable />
          </div>
          
          {/* Structure Management */}
          <div className="lg:col-span-1">
            <StructureManagement />
          </div>
        </div>
      </div>
    </div>
  );
};