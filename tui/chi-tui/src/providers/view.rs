use std::time::Duration;

use anyhow::Result;
use ratatui::layout::{Rect, Layout, Direction, Constraint};
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap};
use reqwest::blocking::Client;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION};
use serde_json::Value;

use crate::app::App;
use crate::util::centered_rect;

use super::{ProvidersState, FormField};

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
        if let Some(status) = &st.test_status {
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
                    let p = Paragraph::new(format!("Type: {}  (Enter to change)", entry.ptype)).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(Block::default().borders(Borders::ALL).border_style(style));
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
                    let title_txt = if ff.schema.required { format!("* {}", ff.schema.name) } else { ff.schema.name.clone() };
                    let block = Block::default().borders(Borders::ALL).border_style(bstyle).title(title_txt);
                    let p = Paragraph::new(display).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).block(block).wrap(Wrap { trim: false });
                    f.render_widget(p, chunks[1 + i_vis]);
                }
                if let Some(form) = &st.form {
                    let mut msg = form.message.clone().unwrap_or_default();
                    if fields.len() > end { msg = format!("{}  ↓ more…", msg); }
                    if start > 0 { msg = format!("↑ more…  {}", msg); }
                    let p = Paragraph::new(msg).style(Style::default().bg(app.theme.bg).fg(app.theme.secondary)).block(Block::default());
                    f.render_widget(p, chunks[1 + visible.len()]);
                    let buttons_area = chunks[1 + visible.len() + 1];
                    let sel = form.selected;
                    let save_idx = fields.len() + 1;
                    let cancel_idx = fields.len() + 2;
                    let save_style = if sel == save_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    let cancel_style = if sel == cancel_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                    let btns = vec![Line::from(vec![Span::styled("[ Save ]  ", save_style), Span::styled("[ Cancel ]", cancel_style)])];
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

    // Draw an outer border around the right pane to indicate active focus
    if let Some(st) = &app.providers {
        let right_border = if st.focus_right { app.theme.selected } else { app.theme.frame };
        let outer = Block::default().borders(Borders::ALL).border_style(Style::default().fg(right_border));
        f.render_widget(outer, right);
    }

    // Overlay dropdown
    if let Some(st) = &app.providers {
        if let Some(dd) = &st.dropdown {
            let area_pop = centered_rect(50, 60, area);
            let mut items: Vec<ListItem> = Vec::new();
            for (i, it) in dd.items.iter().enumerate() {
                let style = if i == dd.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
                items.push(ListItem::new(Line::from(Span::styled(it.clone(), style))));
            }
            let list = List::new(items)
                .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(dd.title.clone()))
                .highlight_style(Style::default().fg(app.theme.selected));
            f.render_widget(Clear, area_pop);
            f.render_widget(list, area_pop);
        }
    }
}

pub fn probe_provider(entry: &super::state::ProviderScratchEntry) -> Result<String> {
    let ptype = entry.ptype.as_str();
    if ptype == "local" { return Ok("local: no network test".to_string()); }
    let client = Client::builder().timeout(Duration::from_secs(3)).build()?;
    match ptype {
        "lmstudio" => {
            let host = entry.config.get("host").and_then(|v| v.as_str()).unwrap_or("127.0.0.1");
            let port = entry.config.get("port").and_then(|v| v.as_u64()).unwrap_or(1234);
            let url = format!("http://{}:{}/v1/models", host, port);
            let resp = client.get(&url).send()?; let status = resp.status();
            if status.is_success() { let v: Value = resp.json()?; let count = v.get("data").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0); Ok(format!("lmstudio: {} models", count)) } else { Ok(format!("lmstudio: HTTP {}", status)) }
        }
        "ollama" => {
            let host = entry.config.get("host").and_then(|v| v.as_str()).unwrap_or("127.0.0.1");
            let port = entry.config.get("port").and_then(|v| v.as_u64()).unwrap_or(11434);
            let url = format!("http://{}:{}/api/tags", host, port);
            let resp = client.get(&url).send()?; let status = resp.status();
            if status.is_success() { let v: Value = resp.json()?; let count = v.get("models").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0); Ok(format!("ollama: {} tags", count)) } else { Ok(format!("ollama: HTTP {}", status)) }
        }
        "openai" => {
            let base = entry.config.get("base_url").and_then(|v| v.as_str()).unwrap_or("https://api.openai.com");
            let url = format!("{}/v1/models", base.trim_end_matches('/'));
            let key = entry.config.get("api_key").and_then(|v| v.as_str()).unwrap_or("");
            let org = entry.config.get("org_id").and_then(|v| v.as_str());
            if key.is_empty() { return Ok("openai: missing api_key".to_string()); }
            let mut headers = HeaderMap::new(); let authv = format!("Bearer {}", key);
            headers.insert(AUTHORIZATION, HeaderValue::from_str(&authv).unwrap_or(HeaderValue::from_static("")));
            if let Some(o) = org { headers.insert("OpenAI-Organization", HeaderValue::from_str(o).unwrap_or(HeaderValue::from_static(""))); }
            let resp = client.get(&url).headers(headers).send()?; let status = resp.status();
            if status.is_success() { let v: Value = resp.json()?; let count = v.get("data").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0); Ok(format!("openai: {} models", count)) } else { Ok(format!("openai: HTTP {}", status)) }
        }
        _ => Ok(format!("{}: no test implemented", ptype)),
    }
}
