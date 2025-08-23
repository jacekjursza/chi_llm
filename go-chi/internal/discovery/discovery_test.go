package discovery

import (
    "encoding/json"
    "net/http"
    "net/http/httptest"
    "testing"
)

func TestLMStudioModels(t *testing.T) {
    mux := http.NewServeMux()
    mux.HandleFunc("/v1/models", func(w http.ResponseWriter, r *http.Request) {
        _ = json.NewEncoder(w).Encode(map[string]any{
            "data": []map[string]any{{"id": "qwen2.5"}, {"id": "phi3-mini"}},
        })
    })
    srv := httptest.NewServer(mux)
    defer srv.Close()
    got, err := LMStudioModels(srv.URL)
    if err != nil { t.Fatal(err) }
    if len(got) != 2 { t.Fatalf("want 2, got %d", len(got)) }
    if got[0].ID == "" || got[1].ID == "" { t.Fatalf("empty ids: %+v", got) }
}

func TestLMStudioModelsEmpty(t *testing.T) {
    mux := http.NewServeMux()
    mux.HandleFunc("/v1/models", func(w http.ResponseWriter, r *http.Request) {
        _ = json.NewEncoder(w).Encode(map[string]any{"data": []any{}})
    })
    srv := httptest.NewServer(mux)
    defer srv.Close()
    got, err := LMStudioModels(srv.URL)
    if err != nil { t.Fatal(err) }
    if len(got) != 0 { t.Fatalf("want 0, got %d", len(got)) }
}

func TestOllamaModels(t *testing.T) {
    mux := http.NewServeMux()
    mux.HandleFunc("/api/tags", func(w http.ResponseWriter, r *http.Request) {
        _ = json.NewEncoder(w).Encode(map[string]any{
            "models": []map[string]any{
                {"name": "llama3.2:latest", "size": 1024 * 1024 * 100},
                {"name": "qwen2.5-coder:7b", "size": 0},
            },
        })
    })
    srv := httptest.NewServer(mux)
    defer srv.Close()
    got, err := OllamaModels(srv.URL)
    if err != nil { t.Fatal(err) }
    if len(got) != 2 { t.Fatalf("want 2, got %d", len(got)) }
    if got[0].SizeMB() == 0 { t.Fatalf("expected non-zero sizeMB for first model: %+v", got[0]) }
}

