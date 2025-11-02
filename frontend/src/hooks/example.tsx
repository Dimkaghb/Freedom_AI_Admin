"use client"

import type React from "react"
import { DashboardLayout } from "@/components/layout/dashboard-layout"
import {
  Building2,
  Users,
  Layers,
  FileText,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  MoreHorizontal,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from "recharts"

interface StatCardProps {
  title: string
  value: string | number
  change?: number
  trend?: "up" | "down" | "neutral"
  description?: string
  icon?: React.ReactNode
}

function StatCard({ title, value, change, trend = "neutral", description, icon }: StatCardProps) {
  return (
    <Card className="border-border bg-card">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-xs font-medium text-muted-foreground">{title}</p>
            <p className="text-2xl font-bold text-foreground">{value}</p>
          </div>
          {icon && <div className="rounded-lg bg-primary/10 p-1.5 text-primary">{icon}</div>}
        </div>

        {change !== undefined && (
          <div className="mt-3 flex items-center gap-2">
            {trend === "up" ? (
              <div className="flex items-center gap-1 text-primary">
                <ArrowUpRight className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">+{change}%</span>
              </div>
            ) : trend === "down" ? (
              <div className="flex items-center gap-1 text-destructive">
                <ArrowDownRight className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">-{change}%</span>
              </div>
            ) : (
              <div className="flex items-center gap-1 text-muted-foreground">
                <TrendingUp className="h-3.5 w-3.5" />
                <span className="text-xs font-medium">{change}%</span>
              </div>
            )}
            {description && <span className="text-xs text-muted-foreground">{description}</span>}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const chartData: { date: string; visitors: number }[] = []

function VisitorsChart() {
  return (
    <Card className="border-border bg-card">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 p-4 pb-3">
        <div>
          <CardTitle className="text-sm font-semibold text-foreground">Всего посетителей</CardTitle>
          <p className="text-xs text-muted-foreground">Всего за последние 3 месяца</p>
        </div>
        <div className="flex gap-1.5">
          <Button variant="outline" size="sm" className="h-7 bg-transparent text-xs">
            Последние 3 месяца
          </Button>
          <Button variant="outline" size="sm" className="h-7 bg-transparent text-xs">
            Последние 30 дней
          </Button>
          <Button variant="outline" size="sm" className="h-7 bg-transparent text-xs">
            Последние 7 дней
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4 pt-0">
        {chartData.length === 0 ? (
          <div className="flex h-60 items-center justify-center">
            <p className="text-xs text-muted-foreground">Нет данных для отображения</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="colorVisitors" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="date"
                stroke="hsl(var(--muted-foreground))"
                fontSize={10}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
              />
              <Area
                type="monotone"
                dataKey="visitors"
                stroke="hsl(var(--primary))"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorVisitors)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

interface Request {
  id: string
  title: string
  type: string
  status: "Done" | "In Progress" | "Pending"
  assignee: string
  date: string
}

const mockRequests: Request[] = []

function RecentRequestsTable() {
  return (
    <div className="rounded-lg border border-border bg-card">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-xs text-muted-foreground">Название</TableHead>
            <TableHead className="text-xs text-muted-foreground">Тип</TableHead>
            <TableHead className="text-xs text-muted-foreground">Статус</TableHead>
            <TableHead className="text-xs text-muted-foreground">Исполнитель</TableHead>
            <TableHead className="text-xs text-muted-foreground">Дата</TableHead>
            <TableHead className="w-12"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {mockRequests.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="h-24 text-center">
                <p className="text-xs text-muted-foreground">Нет данных для отображения</p>
              </TableCell>
            </TableRow>
          ) : (
            mockRequests.map((request) => (
              <TableRow key={request.id} className="border-border hover:bg-accent/50">
                <TableCell className="text-xs font-medium text-foreground">{request.title}</TableCell>
                <TableCell>
                  <Badge variant="secondary" className="bg-secondary/50 text-xs">
                    {request.type}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={request.status === "Done" ? "default" : "secondary"}
                    className={
                      request.status === "Done"
                        ? "bg-primary text-xs text-primary-foreground"
                        : "bg-muted text-xs text-muted-foreground"
                    }
                  >
                    <span
                      className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${
                        request.status === "Done" ? "bg-primary-foreground" : "bg-muted-foreground"
                      }`}
                    />
                    {request.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-xs text-foreground">{request.assignee}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{request.date}</TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon" className="h-7 w-7">
                    <MoreHorizontal className="h-3.5 w-3.5" />
                  </Button>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  )
}

export default function DashboardPage() {
  return (
    <DashboardLayout title="Панель управления">
      <div className="space-y-4">
        {/* Stats Grid */}
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          <StatCard title="Всего холдингов" value="0" icon={<Building2 className="h-4 w-4" />} />
          <StatCard title="Компании" value="0" icon={<Building2 className="h-4 w-4" />} />
          <StatCard title="Активные пользователи" value="0" icon={<Users className="h-4 w-4" />} />
          <StatCard title="Отделы" value="0" icon={<Layers className="h-4 w-4" />} />
        </div>

        {/* Chart */}
        <VisitorsChart />

        {/* Recent Requests */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Последние запросы</h2>
              <p className="text-xs text-muted-foreground">Последняя активность вашей команды</p>
            </div>
            <Button className="h-8 bg-primary text-xs text-primary-foreground hover:bg-primary/90">
              <FileText className="mr-1.5 h-3.5 w-3.5" />
              Новый запрос
            </Button>
          </div>
          <RecentRequestsTable />
        </div>
      </div>
    </DashboardLayout>
  )
}
