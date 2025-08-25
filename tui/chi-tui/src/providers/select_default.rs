use std::fs;

use anyhow::Result;
use ratatui::layout::Rect;
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph};
use serde_json::Value;

use crate::app::App;

#[derive(Clone, Debug)]
pub struct DefaultProviderState {
    pub providers: Vec<ProviderEntry>,
    pub selected: usize,
    pub current_default_id: Option<String>,
}

#[derive(Clone, Debug)]
pub struct ProviderEntry {
    pub id: String,
    pub name: String,
    pub ptype: String,
    pub tags: Vec<String>,
}

pub fn load_providers_scratch() -> Result<DefaultProviderState> {
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{}".to_string());
    let v: Value = serde_json::from_str(&text)?;
    let mut providers: Vec<ProviderEntry> = Vec::new();
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = p.get("name").and_then(|x| x.as_str()).unwrap_or(&id).to_string();
            let ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let tags: Vec<String> = p.get("tags").and_then(|x| x.as_array()).map(|a| {
                a.iter().filter_map(|t| t.as_str().map(|s| s.to_string())).collect()
            }).unwrap_or_default();
            if !id.is_empty() { providers.push(ProviderEntry { id, name, ptype, tags }); }
        }
    }
    let current_default_id = v.get("default_provider_id").and_then(|x| x.as_str()).map(|s| s.to_string());
    Ok(DefaultProviderState { providers, selected: 0, current_default_id })
}

pub fn save_default_provider(id: &str) -> Result<()> {
    let path = "chi.tmp.json";
    let mut root: Value = if let Ok(text) = fs::read_to_string(path) {
        serde_json::from_str(&text).unwrap_or_else(|_| Value::Object(Default::default()))
    } else {
        Value::Object(Default::default())
    };
    if !root.is_object() { root = Value::Object(Default::default()); }
    if let Some(obj) = root.as_object_mut() {
        obj.insert("default_provider_id".to_string(), Value::String(id.to_string()));
    }
    fs::write(path, serde_json::to_vec_pretty(&root)?)?;
    Ok(())
}

pub fn draw_select_default(f: &mut Frame, area: Rect, app: &App) {
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.defaultp {
        for (i, p) in st.providers.iter().enumerate() {
            let mut label = format!("{} {} [{}]", if i == st.selected { '›' } else { ' ' }, p.name, p.ptype);
            if let Some(cur) = &st.current_default_id { if cur == &p.id { label.push_str("  [default]"); } }
            if !p.tags.is_empty() { label.push_str(&format!("  [{}]", p.tags.join(","))); }
            let style = if i == st.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
            items.push(ListItem::new(Line::from(Span::styled(label, style))))
        }
        if st.providers.is_empty() { items.push(ListItem::new("No providers found in chi.tmp.json → Configure first.")); }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Select Default Provider"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);
}

