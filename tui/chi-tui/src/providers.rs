use std::time::Duration;
use std::fs;
use std::collections::HashMap;

use anyhow::Result;
use ratatui::layout::Rect;
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap};
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
use serde_json::Value;

use crate::app::App;
use crate::util::{centered_rect, run_cli_json};

#[derive(Clone, Debug)]
pub struct ProviderEntry {
    pub id: String,
    pub name: String,
    pub ptype: String,
    pub tags: Vec<String>,
}

#[derive(Clone, Debug)]
pub struct DefaultProviderState {
    pub providers: Vec<ProviderEntry>,
    pub selected: usize,
    pub current_default_id: Option<String>,
}

pub fn load_providers_scratch() -> Result<DefaultProviderState> {
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{}".to_string());
    let v: Value = serde_json::from_str(&text)?;
    let mut providers: Vec<ProviderEntry> = Vec::new();
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = p
                .get("name")
                .and_then(|x| x.as_str())
                .unwrap_or(&id)
                .to_string();
            let ptype = p
                .get("type")
                .and_then(|x| x.as_str())
                .unwrap_or("")
                .to_string();
            let tags: Vec<String> = p
                .get("tags")
                .and_then(|x| x.as_array())
                .map(|a| {
                    a.iter()
                        .filter_map(|t| t.as_str().map(|s| s.to_string()))
                        .collect()
                })
                .unwrap_or_default();
            if !id.is_empty() {
                providers.push(ProviderEntry {
                    id,
                    name,
                    ptype,
                    tags,
                });
            }
        }
    }
    let current_default_id = v
        .get("default_provider_id")
        .and_then(|x| x.as_str())
        .map(|s| s.to_string());
    Ok(DefaultProviderState {
        providers,
        selected: 0,
        current_default_id,
    })
}

pub fn save_default_provider(id: &str) -> Result<()> {
    let path = "chi.tmp.json";
    let mut root: Value = if let Ok(text) = fs::read_to_string(path) {
        serde_json::from_str(&text).unwrap_or_else(|_| Value::Object(Default::default()))
    } else {
        Value::Object(Default::default())
    };
    if !root.is_object() {
        root = Value::Object(Default::default());
    }
    if let Some(obj) = root.as_object_mut() {
        obj.insert(
            "default_provider_id".to_string(),
            Value::String(id.to_string()),
        );
    }
    fs::write(path, serde_json::to_vec_pretty(&root)?)?;
    Ok(())
}

pub fn draw_select_default(f: &mut Frame, area: Rect, app: &App) {
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.defaultp {
        for (i, p) in st.providers.iter().enumerate() {
            let mut label = format!(
                "{} {} [{}]",
                if i == st.selected { '›' } else { ' ' },
                p.name,
                p.ptype
            );
            if let Some(cur) = &st.current_default_id {
                if cur == &p.id {
                    label.push_str("  [default]");
                }
            }
            if !p.tags.is_empty() {
                label.push_str(&format!("  [{}]", p.tags.join(",")));
            }
            let style = if i == st.selected {
                Style::default()
                    .fg(app.theme.selected)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(app.theme.fg)
            };
            items.push(ListItem::new(Line::from(Span::styled(label, style))))
        }
        if st.providers.is_empty() {
            items.push(ListItem::new(
                "No providers found in chi.tmp.json → Configure first.",
            ));
        }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title("Select Default Provider"),
        )
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);
}

#[derive(Clone, Debug)]
pub struct ProviderScratchEntry {
    pub id: String,
    pub name: String,
    pub ptype: String,
    pub tags: Vec<String>,
    pub config: Value,
}

#[derive(Clone, Debug)]
pub struct ProvidersState {
    pub entries: Vec<ProviderScratchEntry>,
    pub selected: usize,
    pub schema_types: Vec<String>,
    pub schema_map: HashMap<String, Vec<FieldSchema>>, // type -> fields
    pub edit: Option<EditState>,
    pub test_status: Option<String>,
    pub form: Option<FormState>,
}

