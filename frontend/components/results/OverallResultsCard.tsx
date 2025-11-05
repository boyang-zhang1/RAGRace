'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProviderLabel } from '@/components/providers/ProviderLabel';
import {
  calculateOverallScores,
  sortProvidersByMetric,
  getAllMetricNames,
  formatScore,
  type ProviderOverallScores,
} from '@/lib/aggregateScores';
import type { DocumentResult } from '@/types/api';
import { getProviderDisplayName } from '@/lib/providerMetadata';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { AxisDomain } from 'recharts/types/util/types';
import { TrendingUp } from 'lucide-react';

interface OverallResultsCardProps {
  documents: DocumentResult[];
  providers: string[];
}

export function OverallResultsCard({ documents, providers }: OverallResultsCardProps) {
  // Calculate overall scores
  const overallScores = calculateOverallScores(documents, providers);
  const sortedScores = sortProvidersByMetric(overallScores);
  const metricNames = getAllMetricNames(sortedScores);

  // State for selected metric in chart
  const primaryMetric = findPrimaryMetric(sortedScores);
  const [selectedMetric, setSelectedMetric] = useState<string>(primaryMetric);

  // Determine if the selected metric is duration-based
  const isDurationMetric = selectedMetric.toLowerCase().includes('duration') ||
                          selectedMetric.toLowerCase().includes('seconds');

  // Re-sort providers based on selected metric
  const sortedByMetric = [...sortedScores].sort((a, b) => {
    const scoreA = a.averageScores[selectedMetric] ?? (isDurationMetric ? Infinity : -Infinity);
    const scoreB = b.averageScores[selectedMetric] ?? (isDurationMetric ? Infinity : -Infinity);
    // For duration: lower is better (ascending)
    // For scores: higher is better (descending)
    return isDurationMetric ? scoreA - scoreB : scoreB - scoreA;
  });

  // Calculate best value for each metric (for bolding)
  const bestValues = metricNames.reduce((acc, metric) => {
    const values = sortedScores
      .map((p) => p.averageScores[metric])
      .filter((v) => v !== undefined && v !== null && !isNaN(v)) as number[];

    if (values.length > 0) {
      const isMetricDuration =
        metric.toLowerCase().includes('duration') || metric.toLowerCase().includes('seconds');
      // For duration: lowest is best, for scores: highest is best
      acc[metric] = isMetricDuration ? Math.min(...values) : Math.max(...values);
    }
    return acc;
  }, {} as Record<string, number>);

  // Prepare chart data for selected metric
  const chartData = sortedByMetric.map(p => ({
    provider: getProviderDisplayName(p.provider),
    score: p.averageScores[selectedMetric] ?? 0,
  }));

  // Calculate dynamic Y-axis domain with padding
  const scores = chartData.map((d) => d.score).filter((s) => !isNaN(s) && isFinite(s));
  const minScore = Math.min(...scores);
  const maxScore = Math.max(...scores);
  const range = maxScore - minScore;

  // Use 10% padding, or 20% of max value if range is 0 (single provider)
  const padding = range > 0 ? range * 0.1 : maxScore * 0.2;

  const yAxisDomain: AxisDomain = [
    Math.max(0, minScore - padding),
    maxScore + padding,
  ] as const;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-primary" />
          <CardTitle>Overall Results</CardTitle>
        </div>
        <CardDescription>
          Aggregated scores across all {documents.length} document{documents.length !== 1 ? 's' : ''}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Metrics Table */}
          <div>
            <h4 className="text-sm font-medium mb-3">Average Metrics</h4>
            <div className="rounded-md border overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="px-3 py-2 text-left font-medium sticky left-0 bg-muted/50">Provider</th>
                    {metricNames.map(metric => (
                      <th key={metric} className="px-3 py-2 text-left font-medium whitespace-nowrap">
                        {formatMetricName(metric)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {sortedByMetric.map(result => (
                    <tr key={result.provider} className="border-b last:border-0">
                      <td className="px-3 py-2 font-medium sticky left-0 bg-background">
                        <ProviderLabel provider={result.provider} />
                      </td>
                      {metricNames.map(metric => {
                        const value = result.averageScores[metric];
                        const isBest =
                          value !== undefined &&
                          !isNaN(value) &&
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

          {/* Right: Chart */}
          <div>
            <h4 className="text-sm font-medium mb-3">
              {formatMetricName(selectedMetric)} Comparison
            </h4>
            <div className="w-full">
              <ResponsiveContainer width="100%" height={300}>
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
                      position: 'insideLeft'
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
            <div className="mt-4">
              <p className="text-xs text-muted-foreground mb-2">Select metric to compare:</p>
              <div className="flex flex-wrap gap-2">
                {metricNames.map(metric => (
                  <Button
                    key={metric}
                    size="sm"
                    variant={selectedMetric === metric ? 'default' : 'outline'}
                    onClick={() => setSelectedMetric(metric)}
                    className="text-xs"
                  >
                    {formatMetricName(metric)}
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Find the primary metric to use for chart visualization
 * Prefers factual_correctness, then faithfulness, then first available
 */
function findPrimaryMetric(scores: ProviderOverallScores[]): string {
  if (scores.length === 0) return '';

  const preferredMetrics = ['factual_correctness(mode=f1)', 'faithfulness', 'context_recall'];

  for (const metric of preferredMetrics) {
    if (scores.some(p => p.averageScores[metric] !== undefined)) {
      return metric;
    }
  }

  // Fallback to first available metric
  const firstProvider = scores[0];
  const metrics = Object.keys(firstProvider.averageScores);
  return metrics[0] || '';
}

/**
 * Format metric name for display (shorten common patterns)
 */
function formatMetricName(metric: string): string {
  // Remove (mode=f1) suffix for brevity
  const cleaned = metric.replace(/\(mode=[^)]+\)/g, '');

  // Convert snake_case to Title Case
  return cleaned
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
