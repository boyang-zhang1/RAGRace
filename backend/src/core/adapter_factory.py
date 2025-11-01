"""
Adapter factory for dynamic RAG provider initialization.

Handles:
- Provider name → adapter class mapping
- Environment variable loading
- Configuration merging
- Health check validation
"""

import os
from typing import Dict, List, Optional

from src.adapters.base import BaseAdapter
from src.adapters.llamaindex_adapter import LlamaIndexAdapter
from src.adapters.landingai_adapter import LandingAIAdapter
from src.adapters.reducto_adapter import ReductoAdapter


class AdapterFactory:
    """Factory for creating and initializing RAG adapters."""

    # Mapping: provider name → adapter class
    ADAPTER_REGISTRY = {
        'llamaindex': LlamaIndexAdapter,
        'landingai': LandingAIAdapter,
        'reducto': ReductoAdapter,
    }

    @classmethod
    def create_adapter(
        cls,
        provider_name: str,
        config: Optional[Dict] = None
    ) -> BaseAdapter:
        """
        Create and initialize a single adapter.

        Args:
            provider_name: Name of provider (must be in ADAPTER_REGISTRY)
            config: Provider-specific config with keys:
                - top_k: Number of chunks to retrieve
                - api_key_env: Environment variable for API key
                - Additional provider-specific keys

        Returns:
            Initialized adapter instance

        Raises:
            ValueError: If provider not found or API key missing
        """
        # Validate provider
        provider_lower = provider_name.lower()
        if provider_lower not in cls.ADAPTER_REGISTRY:
            available = ', '.join(cls.ADAPTER_REGISTRY.keys())
            raise ValueError(f"Unknown provider: {provider_name}. Available: {available}")

        # Create adapter instance
        adapter_class = cls.ADAPTER_REGISTRY[provider_lower]
        adapter = adapter_class()

        # Get configuration
        config = config or {}

        # Initialize based on provider type
        if provider_lower == 'llamaindex':
            # Try config first (user-provided), then env vars (testing fallback)
            api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
            cloud_api_key = config.get('llamacloud_api_key') or os.getenv('LLAMAINDEX_API_KEY')

            if not api_key:
                raise ValueError(
                    "OpenAI API key required. Provide via api_keys in request or set OPENAI_API_KEY env variable."
                )
            if not cloud_api_key:
                raise ValueError(
                    "LlamaIndex API key required. Provide via api_keys in request or set LLAMAINDEX_API_KEY env variable."
                )

            adapter.initialize(
                api_key=api_key,
                llamacloud_api_key=cloud_api_key,
                top_k=config.get('top_k', 3)
            )

        elif provider_lower == 'landingai':
            # Try config first (user-provided), then env vars (testing fallback)
            api_key = config.get('api_key') or os.getenv('VISION_AGENT_API_KEY')
            openai_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')

            if not api_key:
                raise ValueError(
                    "Vision Agent API key required. Provide via api_keys in request or set VISION_AGENT_API_KEY env variable."
                )
            if not openai_key:
                raise ValueError(
                    "OpenAI API key required. Provide via api_keys in request or set OPENAI_API_KEY env variable."
                )

            adapter.initialize(
                api_key=api_key,
                openai_api_key=openai_key,
                top_k=config.get('top_k', 3)
            )

        elif provider_lower == 'reducto':
            # Try config first (user-provided), then env vars (testing fallback)
            api_key = config.get('api_key') or os.getenv('REDUCTO_API_KEY')
            openai_key = config.get('openai_api_key') or os.getenv('OPENAI_API_KEY')

            if not api_key:
                raise ValueError(
                    "Reducto API key required. Provide via api_keys in request or set REDUCTO_API_KEY env variable."
                )
            if not openai_key:
                raise ValueError(
                    "OpenAI API key required. Provide via api_keys in request or set OPENAI_API_KEY env variable."
                )

            adapter.initialize(
                api_key=api_key,
                openai_api_key=openai_key,
                top_k=config.get('top_k', 3)
            )

        # Validate adapter is healthy
        if not adapter.health_check():
            raise RuntimeError(f"Health check failed for {provider_name}")

        return adapter

    @classmethod
    def create_all_adapters(
        cls,
        provider_names: List[str],
        provider_configs: Dict[str, Dict]
    ) -> Dict[str, BaseAdapter]:
        """
        Create multiple adapters at once.

        Args:
            provider_names: List of provider names to create
            provider_configs: Dict mapping provider name → config

        Returns:
            Dict mapping provider name → initialized adapter
        """
        adapters = {}
        for name in provider_names:
            config = provider_configs.get(name, {})
            adapters[name] = cls.create_adapter(name, config)

        return adapters

    @staticmethod
    def validate_adapter(adapter: BaseAdapter) -> bool:
        """
        Validate that an adapter is properly initialized.

        Args:
            adapter: Adapter instance to validate

        Returns:
            True if adapter is healthy
        """
        return adapter.health_check()
