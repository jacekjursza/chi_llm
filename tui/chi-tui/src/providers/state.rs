use std::collections::HashMap;
use std::fs;
use std::time::Duration;

use anyhow::Result;
use serde_json::Value;

use crate::util::run_cli_json;

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
    pub test_status: Option<String>,
    pub form: Option<FormState>,
    pub focus_right: bool,
    pub dropdown: Option<DropdownState>,
}

impl ProvidersState {
    pub fn empty() -> Self {
        Self {
            entries: Vec::new(),
            selected: 0,
            schema_types: Vec::new(),
            schema_map: HashMap::new(),
            test_status: None,
            form: None,
            focus_right: false,
            dropdown: None,
        }
    }
    pub fn len_with_add(&self) -> usize { self.entries.len() + 1 }
    pub fn is_add_row(&self) -> bool { self.selected >= self.entries.len() }
    pub fn add_default(&mut self) {
        // Prefer new zeroconfig local type when available, then legacy local, then first type
        let ptype = if let Some(idx) = self.schema_types.iter().position(|t| t == "local-zeroconfig") {
            self.schema_types.get(idx).cloned().unwrap_or_else(|| "local-zeroconfig".to_string())
        } else if let Some(idx) = self.schema_types.iter().position(|t| t == "local") {
            self.schema_types.get(idx).cloned().unwrap_or_else(|| "local".to_string())
        } else {
            self.schema_types.get(0).cloned().unwrap_or_else(|| "local".to_string())
        };
        let id = format!("p{}", self.entries.len() + 1);
        let name = format!("{}", &ptype);
        let cfg = serde_json::json!({"type": ptype});
        self.entries.push(ProviderScratchEntry {
            id,
            name,
            ptype: cfg.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            tags: Vec::new(),
            config: cfg,
        });
        self.selected = self.entries.len().saturating_sub(1);
    }
    pub fn delete_selected(&mut self) {
        if self.selected < self.entries.len() {
            self.entries.remove(self.selected);
            if self.selected > 0 { self.selected -= 1; }
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
        if !root.is_object() { root = serde_json::json!({}); }
        if let Some(obj) = root.as_object_mut() {
            obj.insert("providers".to_string(), Value::Array(providers));
        }
        fs::write(path, serde_json::to_vec_pretty(&root)?)?;
        Ok(())
    }
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
                        // Collect enum-like options for dropdowns from common keys
                        let mut opts: Vec<String> = Vec::new();
                        for key in ["options", "enum", "choices"].iter() {
                            if let Some(arr) = f.get(*key).and_then(|v| v.as_array()) {
                                for it in arr.iter() {
                                    if let Some(s) = it.as_str() {
                                        if !opts.contains(&s.to_string()) { opts.push(s.to_string()); }
                                    }
                                }
                            }
                        }
                        let options = if opts.is_empty() { None } else { Some(opts) };
                        fields.push(FieldSchema { name, ftype, required, default, help, options });
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
            let name = p.get("name").and_then(|x| x.as_str()).unwrap_or(&id).to_string();
            let ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let tags: Vec<String> = p.get("tags").and_then(|x| x.as_array()).map(|a| {
                a.iter().filter_map(|t| t.as_str().map(|s| s.to_string())).collect()
            }).unwrap_or_default();
            let config = p.get("config").cloned().unwrap_or_else(|| serde_json::json!({"type": ptype}));
            entries.push(ProviderScratchEntry { id, name, ptype, tags, config });
        }
    }
    Ok(ProvidersState {
        entries,
        selected: 0,
        schema_types: types,
        schema_map,
        test_status: None,
        form: None,
        focus_right: false,
        dropdown: None,
    })
}

#[derive(Clone, Debug)]
pub struct FieldSchema {
    pub name: String,
    pub ftype: String,
    pub required: bool,
    pub default: Option<String>,
    pub help: Option<String>,
    pub options: Option<Vec<String>>, // optional enum-like options for dropdowns
}

#[derive(Clone, Debug)]
pub struct FormField { pub schema: FieldSchema, pub buffer: String, pub cursor: usize }

#[derive(Clone, Debug)]
pub struct FormState {
    pub fields: Vec<FormField>,
    pub selected: usize, // 0: Type, 1..=fields: fields, fields+1: Save, fields+2: Cancel
    pub editing: bool,
    pub message: Option<String>,
    pub scroll: usize,
    pub initial_hash: String,
    pub last_test_ok_hash: Option<String>,
}

pub fn compute_form_hash(fields: &Vec<FormField>) -> String {
    let mut s = String::new();
    for f in fields.iter() {
        s.push_str(&f.schema.name);
        s.push('=');
        s.push_str(&f.buffer);
        s.push('\u{1F}');
    }
    s
}

#[derive(Clone, Debug)]
pub struct DropdownState {
    pub items: Vec<String>,
    pub selected: usize,
    pub title: String,
    pub target_field: Option<usize>, // None => provider type; Some(i) => form field index
    pub filter: String,
}
