use std::time::Duration;
use std::collections::HashMap;
use std::fs;

use anyhow::{Result, anyhow};
use ratatui::layout::{Rect, Layout, Direction, Constraint};
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap};
use crate::util::{run_cli_json, spinner_char};
use super::state::compute_form_hash;
use serde_json::Value;

use crate::app::App;
use crate::util::centered_rect;

use super::{ProvidersState, FormField};

fn read_json(path: &str) -> Option<Value> {
    let text = fs::read_to_string(path).ok()?;
    serde_json::from_str::<Value>(&text).ok()
}

fn get_tmp_default_id() -> Option<String> {
    let v = read_json(".chi_llm.tmp.json")?;
    v.get("default_provider_id").and_then(|x| x.as_str()).map(|s| s.to_string())
}

fn get_final_provider_object() -> Option<HashMap<String, Value>> {
    let v = read_json(".chi_llm.json")?;
    v.get("provider").and_then(|x| x.as_object()).map(|m| m.clone().into_iter().collect())
}

fn value_to_norm_string(v: &Value) -> String {
    match v {
        Value::String(s) => s.clone(),
        Value::Number(n) => n.to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Null => String::new(),
        other => other.to_string(),
    }
}

pub fn draw_providers_catalog(f: &mut Frame, area: Rect, app: &App) {
    let cols = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([Constraint::Percentage(45), Constraint::Percentage(55)]).split(area);

    // Left list
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.providers {
        for (i, e) in st.entries.iter().enumerate() {
            let mut label = format!("{} {} [{}]", if i == st.selected { '›' } else { ' ' }, e.name, e.ptype);
            if let Some(model) = e.config.get("model").and_then(|v| v.as_str()) { label.push_str(&format!("  [model:{}]", model)); }
            if !e.tags.is_empty() { label.push_str(&format!("  [{}]", e.tags.join(","))); }
            let mut style = if i == st.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
            if !st.focus_right && i == st.selected { style = style.add_modifier(Modifier::UNDERLINED); }
            items.push(ListItem::new(Line::from(Span::styled(label, style))));
        }
        let mut add_style = if st.is_add_row() { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.accent) };
        if !st.focus_right && st.is_add_row() { add_style = add_style.add_modifier(Modifier::UNDERLINED); }
        items.push(ListItem::new(Line::from(Span::styled("+ Add provider", add_style))));
        if st.test_in_progress {
            let spin = spinner_char(app.tick);
            items.push(ListItem::new(Line::from(Span::styled(format!("Status: Testing… {}", spin), Style::default().fg(app.theme.secondary)))));
        } else if let Some(status) = &st.test_status {
            items.push(ListItem::new(Line::from(Span::styled(format!("Status: {}", status), Style::default().fg(app.theme.secondary)))));
        }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    // Highlight left pane when it has focus (focus_right == false)
    let left_border = if let Some(st) = &app.providers { if !st.focus_right { app.theme.selected } else { app.theme.frame } } else { app.theme.frame };
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(left_border)).title("Configure Providers"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, cols[0]);

    // Right form panel
    let right = cols[1];
    // Draw an outer border around the right pane to indicate active focus (draw first to avoid overlapping content)
    if let Some(st) = &app.providers {
        let right_border = if st.focus_right { app.theme.selected } else { app.theme.frame };
        let outer = Block::default().borders(Borders::ALL).border_style(Style::default().fg(right_border));
        f.render_widget(outer, right);
    }
    let mut title = "Provider Details".to_string();
    if let Some(st) = &app.providers {
        if st.selected < st.entries.len() {
            let entry = &st.entries[st.selected];
            title = format!("Provider Details — {}", entry.ptype);
            let fields: Vec<FormField> = if let Some(form) = &st.form { form.fields.clone() } else { Vec::new() };
            if fields.is_empty() {
                let p = Paragraph::new("Tab to open form").style(Style::default().bg(app.theme.bg).fg(app.theme.secondary)).block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title));
                f.render_widget(p, right);
            } else {
                // layout with type row, fields (scroll), message, buttons
                let total_height = right.height as usize;
                let reserve = 3 + 1 + 3;
                let per_field = 3usize;
                let max_fields_visible = if total_height > reserve { (total_height - reserve) / per_field } else { 0 };
                let mut start = 0usize; let mut end = fields.len();
                if let Some(form) = &st.form { if fields.len() > max_fields_visible {
                    let sel = form.selected.saturating_sub(1);
                    let mut scroll = form.scroll;
                    if sel < scroll { scroll = sel; }
                    if sel >= scroll + max_fields_visible { scroll = sel + 1 - max_fields_visible; }
                    start = scroll.min(fields.len().saturating_sub(max_fields_visible));
                    end = (start + max_fields_visible).min(fields.len());
                } }
                let visible = &fields[start..end];
                let mut cons: Vec<Constraint> = Vec::new();
                cons.push(Constraint::Length(3));
                cons.extend(std::iter::repeat(Constraint::Length(3)).take(visible.len()));
                cons.push(Constraint::Length(1));
                cons.push(Constraint::Length(3));
                let chunks = Layout::default().direction(Direction::Vertical).constraints(cons).split(right);
                if let Some(form) = &st.form {
                    let sel = form.selected;
                    let style = if st.focus_right && sel == 0 { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    // Unsaved marker for Type: show * when selected provider is default and final provider type differs
                    let mut type_label = String::from("Type");
                    if let Some(def_id) = get_tmp_default_id() {
                        if def_id == entry.id {
                            if let Some(final_p) = get_final_provider_object() {
                                if let Some(vt) = final_p.get("type") {
                                    let final_type = value_to_norm_string(vt);
                                    if final_type != entry.ptype { type_label.push('*'); }
                                }
                            }
                        }
                    }
                    let p = Paragraph::new(format!("{}: {}  (Enter to change)", type_label, entry.ptype)).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(Block::default().borders(Borders::ALL).border_style(style));
                    f.render_widget(p, chunks[0]);
                }
                for (i_vis, ff) in visible.iter().enumerate() {
                    let i = start + i_vis;
                    let mut display = if ff.schema.ftype == "secret" && !ff.buffer.is_empty() { "••••••".to_string() } else { ff.buffer.clone() };
                    let is_selected = st.focus_right && st.form.as_ref().map(|f| f.selected).unwrap_or(0) == i + 1;
                    let is_editing = st.form.as_ref().map(|f| f.editing).unwrap_or(false);
                    if is_selected && is_editing {
                        let pos = ff.cursor.min(ff.buffer.chars().count());
                        if ff.schema.ftype == "secret" { display = ff.buffer.chars().map(|_| '•').collect(); }
                        let (byte_idx, _) = display.char_indices().nth(pos).unwrap_or((display.len(), ' '));
                        display.insert(byte_idx, '▌');
                    }
                    let mut bstyle = Style::default().fg(app.theme.frame);
                    if ff.schema.required && ff.buffer.trim().is_empty() { bstyle = Style::default().fg(ratatui::style::Color::Red); }
                    if is_selected { bstyle = Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD); }
                    // Unsaved marker per field: show * at label end when selected provider is default and field differs from final provider
                    let mut title_txt = if ff.schema.required { format!("* {}", ff.schema.name) } else { ff.schema.name.clone() };
                    if let Some(def_id) = get_tmp_default_id() {
                        if def_id == entry.id {
                            if let Some(final_p) = get_final_provider_object() {
                                let final_val = final_p.get(&ff.schema.name).map(value_to_norm_string);
                                let current_val = ff.buffer.clone();
                                if final_val.map(|v| v != current_val).unwrap_or(true) {
                                    // When final is missing the key or value differs, mark as unsaved
                                    title_txt.push(' ');
                                    title_txt.push('*');
                                }
                            }
                        }
                    }
                    let block = Block::default().borders(Borders::ALL).border_style(bstyle).title(title_txt);
                    let p = Paragraph::new(display).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(block).wrap(Wrap { trim: false });
                    f.render_widget(p, chunks[1 + i_vis]);
                }
                if let Some(form) = &st.form {
                    let mut msg = form.message.clone().unwrap_or_default();
                    if st.test_in_progress {
                        let spin = spinner_char(app.tick);
                        if msg.is_empty() { msg = "Testing connection…".to_string(); }
                        msg = format!("{} {}  (L: logs)", msg, spin);
                    }
                    if fields.len() > end { msg = format!("{}  ↓ more…", msg); }
                    if start > 0 { msg = format!("↑ more…  {}", msg); }
                    let p = Paragraph::new(msg).style(Style::default().bg(app.theme.bg).fg(app.theme.secondary)).block(Block::default());
                    f.render_widget(p, chunks[1 + visible.len()]);
                    let buttons_area = chunks[1 + visible.len() + 1];
                    let sel = form.selected;
                    let test_idx = fields.len() + 1;
                    let save_idx = fields.len() + 2;
                    let cancel_idx = fields.len() + 3;
                    // Compute save enabled: disabled if dirty and not tested ok for current values
                    let cur_hash = crate::providers::compute_form_hash(&form.fields);
                    let dirty = cur_hash != form.initial_hash;
                    let tested_ok = form.last_test_ok_hash.as_ref().map_or(false, |h| *h == cur_hash);
                    let save_enabled = !(dirty && !tested_ok);
                    let test_style = if sel == test_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    let mut save_style = if sel == save_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    if !save_enabled { save_style = Style::default().fg(app.theme.secondary).add_modifier(Modifier::DIM); }
                    let cancel_style = if sel == cancel_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    let btns = vec![Line::from(vec![Span::styled("[ Test ]  ", test_style), Span::styled("[ Save ]  ", save_style), Span::styled("[ Cancel ]", cancel_style)])];
                    let p = Paragraph::new(btns).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title)).alignment(ratatui::layout::Alignment::Left);
                    f.render_widget(p, buttons_area);
                }
            }
        } else {
            let p = Paragraph::new("Add a provider to edit details.").style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title));
            f.render_widget(p, right);
        }
    } else {
        let p = Paragraph::new("Loading...").style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title));
        f.render_widget(p, right);
    }

    // (outer border drawn earlier)

    // Overlay dropdown
    if let Some(st) = &app.providers {
        if let Some(dd) = &st.dropdown {
            let area_pop = centered_rect(60, 70, area);
            // Compute filtered indices by simple case-insensitive substring match
            let filt = dd.filter.to_lowercase();
            let mut filtered: Vec<usize> = Vec::new();
            for (i, it) in dd.items.iter().enumerate() {
                if filt.is_empty() || it.to_lowercase().contains(&filt) { filtered.push(i); }
            }
            let mut cons: Vec<Constraint> = Vec::new();
            cons.push(Constraint::Length(3)); // filter input
            cons.push(Constraint::Min(3));    // list
            let chunks = Layout::default().direction(Direction::Vertical).constraints(cons).split(area_pop);
            // Filter input line
            let filter_line = format!("Filter: {}", dd.filter);
            let p = Paragraph::new(filter_line)
                .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(dd.title.clone()));
            // List of items
            let mut items: Vec<ListItem> = Vec::new();
            for (pos, &idx) in filtered.iter().enumerate() {
                let raw = dd.items[idx].clone();
                let mut label = raw.clone();
                if let Some(set) = &dd.downloaded {
                    if set.contains(&raw) { label.push_str("  [downloaded]"); }
                }
                let style = if pos == dd.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                items.push(ListItem::new(Line::from(Span::styled(label, style))));
            }
            if items.is_empty() { items.push(ListItem::new(Line::from(Span::styled("(no matches)", Style::default().fg(app.theme.secondary))))); }
            let list = List::new(items)
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)))
                .highlight_style(Style::default().fg(app.theme.selected));
            f.render_widget(Clear, area_pop);
            f.render_widget(p, chunks[0]);
            f.render_widget(list, chunks[1]);
        }
        // Test logs popup overlay
        if st.show_test_popup {
            let area_pop = centered_rect(80, 70, area);
            let mut lines: Vec<Line> = Vec::new();
            let title = if st.test_in_progress { "Connection Test — Logs (press L/Esc to close)" } else { "Connection Test — Logs (closed with L/Esc)" };
            if st.test_log.is_empty() {
                lines.push(Line::from("(no logs yet)"));
            } else {
                // Show last ~100 lines
                let take_n = st.test_log.len().saturating_sub(100);
                for l in st.test_log.iter().skip(take_n) {
                    lines.push(Line::from(l.as_str()));
                }
            }
            let p = Paragraph::new(lines)
                .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title))
                .wrap(Wrap { trim: false });
            f.render_widget(Clear, area_pop);
            f.render_widget(p, area_pop);
        }
    }
}

