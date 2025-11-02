"use client"

import { TrendingUp } from "lucide-react"
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts"

import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"

/**
 * Chart configuration type for styling and labels
 */
type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    color?: string;
  };
};

/**
 * Chart data interface for visitor statistics
 */
interface ChartDataPoint {
  month: string;
  desktop: number;
}

/**
 * Props for the VisitorsAreaChart component
 */
interface VisitorsAreaChartProps {
  /** Optional custom data to display, defaults to sample data */
  data?: ChartDataPoint[];
  /** Optional custom title for the chart */
  title?: string;
  /** Optional custom description for the chart */
  description?: string;
  /** Optional className for custom styling */
  className?: string;
}

// Sample chart data - can be replaced with real data
const defaultChartData: ChartDataPoint[] = [
  { month: "January", desktop: 186 },
  { month: "February", desktop: 305 },
  { month: "March", desktop: 237 },
  { month: "April", desktop: 73 },
  { month: "May", desktop: 209 },
  { month: "June", desktop: 214 },
]

// Chart configuration for styling and labels
const chartConfig = {
  desktop: {
    label: "Visitors",
    color: "#6b7280", // Grey color
  },
} satisfies ChartConfig

/**
 * VisitorsAreaChart Component
 * 
 * A responsive area chart component that displays visitor data over time.
 * Uses Recharts library with shadcn/ui chart components for consistent styling.
 * 
 * @param data - Array of chart data points (optional, uses sample data if not provided)
 * @param title - Custom title for the chart (optional)
 * @param description - Custom description for the chart (optional)
 * @param className - Additional CSS classes for styling (optional)
 */
export function VisitorsAreaChart({ 
  data = defaultChartData,
  title = "Visitors Overview",
  description = "Showing total visitors for the last 6 months",
  className = ""
}: VisitorsAreaChartProps) {
  // Calculate trend percentage (simplified calculation)
  const currentMonth = data[data.length - 1]?.desktop || 0;
  const previousMonth = data[data.length - 2]?.desktop || 0;
  const trendPercentage = previousMonth > 0 
    ? ((currentMonth - previousMonth) / previousMonth * 100).toFixed(1)
    : "0.0";

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
        <CardDescription className="text-sm text-muted-foreground">
          {description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[200px] w-full">
          <AreaChart
            accessibilityLayer
            data={data}
            margin={{
              left: 12,
              right: 12,
            }}
          >
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              tickFormatter={(value) => value.slice(0, 3)}
            />
            <ChartTooltip
              cursor={false}
              content={<ChartTooltipContent indicator="line" />}
            />
            <Area
              dataKey="desktop"
              type="natural"
              fill="#6b7280"
              fillOpacity={0.2}
              stroke="#6b7280"
              strokeWidth={2}
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
      <CardFooter>
        <div className="flex w-full items-start gap-2 text-sm">
          <div className="grid gap-2">
            <div className="flex items-center gap-2 leading-none font-medium">
              Trending {parseFloat(trendPercentage) >= 0 ? 'up' : 'down'} by {Math.abs(parseFloat(trendPercentage))}% this month 
              <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-muted-foreground flex items-center gap-2 leading-none">
              January - June 2024
            </div>
          </div>
        </div>
      </CardFooter>
    </Card>
  )
}