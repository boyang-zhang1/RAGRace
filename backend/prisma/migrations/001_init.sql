-- CreateEnum
CREATE TYPE "UserType" AS ENUM ('PAID', 'FREE');

-- CreateEnum
CREATE TYPE "BenchmarkStatus" AS ENUM ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED');

-- CreateEnum
CREATE TYPE "ProviderStatus" AS ENUM ('SUCCESS', 'ERROR');

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "api_key" TEXT NOT NULL,
    "user_type" "UserType" NOT NULL,
    "credits_remaining" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "benchmark_runs" (
    "id" TEXT NOT NULL,
    "run_id" TEXT NOT NULL,
    "user_id" TEXT,
    "dataset_name" TEXT NOT NULL,
    "dataset_split" TEXT NOT NULL,
    "providers" TEXT[],
    "num_docs" INTEGER NOT NULL,
    "num_questions_total" INTEGER NOT NULL,
    "status" "BenchmarkStatus" NOT NULL,
    "config" JSONB NOT NULL,
    "duration_seconds" DOUBLE PRECISION,
    "error_message" TEXT,
    "started_at" TIMESTAMP(3) NOT NULL,
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "benchmark_runs_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "documents" (
    "id" TEXT NOT NULL,
    "doc_id" TEXT NOT NULL,
    "dataset_name" TEXT NOT NULL,
    "doc_title" TEXT NOT NULL,
    "pdf_path" TEXT,
    "pdf_url" TEXT,
    "pdf_size_bytes" BIGINT,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "documents_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "questions" (
    "id" TEXT NOT NULL,
    "question_id" TEXT NOT NULL,
    "document_id" TEXT NOT NULL,
    "question" TEXT NOT NULL,
    "ground_truth" TEXT NOT NULL,
    "metadata" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "questions_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "provider_results" (
    "id" TEXT NOT NULL,
    "run_id" TEXT NOT NULL,
    "document_id" TEXT NOT NULL,
    "provider" TEXT NOT NULL,
    "status" "ProviderStatus" NOT NULL,
    "error" TEXT,
    "index_id" TEXT,
    "aggregated_scores" JSONB NOT NULL DEFAULT '{}',
    "duration_seconds" DOUBLE PRECISION,
    "started_at" TIMESTAMP(3),
    "completed_at" TIMESTAMP(3),
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "provider_results_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "question_results" (
    "id" TEXT NOT NULL,
    "provider_result_id" TEXT NOT NULL,
    "question_id" TEXT NOT NULL,
    "response_answer" TEXT NOT NULL,
    "response_context" TEXT[] DEFAULT ARRAY[]::TEXT[],
    "response_latency_ms" DOUBLE PRECISION,
    "response_metadata" JSONB NOT NULL DEFAULT '{}',
    "evaluation_scores" JSONB NOT NULL DEFAULT '{}',
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "question_results_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "api_requests" (
    "id" TEXT NOT NULL,
    "user_id" TEXT NOT NULL,
    "endpoint" TEXT NOT NULL,
    "method" TEXT NOT NULL,
    "status_code" INTEGER,
    "credits_used" INTEGER NOT NULL DEFAULT 0,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "api_requests_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE UNIQUE INDEX "users_api_key_key" ON "users"("api_key");

-- CreateIndex
CREATE INDEX "users_api_key_idx" ON "users"("api_key");

-- CreateIndex
CREATE UNIQUE INDEX "benchmark_runs_run_id_key" ON "benchmark_runs"("run_id");

-- CreateIndex
CREATE INDEX "benchmark_runs_user_id_idx" ON "benchmark_runs"("user_id");

-- CreateIndex
CREATE INDEX "benchmark_runs_status_idx" ON "benchmark_runs"("status");

-- CreateIndex
CREATE INDEX "benchmark_runs_dataset_name_dataset_split_idx" ON "benchmark_runs"("dataset_name", "dataset_split");

-- CreateIndex
CREATE INDEX "documents_dataset_name_idx" ON "documents"("dataset_name");

-- CreateIndex
CREATE UNIQUE INDEX "documents_doc_id_dataset_name_key" ON "documents"("doc_id", "dataset_name");

-- CreateIndex
CREATE INDEX "questions_document_id_idx" ON "questions"("document_id");

-- CreateIndex
CREATE UNIQUE INDEX "questions_question_id_document_id_key" ON "questions"("question_id", "document_id");

-- CreateIndex
CREATE INDEX "provider_results_run_id_idx" ON "provider_results"("run_id");

-- CreateIndex
CREATE INDEX "provider_results_document_id_idx" ON "provider_results"("document_id");

-- CreateIndex
CREATE UNIQUE INDEX "provider_results_run_id_document_id_provider_key" ON "provider_results"("run_id", "document_id", "provider");

-- CreateIndex
CREATE INDEX "question_results_provider_result_id_idx" ON "question_results"("provider_result_id");

-- CreateIndex
CREATE UNIQUE INDEX "question_results_provider_result_id_question_id_key" ON "question_results"("provider_result_id", "question_id");

-- CreateIndex
CREATE INDEX "api_requests_user_id_idx" ON "api_requests"("user_id");

-- CreateIndex
CREATE INDEX "api_requests_created_at_idx" ON "api_requests"("created_at");

-- AddForeignKey
ALTER TABLE "benchmark_runs" ADD CONSTRAINT "benchmark_runs_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "questions" ADD CONSTRAINT "questions_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "provider_results" ADD CONSTRAINT "provider_results_run_id_fkey" FOREIGN KEY ("run_id") REFERENCES "benchmark_runs"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "provider_results" ADD CONSTRAINT "provider_results_document_id_fkey" FOREIGN KEY ("document_id") REFERENCES "documents"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "question_results" ADD CONSTRAINT "question_results_provider_result_id_fkey" FOREIGN KEY ("provider_result_id") REFERENCES "provider_results"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "question_results" ADD CONSTRAINT "question_results_question_id_fkey" FOREIGN KEY ("question_id") REFERENCES "questions"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "api_requests" ADD CONSTRAINT "api_requests_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users"("id") ON DELETE CASCADE ON UPDATE CASCADE;