pub fn probe_provider(entry: &super::state::ProviderScratchEntry) -> Result<String> {
    let ptype = entry.ptype.as_str();
    // Build args for unified CLI probe
    let mut args: Vec<String> = vec!["providers".into(), "test".into(), "--type".into(), ptype.into(), "--e2e".into(), "--json".into()];
    match ptype {
        "local" => { /* no extra args */ }
        "local-custom" => {
            if let Some(path) = entry.config.get("model_path").and_then(|v| v.as_str()) {
                args.push("--model-path".into()); args.push(path.into());
            }
        }
        "lmstudio" | "ollama" => {
            if let Some(host) = entry.config.get("host").and_then(|v| v.as_str()) {
                args.push("--host".into()); args.push(host.into());
            }
            if let Some(port) = entry.config.get("port").and_then(|v| v.as_u64()) {
                args.push("--port".into()); args.push(port.to_string());
            }
            if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                args.push("--model".into()); args.push(model.into());
            }
        }
        "openai" => {
            if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                args.push("--base-url".into()); args.push(base.into());
            }
            if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                args.push("--api-key".into()); args.push(key.into());
            }
            if let Some(org) = entry.config.get("org_id").and_then(|v| v.as_str()) {
                if !org.is_empty() { args.push("--org-id".into()); args.push(org.into()); }
            }
            if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                args.push("--model".into()); args.push(model.into());
            }
        }
        "anthropic" => {
            if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                args.push("--base-url".into()); args.push(base.into());
            }
            if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                args.push("--api-key".into()); args.push(key.into());
            }
            if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                args.push("--model".into()); args.push(model.into());
            }
        }
        _ => {}
    }
    // Convert to &str slice for run
    let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
    // Pass timeout through to CLI to avoid inner 5s default
    let mut args_with_timeout: Vec<String> = args.iter().cloned().collect();
    args_with_timeout.push("--timeout".into()); args_with_timeout.push("30".into());
    let v = run_cli_json(&args_with_timeout.iter().map(|s| s.as_str()).collect::<Vec<&str>>(), Duration::from_secs(30))?;
    let ok = v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false);
    let msg = v.get("message").and_then(|x| x.as_str()).unwrap_or("").to_string();
    if ok { Ok(msg) } else { Err(anyhow!(msg)) }
}
