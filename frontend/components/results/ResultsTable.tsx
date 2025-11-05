'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ProviderLabel } from '@/components/providers/ProviderLabel';
import type { RunSummary } from '@/types/api';

interface ResultsTableProps {
  runs: RunSummary[];
}

export function ResultsTable({ runs }: ResultsTableProps) {
  const router = useRouter();

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds.toFixed(0)}s`;
  };

  if (runs.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No benchmark runs found.</p>
      </div>
    );
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Run ID</TableHead>
            <TableHead>Dataset</TableHead>
            <TableHead>Providers</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Docs</TableHead>
            <TableHead className="text-right">Questions</TableHead>
            <TableHead>Started</TableHead>
            <TableHead className="text-right">Duration</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => (
            <TableRow
              key={run.run_id}
              className="cursor-pointer hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/70"
              onClick={() => router.push(`/results/${run.run_id}`)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault();
                  router.push(`/results/${run.run_id}`);
                }
              }}
              role="button"
              tabIndex={0}
            >
              <TableCell>
                <Link
                  href={`/results/${run.run_id}`}
                  className="font-medium text-primary hover:underline"
                >
                  {run.run_id}
                </Link>
              </TableCell>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">{run.dataset}</span>
                  <span className="text-xs text-muted-foreground">{run.split}</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {run.providers.map((provider) => (
                    <Badge key={provider} variant="outline" className="gap-1.5">
                      <ProviderLabel
                        provider={provider}
                        size={14}
                        nameClassName="text-xs font-semibold"
                      />
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant={getStatusBadgeVariant(run.status)}>
                  {run.status}
                </Badge>
              </TableCell>
              <TableCell className="text-right">{run.num_docs}</TableCell>
              <TableCell className="text-right">{run.num_questions}</TableCell>
              <TableCell>
                <div className="flex flex-col">
                  <span className="text-sm">
                    {format(new Date(run.started_at), 'MMM d, yyyy')}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {format(new Date(run.started_at), 'HH:mm:ss')}
                  </span>
                </div>
              </TableCell>
              <TableCell className="text-right">
                {formatDuration(run.duration_seconds)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
