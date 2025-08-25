use anyhow::Result;
use ratatui::layout::{Alignment, Constraint, Direction, Layout, Rect};
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};

use crate::app::App;

#[derive(Clone, Debug)]
pub struct TocEntry {
    pub level: u8,
    pub title: String,
    pub line: usize,
}

#[derive(Clone, Debug)]
pub struct ReadmeState {
    pub lines: Vec<String>,
    pub toc: Vec<TocEntry>,
    pub show_toc: bool,
    pub scroll: usize,
    pub focus_toc: bool,
    pub toc_selected: usize,
}

impl ReadmeState {
    pub fn scroll_up(&mut self, n: usize) {
        self.scroll = self.scroll.saturating_sub(n);
    }
    pub fn scroll_down(&mut self, n: usize) {
        self.scroll = self.scroll.saturating_add(n);
    }
}

pub fn load_readme() -> ReadmeState {
    let content = std::fs::read_to_string("README.md")
        .unwrap_or_else(|_| "# README not found\n\nPlace a README.md in the current directory.".to_string());
    let mut lines = Vec::new();
    let mut toc = Vec::new();
    for (idx, raw) in content.lines().enumerate() {
        let mut level = 0u8;
        let mut title = raw.to_string();
        if let Some(stripped) = raw.strip_prefix("### ") {
            level = 3;
            title = stripped.to_string();
        } else if let Some(stripped) = raw.strip_prefix("## ") {
            level = 2;
            title = stripped.to_string();
        } else if let Some(stripped) = raw.strip_prefix("# ") {
            level = 1;
            title = stripped.to_string();
        }
        if level > 0 {
            toc.push(TocEntry {
                level,
                title: title.clone(),
                line: idx,
            });
        }
        lines.push(raw.to_string());
    }
    ReadmeState {
        lines,
        toc,
        show_toc: false,
        scroll: 0,
        focus_toc: false,
        toc_selected: 0,
    }
}

pub fn draw_readme(f: &mut Frame, area: Rect, app: &App) {
    // Ensure loaded
    let mut rm = app.readme.clone().unwrap_or_else(load_readme);
    let show_toc = rm.show_toc;
    let chunks = if show_toc {
        Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(25), Constraint::Percentage(75)])
            .split(area)
    } else {
        Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Percentage(100)])
            .split(area)
    };

    if show_toc {
        let mut toc_items: Vec<ListItem> = Vec::new();
        for (i, e) in rm.toc.iter().enumerate() {
            let indent = match e.level {
                1 => "",
                2 => "  ",
                _ => "    ",
            };
            let style = if rm.focus_toc && i == rm.toc_selected {
                Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD)
            } else { Style::default().fg(app.theme.fg) };
            toc_items.push(ListItem::new(Line::from(Span::styled(format!("{}- {}", indent, e.title), style))));
        }
        let left_border = if rm.focus_toc { app.theme.selected } else { app.theme.frame };
        let list = List::new(toc_items).block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(left_border))
                .title("TOC"),
        );
        f.render_widget(list, chunks[0]);
    }

    // Render content with simple styling for headings
    let mut vlines: Vec<Line> = Vec::new();
    let start = rm.scroll.min(rm.lines.len());
    let max_rows = area.height.saturating_sub(2) as usize; // rough, accounting for borders
    for raw in rm.lines.iter().skip(start).take(max_rows) {
        if let Some(s) = raw.strip_prefix("# ") {
            vlines.push(Line::from(Span::styled(
                s.to_string(),
                Style::default()
                    .fg(app.theme.primary)
                    .add_modifier(Modifier::BOLD),
            )))
        } else if let Some(s) = raw.strip_prefix("## ") {
            vlines.push(Line::from(Span::styled(
                s.to_string(),
                Style::default()
                    .fg(app.theme.accent)
                    .add_modifier(Modifier::BOLD),
            )))
        } else if let Some(s) = raw.strip_prefix("### ") {
            vlines.push(Line::from(Span::styled(
                s.to_string(),
                Style::default().fg(app.theme.secondary),
            )))
        } else {
            vlines.push(Line::from(raw.as_str()));
        }
    }
    let right_border = if show_toc && !rm.focus_toc { app.theme.selected } else { app.theme.frame };
    let p = Paragraph::new(vlines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(right_border))
                .title("README"),
        )
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true });
    f.render_widget(p, chunks[if show_toc { 1 } else { 0 }]);

    // Note: caller updates app.readme via key handler (holds &mut App there)
}
