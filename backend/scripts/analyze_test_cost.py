#!/usr/bin/env python3
"""
Analyze the cost of the comprehensive 3-provider RAG evaluation test.

Based on the test run from CP4 extended evaluation.
"""

from src.utils.cost_tracker import CostReport, ProviderCost, EvaluationCost, estimate_tokens


def analyze_cp4_comprehensive_test():
    """
    Analyze costs from test_all_providers_comparison test.

    Test details:
    - 3 providers: LlamaIndex, LandingAI, Reducto
    - 1 document: Beyoncé context (694 chars)
    - 2 questions about Beyoncé
    - 3 Ragas metrics: Faithfulness, ContextRecall, FactualCorrectness
    """

    # Test data
    context_text = "Beyoncé Giselle Knowles-Carter (/biːˈjɒnseɪ/ bee-YON-say) (born September 4, 1981) is an American singer, songwriter, record producer and actress. Born and raised in Houston, Texas, she performed in various singing and dancing competitions as a child, and rose to fame in the late 1990s as lead singer of R&B girl-group Destiny's Child. Managed by her father, Mathew Knowles, the group became one of the world's best-selling girl groups of all time. Their hiatus saw the release of Beyoncé's debut album, Dangerously in Love (2003), which established her as a solo artist worldwide, earned five Grammy Awards and featured the Billboard Hot 100 number-one singles \"Crazy in Love\" and \"Baby Boy\"."

    questions = [
        "When did Beyonce start becoming popular?",
        "What areas did Beyonce compete in when she was growing up?"
    ]

    # Typical answers (from test output)
    answers = [
        "Beyoncé started becoming popular in the late 1990s as the lead singer of the R&B girl-group Destiny's Child.",
        "Beyoncé competed in various singing and dancing competitions as a child."
    ]

    # Estimate tokens
    context_tokens = estimate_tokens(context_text)
    question_tokens = [estimate_tokens(q) for q in questions]
    answer_tokens = [estimate_tokens(a) for a in answers]

    print("=" * 80)
    print("📊 TOKEN ESTIMATION")
    print("=" * 80)
    print(f"\nContext: {len(context_text)} chars → ~{context_tokens} tokens")
    for i, (q, a) in enumerate(zip(questions, answers), 1):
        print(f"\nQuestion {i}: {len(q)} chars → ~{question_tokens[i-1]} tokens")
        print(f"Answer {i}: {len(a)} chars → ~{answer_tokens[i-1]} tokens")

    # Create cost report
    report = CostReport()

    # For each provider
    providers_config = {
        'LlamaIndex': {
            'embedding_model': 'text-embedding-3-small',
            'llm_model': 'gpt-4o-mini'
        },
        'LandingAI': {
            'embedding_model': 'text-embedding-3-small',  # External OpenAI
            'llm_model': 'gpt-4o-mini'  # External OpenAI
        },
        'Reducto': {
            'embedding_model': 'text-embedding-3-small',  # External OpenAI
            'llm_model': 'gpt-4o-mini'  # External OpenAI
        }
    }

    for provider_name, config in providers_config.items():
        provider_cost = ProviderCost(
            provider_name=provider_name,
            embedding_model=config['embedding_model'],
            llm_model=config['llm_model'],
            num_documents=1,
            num_queries=len(questions)
        )

        # Embedding costs
        # 1. Document ingestion: embed the full context
        provider_cost.embedding_tokens += context_tokens

        # 2. Query embeddings: embed each question
        provider_cost.embedding_tokens += sum(question_tokens)

        # LLM costs
        # For each query: context + question → answer
        for q_tokens, a_tokens in zip(question_tokens, answer_tokens):
            # Input: retrieved context chunks (assume 1 chunk = full context for this simple test)
            # + question + system prompt (~50 tokens)
            provider_cost.llm_input_tokens += context_tokens + q_tokens + 50

            # Output: generated answer
            provider_cost.llm_output_tokens += a_tokens

        report.providers[provider_name] = provider_cost

    # Evaluation costs (Ragas)
    # 3 providers × 2 questions = 6 samples
    # 3 metrics per sample = 18 metric evaluations
    num_samples = 3 * len(questions)  # 6 samples
    num_metrics = 3  # Faithfulness, ContextRecall, FactualCorrectness
    total_evaluations = num_samples * num_metrics  # 18 evaluations

    eval_cost = EvaluationCost(
        num_samples=num_samples,
        num_metrics=num_metrics,
        llm_model='gpt-4o-mini'
    )

    # Each Ragas metric evaluation:
    # Input: question + context + answer + reference + metric prompt (~500 tokens avg)
    # Output: score + reasoning (~100 tokens avg)
    avg_eval_input_tokens = 500
    avg_eval_output_tokens = 100

    eval_cost.llm_input_tokens = total_evaluations * avg_eval_input_tokens
    eval_cost.llm_output_tokens = total_evaluations * avg_eval_output_tokens

    report.evaluation = eval_cost

    # Print report
    report.print_report()

    # Breakdown by category
    print("\n" + "=" * 80)
    print("📋 COST BREAKDOWN BY OPERATION")
    print("=" * 80)

    total_embed_cost = sum(p.embedding_cost() for p in report.providers.values())
    total_llm_cost = sum(p.llm_cost() for p in report.providers.values())
    eval_cost_val = report.evaluation.cost()

    print(f"\n  Embeddings (all providers):  ${total_embed_cost:.6f}")
    print(f"  RAG LLM calls (all providers): ${total_llm_cost:.6f}")
    print(f"  Ragas evaluation:             ${eval_cost_val:.6f}")
    print(f"  " + "-" * 40)
    print(f"  TOTAL:                        ${report.total_cost():.6f}")

    # Cost per provider
    print("\n" + "=" * 80)
    print("💵 COST PER PROVIDER")
    print("=" * 80)
    for name, provider in report.providers.items():
        cost_per_query = provider.total_cost() / provider.num_queries if provider.num_queries > 0 else 0
        print(f"\n  {name}:")
        print(f"    Total: ${provider.total_cost():.6f}")
        print(f"    Per query: ${cost_per_query:.6f}")

    # Cost efficiency
    print("\n" + "=" * 80)
    print("⚡ EFFICIENCY METRICS")
    print("=" * 80)

    total_queries = sum(p.num_queries for p in report.providers.values())
    cost_per_query = report.total_cost() / total_queries if total_queries > 0 else 0
    cost_per_sample = report.total_cost() / num_samples if num_samples > 0 else 0

    print(f"\n  Total queries: {total_queries}")
    print(f"  Total samples evaluated: {num_samples}")
    print(f"  Cost per query: ${cost_per_query:.6f}")
    print(f"  Cost per evaluated sample: ${cost_per_sample:.6f}")

    # Comparison to baseline
    print("\n" + "=" * 80)
    print("📈 COMPARISON & INSIGHTS")
    print("=" * 80)
    print(f"\n  ✅ Actual test cost: ${report.total_cost():.2f}")
    print(f"  📊 This covered: {len(providers_config)} providers × {len(questions)} questions")
    print(f"  📊 With {num_metrics} Ragas metrics = {total_evaluations} metric evaluations")

    # Extrapolate to larger tests
    print(f"\n  💡 Scaling estimates:")
    cost_per_question_per_provider = report.total_cost() / (len(providers_config) * len(questions))
    print(f"     • 10 questions, 3 providers: ${cost_per_question_per_provider * 10 * 3:.2f}")
    print(f"     • 100 questions, 3 providers: ${cost_per_question_per_provider * 100 * 3:.2f}")
    print(f"     • 1000 questions, 1 provider: ${cost_per_question_per_provider * 1000:.2f}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    analyze_cp4_comprehensive_test()