impl ProvidersState {
    pub fn empty() -> Self {
        Self {
            entries: Vec::new(),
            selected: 0,
            schema_types: Vec::new(),
            schema_map: HashMap::new(),
            edit: None,
            test_status: None,
            form: None,
        }
    }
    pub fn len_with_add(&self) -> usize {
        self.entries.len() + 1
    }
    pub fn is_add_row(&self) -> bool {
        self.selected >= self.entries.len()
    }
    pub fn add_default(&mut self) {
        let ptype = self
            .schema_types
            .get(0)
            .cloned()
            .unwrap_or_else(|| "local".to_string());
        let id = format!("p{}", self.entries.len() + 1);
        let name = format!("{}", &ptype);
        let cfg = serde_json::json!({"type": ptype});
        self.entries.push(ProviderScratchEntry {
            id,
            name,
            ptype: cfg
                .get("type")
                .and_then(|x| x.as_str())
                .unwrap_or("")
                .to_string(),
            tags: Vec::new(),
            config: cfg,
        });
        self.selected = self.entries.len().saturating_sub(1);
    }
    pub fn delete_selected(&mut self) {
        if self.selected < self.entries.len() {
            self.entries.remove(self.selected);
            if self.selected > 0 {
                self.selected -= 1;
            }
        }
    }
    pub fn apply_model_to_selected(&mut self, model_id: &str) {
        if self.selected < self.entries.len() {
            if let Some(obj) = self.entries[self.selected].config.as_object_mut() {
                obj.insert("model".to_string(), Value::String(model_id.to_string()));
            }
        }
    }
    pub fn save(&self) -> Result<()> {
        // Preserve default_provider_id if present
        let path = "chi.tmp.json";
        let mut root: Value = if let Ok(text) = fs::read_to_string(path) {
            serde_json::from_str(&text).unwrap_or_else(|_| serde_json::json!({}))
        } else {
            serde_json::json!({})
        };
        let mut providers: Vec<Value> = Vec::new();
        for e in &self.entries {
            providers.push(serde_json::json!({
                "id": e.id,
                "name": e.name,
                "type": e.ptype,
                "tags": e.tags,
                "config": e.config,
            }));
        }
        if !root.is_object() {
            root = serde_json::json!({});
        }
        if let Some(obj) = root.as_object_mut() {
            obj.insert("providers".to_string(), Value::Array(providers));
        }
        fs::write(path, serde_json::to_vec_pretty(&root)?)?;
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct EditState {
    pub field: String,
    pub buffer: String,
}

pub fn load_providers_state() -> Result<ProvidersState> {
    // Load schema types and fields
    let schema = run_cli_json(&["providers", "schema", "--json"], Duration::from_secs(5))?;
    let mut types: Vec<String> = Vec::new();
    let mut schema_map: HashMap<String, Vec<FieldSchema>> = HashMap::new();
    if let Some(arr) = schema.get("providers").and_then(|v| v.as_array()) {
        for prov in arr {
            if let Some(ptype) = prov.get("type").and_then(|v| v.as_str()) {
                types.push(ptype.to_string());
                let mut fields: Vec<FieldSchema> = Vec::new();
                if let Some(farr) = prov.get("fields").and_then(|v| v.as_array()) {
                    for f in farr {
                        let name = f.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        if name.is_empty() { continue; }
                        let ftype = f.get("type").and_then(|v| v.as_str()).unwrap_or("string").to_string();
                        let required = f.get("required").and_then(|v| v.as_bool()).unwrap_or(false);
                        let default = if let Some(d) = f.get("default") { Some(d.to_string().trim_matches('"').to_string()) } else { None };
                        let help = f.get("help").and_then(|v| v.as_str()).map(|s| s.to_string());
                        fields.push(FieldSchema { name, ftype, required, default, help });
                    }
                }
                schema_map.insert(ptype.to_string(), fields);
            }
        }
    }
    types.sort();
    // Load scratch file
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{}".to_string());
    let v: Value = serde_json::from_str(&text)?;
    let mut entries: Vec<ProviderScratchEntry> = Vec::new();
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = p
                .get("name")
                .and_then(|x| x.as_str())
                .unwrap_or(&id)
                .to_string();
            let ptype = p
                .get("type")
                .and_then(|x| x.as_str())
                .unwrap_or("")
                .to_string();
            let tags: Vec<String> = p
                .get("tags")
                .and_then(|x| x.as_array())
                .map(|a| {
                    a.iter()
                        .filter_map(|t| t.as_str().map(|s| s.to_string()))
                        .collect()
                })
                .unwrap_or_default();
            let config = p
                .get("config")
                .cloned()
                .unwrap_or_else(|| serde_json::json!({"type": ptype}));
            entries.push(ProviderScratchEntry {
                id,
                name,
                ptype,
                tags,
                config,
            });
        }
    }
    Ok(ProvidersState {
        entries,
        selected: 0,
        schema_types: types,
        schema_map,
        edit: None,
        test_status: None,
        form: None,
    })
}

