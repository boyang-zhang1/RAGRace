import { Suspense } from 'react';
import { apiClient } from '@/lib/api-client';
import Link from 'next/link';
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ResultsTable } from '@/components/results/ResultsTable';
import { Skeleton } from '@/components/ui/skeleton';

async function DatasetsList() {
  try {
    const datasets = await apiClient.getDatasets();

    return (
      <div className="space-y-8">
        {datasets.map((dataset) => (
          <Link key={dataset.name} href={`/datasets/${dataset.name}`}>
            <Card className="hover:bg-muted/50 transition-colors cursor-pointer">
              {/* Dataset Header */}
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-2xl hover:text-primary transition-colors">
                      {dataset.display_name}
                    </CardTitle>
                    <CardDescription className="mt-1">{dataset.description}</CardDescription>
                  </div>
                  <Badge variant="outline" className="ml-4">
                    {dataset.task_type}
                  </Badge>
                </div>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    );
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Datasets</h2>
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : 'Failed to load datasets'}
        </p>
      </div>
    );
  }
}

async function ResultsList() {
  try {
    const data = await apiClient.getResults({ limit: 50 });

    return (
      <div>
        <ResultsTable runs={data.runs} />
        {data.total > 0 && (
          <div className="text-sm text-muted-foreground mt-4 text-center">
            Showing {data.runs.length} of {data.total} {data.total === 1 ? 'run' : 'runs'}
          </div>
        )}
      </div>
    );
  } catch (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-destructive mb-2">Error Loading Results</h2>
        <p className="text-muted-foreground">
          {error instanceof Error ? error.message : 'Failed to load benchmark results'}
        </p>
        <p className="text-sm text-muted-foreground mt-4">
          Make sure the backend API is running at{' '}
          <code className="bg-muted px-2 py-1 rounded">
            {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
          </code>
        </p>
      </div>
    );
  }
}

function DatasetsLoading() {
  return (
    <div className="space-y-8">
      {[...Array(3)].map((_, i) => (
        <Skeleton key={i} className="h-24 w-full" />
      ))}
    </div>
  );
}

function ResultsLoading() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <Skeleton key={i} className="h-16 w-full" />
      ))}
    </div>
  );
}

export default function DatasetsPage() {
  return (
    <div>
      {/* Datasets Section */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight">Datasets</h1>
        <p className="text-muted-foreground mt-2">
          Available datasets for RAG benchmarking
        </p>
      </div>

      <Suspense fallback={<DatasetsLoading />}>
        <DatasetsList />
      </Suspense>

      {/* Divider */}
      <div className="my-12 border-t pt-12">
        <div className="mb-6">
          <h2 className="text-3xl font-bold tracking-tight">Benchmark Results</h2>
          <p className="text-muted-foreground mt-2">
            Browse and compare RAG provider benchmark results
          </p>
        </div>

        <Suspense fallback={<ResultsLoading />}>
          <ResultsList />
        </Suspense>
      </div>
    </div>
  );
}
