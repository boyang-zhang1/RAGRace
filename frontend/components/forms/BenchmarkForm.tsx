'use client';

/**
 * Benchmark Form Component
 * Form to create and submit new benchmark runs with provider API keys
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import type { BenchmarkRequest } from '@/types/api';
import { apiClient } from '@/lib/api-client';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Slider } from '@/components/ui/slider';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle } from 'lucide-react';
import { ProviderLabel } from '@/components/providers/ProviderLabel';

// Available options
const DATASETS = [
  { value: 'qasper', label: 'Qasper (Scientific Papers)' },
  { value: 'policyqa', label: 'PolicyQA (Policy Documents)' },
  { value: 'squad2', label: 'SQuAD 2.0 (Wikipedia)' },
];

const PROVIDERS = [
  { value: 'llamaindex', label: 'LlamaIndex', description: 'General-purpose RAG framework' },
  { value: 'landingai', label: 'LandingAI', description: 'Document AI platform' },
  { value: 'reducto', label: 'Reducto', description: 'Document processing API' },
];

interface BenchmarkFormProps {
  onSubmitStart?: () => void;
  onSubmitEnd?: () => void;
}

export function BenchmarkForm({ onSubmitStart, onSubmitEnd }: BenchmarkFormProps) {
  const router = useRouter();

  // Form state
  const [dataset, setDataset] = useState('qasper');
  const [selectedProviders, setSelectedProviders] = useState<string[]>(['llamaindex']);
  const [maxDocs, setMaxDocs] = useState<number[]>([2]);
  const [maxQuestions, setMaxQuestions] = useState<number[]>([3]);
  const [filterUnanswerable, setFilterUnanswerable] = useState(true);

  // API Keys state (user provides their own keys)
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    openai: '',
    llamaindex: '',
    landingai: '',  // Note: landingai and vision_agent are the same key
    reducto: '',
  });

  // UI state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Determine which API keys are needed based on selected providers
  const needsOpenAI = selectedProviders.length > 0;  // All providers need OpenAI
  const needsLlamaIndex = selectedProviders.includes('llamaindex');
  const needsLandingAI = selectedProviders.includes('landingai');
  const needsReducto = selectedProviders.includes('reducto');

  // Validation: check required API keys are filled
  const hasRequiredKeys = () => {
    if (needsOpenAI && !apiKeys.openai.trim()) return false;
    if (needsLlamaIndex && !apiKeys.llamaindex.trim()) return false;
    if (needsLandingAI && !apiKeys.landingai.trim()) return false;
    if (needsReducto && !apiKeys.reducto.trim()) return false;
    return true;
  };

  const canSubmit = selectedProviders.length > 0 && hasRequiredKeys();

  const handleProviderToggle = (provider: string, checked: boolean) => {
    setSelectedProviders((prev) =>
      checked ? [...prev, provider] : prev.filter((p) => p !== provider)
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!canSubmit) {
      setError('Please select at least one provider and provide all required API keys');
      return;
    }

    try {
      setIsSubmitting(true);
      onSubmitStart?.();

      // Build api_keys object with only needed keys
      const requestApiKeys: Record<string, string> = {
        openai: apiKeys.openai,
      };

      if (needsLlamaIndex) {
        requestApiKeys.llamaindex = apiKeys.llamaindex;
      }
      if (needsLandingAI) {
        // Use same key for both vision_agent and landingai
        requestApiKeys.vision_agent = apiKeys.landingai;
      }
      if (needsReducto) {
        requestApiKeys.reducto = apiKeys.reducto;
      }

      const request: BenchmarkRequest = {
        dataset,
        split: 'train',  // Always use 'train' split
        providers: selectedProviders,
        max_docs: maxDocs[0],  // Extract number from slider array
        max_questions_per_doc: maxQuestions[0],  // Extract number from slider array
        filter_unanswerable: filterUnanswerable,
        api_keys: requestApiKeys,
      };

      console.log('Sending benchmark request:', JSON.stringify(request, null, 2));

      // Note: No X-API-Key header needed - user provides provider keys directly
      const response = await apiClient.createBenchmark(request, '');

      // End loading state (form stays on screen briefly)
      setIsSubmitting(false);

      // Redirect to results page immediately
      router.push(`/results/${response.run_id}`);
    } catch (err) {
      console.error('Benchmark submission failed:', err);
      setError(err instanceof Error ? err.message : 'Failed to create benchmark');
      setIsSubmitting(false);
      onSubmitEnd?.();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Dataset Selection */}
      <div className="space-y-2">
        <Label htmlFor="dataset">Dataset</Label>
        <Select value={dataset} onValueChange={setDataset}>
          <SelectTrigger id="dataset">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DATASETS.map((ds) => (
              <SelectItem key={ds.value} value={ds.value}>
                {ds.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Provider Selection */}
      <div className="space-y-3">
        <Label>Providers (select at least one)</Label>
        <div className="space-y-2">
          {PROVIDERS.map((provider) => (
            <div key={provider.value} className="flex items-start space-x-3">
              <Checkbox
                id={provider.value}
                checked={selectedProviders.includes(provider.value)}
                onCheckedChange={(checked) =>
                  handleProviderToggle(provider.value, checked as boolean)
                }
              />
              <div className="grid gap-1.5 leading-none">
                <label
                  htmlFor={provider.value}
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  <ProviderLabel
                    provider={provider.value}
                    size={18}
                    className="gap-2"
                    nameClassName="text-sm font-medium"
                  />
                </label>
                <p className="text-sm text-muted-foreground">
                  {provider.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* API Keys Section - Dynamic based on selected providers */}
      {selectedProviders.length > 0 && (
        <div className="space-y-4 border-t pt-4">
          <div>
            <Label className="text-base font-semibold">API Keys (Required)</Label>
            <p className="text-sm text-muted-foreground mt-1">
              Provide your own API keys for the selected providers
            </p>
          </div>

          {/* OpenAI API Key - always shown if any provider selected */}
          <div className="space-y-2">
            <Label htmlFor="openai-key">OpenAI API Key *</Label>
            <Input
              id="openai-key"
              type="password"
              placeholder="sk-..."
              value={apiKeys.openai}
              onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
              disabled={isSubmitting}
            />
            <p className="text-xs text-muted-foreground">
              Used for embeddings and LLM (required by all providers)
            </p>
          </div>

          {/* LlamaIndex API Key */}
          {needsLlamaIndex && (
            <div className="space-y-2">
              <Label htmlFor="llamaindex-key">LlamaIndex API Key *</Label>
              <Input
                id="llamaindex-key"
                type="password"
                placeholder="llx-..."
                value={apiKeys.llamaindex}
                onChange={(e) => setApiKeys({ ...apiKeys, llamaindex: e.target.value })}
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                LlamaCloud API key for LlamaParse
              </p>
            </div>
          )}

          {/* LandingAI API Key */}
          {needsLandingAI && (
            <div className="space-y-2">
              <Label htmlFor="landingai-key">LandingAI API Key *</Label>
              <Input
                id="landingai-key"
                type="password"
                placeholder="your-landing-ai-key"
                value={apiKeys.landingai}
                onChange={(e) => setApiKeys({ ...apiKeys, landingai: e.target.value })}
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                LandingAI Vision Agent API key
              </p>
            </div>
          )}

          {/* Reducto API Key */}
          {needsReducto && (
            <div className="space-y-2">
              <Label htmlFor="reducto-key">Reducto API Key *</Label>
              <Input
                id="reducto-key"
                type="password"
                placeholder="your-reducto-key"
                value={apiKeys.reducto}
                onChange={(e) => setApiKeys({ ...apiKeys, reducto: e.target.value })}
                disabled={isSubmitting}
              />
              <p className="text-xs text-muted-foreground">
                Reducto service API key
              </p>
            </div>
          )}
        </div>
      )}

      {/* Max Documents */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="max-docs">Max Documents</Label>
          <span className="text-sm text-muted-foreground">
            {maxDocs[0]} document{maxDocs[0] !== 1 ? 's' : ''}
          </span>
        </div>
        <Slider
          id="max-docs"
          min={1}
          max={10}
          step={1}
          value={maxDocs}
          onValueChange={setMaxDocs}
          className="w-full"
          disabled={isSubmitting}
        />
        <p className="text-xs text-muted-foreground">
          ⚠️ Use 1-2 docs for testing! More docs = longer execution time.
        </p>
      </div>

      {/* Max Questions */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <Label htmlFor="max-questions">Max Questions per Document</Label>
          <span className="text-sm text-muted-foreground">
            {maxQuestions[0]} question{maxQuestions[0] !== 1 ? 's' : ''}
          </span>
        </div>
        <Slider
          id="max-questions"
          min={1}
          max={20}
          step={1}
          value={maxQuestions}
          onValueChange={setMaxQuestions}
          className="w-full"
          disabled={isSubmitting}
        />
      </div>

      {/* Filter Unanswerable */}
      <div className="flex items-center space-x-2">
        <Checkbox
          id="filter-unanswerable"
          checked={filterUnanswerable}
          onCheckedChange={(checked) => setFilterUnanswerable(checked as boolean)}
          disabled={isSubmitting}
        />
        <label
          htmlFor="filter-unanswerable"
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          Filter unanswerable questions
        </label>
      </div>

      {/* Submit Button */}
      <Button type="submit" disabled={!canSubmit || isSubmitting} className="w-full">
        {isSubmitting ? 'Running Benchmark...' : 'Run Benchmark'}
      </Button>

      {!canSubmit && selectedProviders.length > 0 && (
        <p className="text-sm text-muted-foreground text-center">
          Please provide all required API keys to continue
        </p>
      )}
    </form>
  );
}
