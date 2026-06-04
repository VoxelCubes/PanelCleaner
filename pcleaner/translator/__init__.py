"""
Translation subsystem for the Webtoon Translate & Cleaner.

Phase 1 provides the data models and configuration only:
- ``config.TranslatorConfig``: settings owned by a workspace.
- ``structures``: the ``#translated.json`` cache sidecar models and cost accounting.

The OpenRouter HTTP client, prompt construction and batching are added in a later phase.
"""
