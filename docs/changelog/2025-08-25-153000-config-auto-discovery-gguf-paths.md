title: Config — auto_discovery_gguf_paths for local GGUF search

- Added `auto_discovery_gguf_paths` config key (JSON/YAML) to recursively scan directories for `.gguf` models.
- Env override: `CHI_LLM_GGUF_PATHS` (path-separator delimited) sets the same list.
- Local discovery now merges curated catalog IDs with discovered `.gguf` file paths.
- CLI `providers discover-models --type local` returns both.