pub fn draw_providers_catalog(f: &mut Frame, area: Rect, app: &App) {
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.providers {
        for (i, e) in st.entries.iter().enumerate() {
            let mut label = format!(
                "{} {} [{}]",
                if i == st.selected { '›' } else { ' ' },
                e.name,
                e.ptype
            );
            if let Some(model) = e.config.get("model").and_then(|v| v.as_str()) {
                label.push_str(&format!("  [model:{}]", model));
            }
            if !e.tags.is_empty() {
                label.push_str(&format!("  [{}]", e.tags.join(",")));
            }
            let style = if i == st.selected {
                Style::default()
                    .fg(app.theme.selected)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(app.theme.fg)
            };
            items.push(ListItem::new(Line::from(Span::styled(label, style))));
        }
        // Add provider row
        let add_style = if st.is_add_row() {
            Style::default()
                .fg(app.theme.selected)
                .add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(app.theme.accent)
        };
        items.push(ListItem::new(Line::from(Span::styled(
            "+ Add provider",
            add_style,
        ))));
        if let Some(status) = &st.test_status {
            items.push(ListItem::new(Line::from(Span::styled(
                format!("Status: {}", status),
                Style::default().fg(app.theme.secondary),
            ))));
        }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title("Configure Providers"),
        )
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);

    // Input overlay for editing provider field or schema-driven form
    if let Some(st) = &app.providers {
        if let Some(edit) = &st.edit {
            let area_pop = centered_rect(60, 30, area);
            let prompt = format!("Edit {}: {}", edit.field, edit.buffer);
            let p = Paragraph::new(prompt)
                .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(Style::default().fg(app.theme.frame))
                        .title("Edit Field (Enter=save, Esc=cancel)"),
                )
                .alignment(ratatui::layout::Alignment::Left)
                .wrap(Wrap { trim: true });
            f.render_widget(Clear, area_pop);
            f.render_widget(p, area_pop);
        } else if let Some(form) = &st.form {
            let area_pop = centered_rect(70, 70, area);
            let mut lines: Vec<Line> = Vec::new();
            lines.push(Line::from(Span::styled(
                "Provider Form (↑/↓ select • Enter edit • s save • Esc close)",
                Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD),
            )));
            for (i, ff) in form.fields.iter().enumerate() {
                let req = if ff.schema.required { "*" } else { " " };
                let label = format!("{} {}: {}", req, ff.schema.name, ff.buffer);
                let style = if i == form.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                lines.push(Line::from(Span::styled(label, style)));
            }
            let p = Paragraph::new(lines)
                .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
                .block(
                    Block::default()
                        .borders(Borders::ALL)
                        .border_style(Style::default().fg(app.theme.frame))
                        .title("Edit Provider"),
                )
                .alignment(ratatui::layout::Alignment::Left)
                .wrap(Wrap { trim: true });
            f.render_widget(Clear, area_pop);
            f.render_widget(p, area_pop);
        }
    }
}

#[derive(Clone, Debug)]
pub struct FieldSchema {
    pub name: String,
    pub ftype: String,
    pub required: bool,
    pub default: Option<String>,
    pub help: Option<String>,
}

#[derive(Clone, Debug)]
pub struct FormField { pub schema: FieldSchema, pub buffer: String }

#[derive(Clone, Debug)]
pub struct FormState { pub fields: Vec<FormField>, pub selected: usize, pub editing: bool }

pub fn probe_provider(entry: &ProviderScratchEntry) -> Result<String> {
    let ptype = entry.ptype.as_str();
    if ptype == "local" {
        return Ok("local: no network test".to_string());
    }
    let client = Client::builder().timeout(Duration::from_secs(3)).build()?;
    match ptype {
        "lmstudio" => {
            let host = entry
                .config
                .get("host")
                .and_then(|v| v.as_str())
                .unwrap_or("127.0.0.1");
            let port = entry
                .config
                .get("port")
                .and_then(|v| v.as_u64())
                .unwrap_or(1234);
            let url = format!("http://{}:{}/v1/models", host, port);
            let resp = client.get(&url).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v
                    .get("data")
                    .and_then(|d| d.as_array())
                    .map(|a| a.len())
                    .unwrap_or(0);
                Ok(format!("lmstudio: {} models", count))
            } else {
                Ok(format!("lmstudio: HTTP {}", status))
            }
        }
        "ollama" => {
            let host = entry
                .config
                .get("host")
                .and_then(|v| v.as_str())
                .unwrap_or("127.0.0.1");
            let port = entry
                .config
                .get("port")
                .and_then(|v| v.as_u64())
                .unwrap_or(11434);
            let url = format!("http://{}:{}/api/tags", host, port);
            let resp = client.get(&url).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v
                    .get("models")
                    .and_then(|d| d.as_array())
                    .map(|a| a.len())
                    .unwrap_or(0);
                Ok(format!("ollama: {} tags", count))
            } else {
                Ok(format!("ollama: HTTP {}", status))
            }
        }
        "openai" => {
            let base = entry
                .config
                .get("base_url")
                .and_then(|v| v.as_str())
                .unwrap_or("https://api.openai.com");
            let url = format!("{}/v1/models", base.trim_end_matches('/'));
            let key = entry
                .config
                .get("api_key")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let org = entry.config.get("org_id").and_then(|v| v.as_str());
            if key.is_empty() {
                return Ok("openai: missing api_key".to_string());
            }
            let mut headers = HeaderMap::new();
            let authv = format!("Bearer {}", key);
            headers.insert(
                AUTHORIZATION,
                HeaderValue::from_str(&authv).unwrap_or(HeaderValue::from_static("")),
            );
            if let Some(o) = org {
                headers.insert(
                    "OpenAI-Organization",
                    HeaderValue::from_str(o)
                        .unwrap_or(HeaderValue::from_static("")),
                );
            }
            let resp = client.get(&url).headers(headers).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v
                    .get("data")
                    .and_then(|d| d.as_array())
                    .map(|a| a.len())
                    .unwrap_or(0);
                Ok(format!("openai: {} models", count))
            } else {
                Ok(format!("openai: HTTP {}", status))
            }
        }
        _ => Ok(format!("{}: no test implemented", ptype)),
    }
}
