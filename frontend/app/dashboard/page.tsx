'use client';

/**
 * Dashboard page for creating benchmark runs
 * Provides a form interface to trigger new benchmarks via the API
 */

import { useState } from 'react';
import { BenchmarkForm } from '@/components/forms/BenchmarkForm';
import { LoadingOverlay } from '@/components/LoadingOverlay';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, Info, CheckCircle2 } from 'lucide-react';
import { ContactIcons } from '@/components/ui/ContactIcons';

export default function DashboardPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);

  const handleSubmitStart = () => {
    setIsRunning(true);
    setShowSuccess(false);
  };

  const handleSubmitEnd = () => {
    setIsRunning(false);
    setShowSuccess(true);
  };

  return (
    <div className="container max-w-3xl py-8">
      <LoadingOverlay
        isOpen={isRunning}
        message="Running Benchmark..."
        submessage="This may take 1-5 minutes depending on your configuration. Please wait."
      />

      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Run Benchmark</h1>
          <p className="text-muted-foreground mt-2">
            Create a new benchmark run to compare RAG providers
          </p>
        </div>

        {/* Success Message */}
        {showSuccess && (
          <Alert className="border-green-500 bg-green-50">
            <CheckCircle2 className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-900">Benchmark Completed!</AlertTitle>
            <AlertDescription className="text-green-800">
              Redirecting to results page...
            </AlertDescription>
          </Alert>
        )}

        {/* Warning Banner */}
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Important: Test with Small Values!</AlertTitle>
          <AlertDescription>
            Use <strong>1-2 documents</strong> for testing. Full datasets can take hours to
            complete. The benchmark runs synchronously and will block until finished.
          </AlertDescription>
        </Alert>

        {/* Info Card */}
        <Alert>
          <Info className="h-4 w-4" />
          <AlertTitle>How it works</AlertTitle>
          <AlertDescription>
            <ul className="mt-2 space-y-1 list-disc list-inside text-sm">
              <li>Select a dataset and providers to benchmark</li>
              <li>Configure the number of documents and questions</li>
              <li>Provide your API key for authentication</li>
              <li>Submit to start the benchmark execution</li>
              <li>You’ll be redirected to the results page when complete</li>
            </ul>
          </AlertDescription>
        </Alert>

        {/* Form Card */}
        <Card>
          <CardHeader>
            <CardTitle>Benchmark Configuration</CardTitle>
            <CardDescription>
              Configure your benchmark run below. All fields are required.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <BenchmarkForm
              onSubmitStart={handleSubmitStart}
              onSubmitEnd={handleSubmitEnd}
            />
          </CardContent>
        </Card>

        {/* Additional Info */}
        <div className="text-sm text-muted-foreground space-y-2">
          <p>
            <strong>Note:</strong> The backend currently runs benchmarks synchronously. Your
            request will wait until the benchmark completes before returning results.
          </p>
          <p>
            <strong>Estimated times:</strong>
          </p>
          <ul className="list-disc list-inside ml-4 space-y-1">
            <li>1 doc, 1 provider, 2 questions: ~2-3 minutes</li>
            <li>2 docs, 1 provider, 3 questions: ~3-5 minutes</li>
            <li>5+ docs or 2+ providers: 10+ minutes (not recommended for testing)</li>
          </ul>
        </div>
      </div>

      <ContactIcons />
    </div>
  );
}
