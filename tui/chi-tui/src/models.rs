use std::time::Duration;

use anyhow::Result;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};
use serde_json::Value;

use crate::app::App;
use crate::util::run_cli_json;

#[derive(Clone, Debug)]
pub struct ModelEntry {
    pub id: String,
    pub name: String,
    pub size: Option<String>,
    pub file_size_mb: Option<u64>,
    pub context_window: Option<u64>,
    pub tags: Vec<String>,
    pub downloaded: bool,
    pub current: bool,
    pub raw: Value,
}

#[derive(Clone, Debug)]
pub struct ModelBrowser {
    pub entries: Vec<ModelEntry>,
    pub filtered: Vec<usize>,
    pub selected: usize, // index in filtered
    pub downloaded_only: bool,
    pub tag_filter: Option<String>,
    pub show_info: bool,
    pub all_tags: Vec<String>,
}

impl ModelBrowser {
    pub fn compute_filtered(&mut self) {
        self.filtered.clear();
        for (i, e) in self.entries.iter().enumerate() {
            if self.downloaded_only && !e.downloaded {
                continue;
            }
            if let Some(tag) = &self.tag_filter {
                if !e.tags.iter().any(|t| t == tag) {
                    continue;
                }
            }
            self.filtered.push(i);
        }
        if self.filtered.is_empty() {
            self.selected = 0;
        } else if self.selected >= self.filtered.len() {
            self.selected = self.filtered.len() - 1;
        }
    }
    pub fn move_up(&mut self) {
        if !self.filtered.is_empty() && self.selected > 0 {
            self.selected -= 1;
        }
    }
    pub fn move_down(&mut self) {
        if !self.filtered.is_empty() && self.selected + 1 < self.filtered.len() {
            self.selected += 1;
        }
    }
    pub fn toggle_downloaded_only(&mut self) {
        self.downloaded_only = !self.downloaded_only;
        self.compute_filtered();
    }
    pub fn cycle_tag(&mut self) {
        if self.all_tags.is_empty() {
            return;
        }
        match &self.tag_filter {
            None => {
                self.tag_filter = Some(self.all_tags[0].clone());
            }
            Some(cur) => {
                let mut idx = self
                    .all_tags
                    .iter()
                    .position(|t| t == cur)
                    .unwrap_or(0);
                idx = (idx + 1) % (self.all_tags.len() + 1); // +1 to allow none state
                if idx >= self.all_tags.len() {
                    self.tag_filter = None;
                } else {
                    self.tag_filter = Some(self.all_tags[idx].clone());
                }
            }
        }
        self.compute_filtered();
    }
    pub fn current_entry(&self) -> Option<&ModelEntry> {
        self.filtered.get(self.selected).map(|&i| &self.entries[i])
    }
}

pub fn fetch_models(timeout: Duration) -> Result<ModelBrowser> {
    let arr = run_cli_json(&["models", "list", "--json"], timeout)?;
    let mut entries: Vec<ModelEntry> = Vec::new();
    let mut tagset: std::collections::BTreeSet<String> =
        std::collections::BTreeSet::new();
    if let Some(list) = arr.as_array() {
        for v in list {
            let id = v.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = v
                .get("name")
                .and_then(|x| x.as_str())
                .unwrap_or(&id)
                .to_string();
            let size = v
                .get("size")
                .and_then(|x| x.as_str())
                .map(|s| s.to_string());
            let file_size_mb = v.get("file_size_mb").and_then(|x| x.as_u64());
            let context_window = v.get("context_window").and_then(|x| x.as_u64());
            let tags: Vec<String> = v
                .get("tags")
                .and_then(|x| x.as_array())
                .map(|a| {
                    a.iter()
                        .filter_map(|t| t.as_str().map(|s| s.to_string()))
                        .collect()
                })
                .unwrap_or_default();
            for t in &tags {
                tagset.insert(t.clone());
            }
            let downloaded = v
                .get("downloaded")
                .and_then(|x| x.as_bool())
                .unwrap_or(false);
            let current = v
                .get("current")
                .and_then(|x| x.as_bool())
                .unwrap_or(false);
            entries.push(ModelEntry {
                id,
                name,
                size,
                file_size_mb,
                context_window,
                tags,
                downloaded,
                current,
                raw: v.clone(),
            });
        }
    }
    let all_tags = tagset.into_iter().collect();
    let mut mb = ModelBrowser {
        entries,
        filtered: Vec::new(),
        selected: 0,
        downloaded_only: false,
        tag_filter: None,
        show_info: false,
        all_tags,
    };
    mb.compute_filtered();
    Ok(mb)
}

pub fn draw_model_browser(f: &mut Frame, area: Rect, app: &App) {
    let mut upper = area;
    let mut lower = area;
    let show_info = app.model.as_ref().map(|m| m.show_info).unwrap_or(false);
    if show_info {
        let chunks = Layout::default()
            .direction(Direction::Vertical)
            .constraints([Constraint::Percentage(70), Constraint::Percentage(30)])
            .split(area);
        upper = chunks[0];
        lower = chunks[1];
    }
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(mb) = &app.model {
        for (pos, &idx) in mb.filtered.iter().enumerate() {
            let e = &mb.entries[idx];
            let mut label = format!("{} {}", if pos == mb.selected { '›' } else { ' ' }, e.name);
            if e.current {
                label.push_str("  [current]");
            }
            if e.downloaded {
                label.push_str("  [downloaded]");
            }
            if let Some(ref tag) = mb.tag_filter {
                label.push_str(&format!("  [tag:{}]", tag));
            }
            let style = if pos == mb.selected {
                Style::default()
                    .fg(app.theme.selected)
                    .add_modifier(Modifier::BOLD)
            } else {
                Style::default().fg(app.theme.fg)
            };
            items.push(ListItem::new(Line::from(Span::styled(label, style))));
        }
    } else {
        items.push(ListItem::new("Loading models..."));
    }
    let title = if let Some(mb) = &app.model {
        let mut t = String::from("Models");
        if mb.downloaded_only {
            t.push_str(" • downloaded-only");
        }
        if let Some(tag) = &mb.tag_filter {
            t.push_str(&format!(" • tag:{}", tag));
        }
        t
    } else {
        String::from("Models")
    };
    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title(title),
        )
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, upper);

    if show_info {
        let mut lines: Vec<Line> = Vec::new();
        if let Some(mb) = &app.model {
            if let Some(e) = mb.current_entry() {
                lines.push(Line::from(Span::styled(
                    format!("{} ({})", e.name, e.id),
                    Style::default()
                        .fg(app.theme.primary)
                        .add_modifier(Modifier::BOLD),
                )));
                if let Some(s) = &e.size {
                    lines.push(Line::from(format!("size: {}", s)));
                }
                if let Some(fs) = e.file_size_mb {
                    lines.push(Line::from(format!("file_size_mb: {}", fs)));
                }
                if let Some(ctx) = e.context_window {
                    lines.push(Line::from(format!("context_window: {}", ctx)));
                }
                if !e.tags.is_empty() {
                    lines.push(Line::from(format!("tags: {}", e.tags.join(", "))));
                }
            }
        }
        let p = Paragraph::new(lines)
            .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
            .block(
                Block::default()
                    .borders(Borders::ALL)
                    .border_style(Style::default().fg(app.theme.frame))
                    .title("Info"),
            )
            .alignment(ratatui::layout::Alignment::Left)
            .wrap(Wrap { trim: true });
        f.render_widget(p, lower);
    }
}

