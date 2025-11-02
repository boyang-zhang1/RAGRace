'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { AxisDomain } from 'recharts/types/util/types';
import { TrendingUp } from 'lucide-react';
import type { ProviderPerformance } from '@/types/api';

interface DatasetPerformanceCardProps {
  datasetName: string;
  providers: ProviderPerformance[];
  totalDocuments: number;
  totalRuns: number;
  embedded?: boolean; // New prop to control card wrapper
}

export function DatasetPerformanceCard({
  datasetName,
  providers,
  totalDocuments,
  totalRuns,
  embedded = false,
}: DatasetPerformanceCardProps) {
  // Get all unique metric names and reorder (Duration Seconds last)
  const allMetrics = Array.from(
    new Set(
      providers.flatMap((p) => Object.keys(p.aggregated_scores))
    )
  );

  // Separate duration metrics from others
  const durationMetrics = allMetrics.filter(
    (m) => m.toLowerCase().includes('duration') || m.toLowerCase().includes('seconds')
  );
  const otherMetrics = allMetrics.filter(
    (m) => !m.toLowerCase().includes('duration') && !m.toLowerCase().includes('seconds')
  );

  // Reorder: other metrics first, then duration metrics
  const metricNames = [...otherMetrics.sort(), ...durationMetrics.sort()];

  // Find primary metric for chart
  const primaryMetric = findPrimaryMetric(providers);
  const [selectedMetric, setSelectedMetric] = useState<string>(primaryMetric);

  // Sort providers by selected metric (descending for scores, ascending for duration)
  const isDurationMetric =
    selectedMetric.toLowerCase().includes('duration') ||
    selectedMetric.toLowerCase().includes('seconds');

  const sortedProviders = [...providers].sort((a, b) => {
    const scoreA = a.aggregated_scores[selectedMetric] ?? (isDurationMetric ? Infinity : -Infinity);
    const scoreB = b.aggregated_scores[selectedMetric] ?? (isDurationMetric ? Infinity : -Infinity);
    // For duration: lower is better (ascending)
    // For scores: higher is better (descending)
    return isDurationMetric ? scoreA - scoreB : scoreB - scoreA;
  });

  // Calculate best value for each metric (for bolding)
  const bestValues = metricNames.reduce((acc, metric) => {
    const values = providers
      .map((p) => p.aggregated_scores[metric])
      .filter((v) => v !== undefined && v !== null) as number[];

    if (values.length > 0) {
      const isMetricDuration =
        metric.toLowerCase().includes('duration') || metric.toLowerCase().includes('seconds');
      // For duration: lowest is best, for scores: highest is best
      acc[metric] = isMetricDuration ? Math.min(...values) : Math.max(...values);
    }
    return acc;
  }, {} as Record<string, number>);

  // Prepare chart data
  const chartData = sortedProviders.map((p) => ({
    provider: p.provider,
    score: p.aggregated_scores[selectedMetric] ?? 0,
  }));

  // Calculate dynamic Y-axis domain with padding
  const scores = chartData.map((d) => d.score).filter((s) => !isNaN(s) && isFinite(s));
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);
  const range = maxScore - minScore;
  const padding = range * 0.1; // 10% padding

  const yAxisDomain: AxisDomain = [
    Math.max(0, minScore - padding),
    maxScore + padding,
  ] as const;

  const content = (
    <>
      {!embedded && (
        <CardHeader>
          <div className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <CardTitle>Provider Performance History</CardTitle>
          </div>
          <CardDescription>
            Aggregated across {totalDocuments} documents from {totalRuns} benchmark runs
          </CardDescription>
        </CardHeader>
      )}
      <CardContent className={embedded ? 'px-0' : ''}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Metrics Table */}
          <div>
            {metricNames.length > 0 && (
              <div>
                <h4 className="text-sm font-medium mb-3">Average Metrics</h4>
                <div className="rounded-md border overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/50">
                        <th className="px-3 py-2 text-left font-medium sticky left-0 bg-muted/50">
                          Provider
                        </th>
                        {metricNames.map((metric) => (
                          <th
                            key={metric}
                            className="px-3 py-2 text-left font-medium whitespace-nowrap"
                          >
                            {formatMetricName(metric)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sortedProviders.map((provider) => (
                        <tr key={provider.provider} className="border-b last:border-0">
                          <td className="px-3 py-2 font-medium sticky left-0 bg-background">
                            {provider.provider}
                          </td>
                          {metricNames.map((metric) => {
                            const value = provider.aggregated_scores[metric];
                            const isBest =
                              value !== undefined &&
                              bestValues[metric] !== undefined &&
                              Math.abs(value - bestValues[metric]) < 0.0001;

                            return (
                              <td
                                key={metric}
                                className={`px-3 py-2 text-muted-foreground tabular-nums ${
                                  isBest ? 'font-bold text-foreground' : ''
                                }`}
                              >
                                {formatScore(value)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Right: Chart */}
          <div>
            <h4 className="text-sm font-medium mb-3">
              {formatMetricName(selectedMetric)} Comparison
            </h4>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="provider"
                    angle={-45}
                    textAnchor="end"
                    height={80}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    domain={yAxisDomain}
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => value.toFixed(2)}
                    label={{
                      value: isDurationMetric ? 'Seconds' : 'Score',
                      angle: -90,
                      position: 'insideLeft',
                    }}
                  />
                  <Tooltip
                    formatter={(value: number) => {
                      if (isDurationMetric) {
                        return `${value.toFixed(2)}s`;
                      }
                      return value.toFixed(3);
                    }}
                    contentStyle={{
                      backgroundColor: 'hsl(var(--background))',
                      border: '1px solid hsl(var(--border))',
                      borderRadius: '6px',
                    }}
                  />
                  <Legend wrapperStyle={{ paddingTop: '20px' }} />
                  <Bar
                    dataKey="score"
                    fill="hsl(var(--primary))"
                    name={formatMetricName(selectedMetric)}
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Metric Selection Buttons */}
            {metricNames.length > 0 && (
              <div className="mt-4">
                <p className="text-xs text-muted-foreground mb-2">
                  Select metric to compare:
                </p>
                <div className="flex flex-wrap gap-2">
                  {metricNames.map((metric) => (
                    <Button
                      key={metric}
                      size="sm"
                      variant={selectedMetric === metric ? 'default' : 'outline'}
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setSelectedMetric(metric);
                      }}
                      className="text-xs"
                    >
                      {formatMetricName(metric)}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </>
  );

  return embedded ? content : <Card>{content}</Card>;
}

/**
 * Find the primary metric for chart visualization
 */
function findPrimaryMetric(providers: ProviderPerformance[]): string {
  if (providers.length === 0) return '';

  const preferredMetrics = [
    'factual_correctness(mode=f1)',
    'faithfulness',
    'context_recall',
  ];

  for (const metric of preferredMetrics) {
    if (providers.some((p) => p.aggregated_scores[metric] !== undefined)) {
      return metric;
    }
  }

  // Fallback to first available metric
  const firstProvider = providers[0];
  const metrics = Object.keys(firstProvider.aggregated_scores);
  return metrics[0] || '';
}

/**
 * Format metric name for display
 */
function formatMetricName(metric: string): string {
  // Remove (mode=f1) suffix for brevity
  const cleaned = metric.replace(/\(mode=[^)]+\)/g, '');

  // Convert snake_case to Title Case
  return cleaned
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format score for display
 */
function formatScore(score: number | undefined): string {
  if (score === undefined || score === null) return '-';
  return score.toFixed(3);
}
