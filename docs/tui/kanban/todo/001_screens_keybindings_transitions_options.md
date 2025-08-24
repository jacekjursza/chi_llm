# EPIC: Screens, Keybindings, Transitions & Options (Technology‑Agnostic)

Meta
- Type: Epic
- Scope: TUI vNext (Go version retired)
- Status: Planned / In Progress
- See also: 000_general_app_description.md (Brief/Contract)

Decision
- Implementation language/framework: Rust + ratatui (Aug 24, 2025)

- Context: Specyfikacja ekranów, klawiszologii, przejść i opcji dla nowej wersji TUI jako wrapper nad chi‑llm (Python jako source‑of‑truth). Wymaga `chi-llm` na PATH. Wersja Go jest wycofywana.
- Scope: EPIC rozbity na mniejsze, wykonawcze zadania (poniżej). Każde zadanie ma własny plik TODO z zakresem i kryteriami akceptacji.
- Non‑goals: Wybór języka i frameworka UI; implementacja logiki chi‑llm.

## Sub‑tasks
1) 002_navigation_keymap_skeleton.md — globalna nawigacja, szkielety ekranów, overlay pomocy, check obecności `chi-llm`.
2) 003_readme_viewer.md — przeglądarka README z TOC, przewijanie, stabilny layout.
3) 004_providers_catalog.md — CRUD katalogu providerów na bazie schematów z CLI, tagi, test połączeń (hooki), zapis `chi.tmp.json`.
4) 005_default_provider_selection.md — wybór i zapis providera domyślnego w `chi.tmp.json`.
5) 006_model_browser.md — przeglądarka modeli (CLI + ewentualnie sieć), filtry, wybór modelu do providera.
6) 007_diagnostics.md — widok diagnostyki, eksport JSON, hints środowiskowe.
7) 008_build_configuration.md — zapis `.chi_llm.json` (projekt/global), pretty‑print, tylko niepuste pola, zgodność ze schematem.
8) 009_settings_and_theming.md — ustawienia (theme/animation), tokeny stylów, stała wysokość nagłówka, brak jitteru.
9) 010_connection_tests_utilities.md — narzędzia do testów połączeń (LM Studio, Ollama, OpenAI) z timeoutami i statusami.

Każdy plik zawiera: Scope, Constraints (language‑agnostic, rely on CLI), UX/Keymap, Data contracts, Acceptance Criteria.

## Notes
- Wycofujemy TUI w Go; ten EPIC dotyczy nowej implementacji (język nieustalony).
- Źródłem prawdy są wyjścia CLI (`--json`) i pliki `.chi_llm.json`/`chi.tmp.json`.
