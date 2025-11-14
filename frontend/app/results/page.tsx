import { Suspense } from 'react';
import { apiClient } from '@/lib/api-client';
import { ResultsTable } from '@/components/results/ResultsTable';
import { Skeleton } from '@/components/ui/skeleton';
import { ContactIcons } from '@/components/ui/ContactIcons';

async function ResultsList() {
  try {
    const data = await apiClient.getResults({ limit: 50 });

    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Benchmark Results</h1>
            <p className="text-muted-foreground mt-2">
              Browse and compare RAG provider benchmark results
            </p>
          </div>
          <div className="text-sm text-muted-foreground">
            {data.total} {data.total === 1 ? 'run' : 'runs'} found
          </div>
        </div>

        <ResultsTable runs={data.runs} />
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

function ResultsLoading() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-4 w-96" />
        </div>
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-2">
        {[...Array(5)].map((_, i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    </div>
  );
}

export default function ResultsPage() {
  return (
    <>
      <Suspense fallback={<ResultsLoading />}>
        <ResultsList />
      </Suspense>
      <ContactIcons />
    </>
  );
}
