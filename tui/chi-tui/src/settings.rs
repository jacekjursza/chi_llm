use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::prelude::Frame;
use ratatui::style::{Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, List, ListItem, Paragraph, Wrap};

use crate::app::App;

pub fn draw_settings(f: &mut Frame, area: Rect, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),
            Constraint::Min(3),
            Constraint::Length(2),
        ])
        .split(area);

    // Title/legend
    let title = Paragraph::new(
        Line::from(vec![
            Span::styled("Settings ", Style::default().fg(app.theme.primary)),
            Span::styled("— use Up/Down, Enter to toggle; t/a also work", Style::default().fg(app.theme.secondary)),
        ])
    )
    .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
    .block(
        Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(app.theme.frame)),
    )
    .wrap(Wrap { trim: false });
    f.render_widget(title, chunks[0]);

    // Items
    let theme_mode = match app.theme.mode {
        crate::theme::ThemeMode::Dark => "Dark",
        crate::theme::ThemeMode::Light => "Light",
    };
    let anim_status = if app.anim { "On" } else { "Off" };

    let mut items: Vec<ListItem> = Vec::new();
    for (pos, (label, value)) in [
        ("Theme", theme_mode.to_string()),
        ("Animation", anim_status.to_string()),
    ]
    .into_iter()
    .enumerate()
    {
        let marker = if pos == app.settings_idx { '›' } else { ' ' };
        let style = if pos == app.settings_idx {
            Style::default()
                .fg(app.theme.selected)
                .add_modifier(Modifier::BOLD)
        } else {
            Style::default().fg(app.theme.fg)
        };
        items.push(ListItem::new(Line::from(vec![
            Span::styled(format!("{} {}: ", marker, label), Style::default().fg(app.theme.secondary)),
            Span::styled(value, style),
        ])));
    }

    let list = List::new(items)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title("Preferences"),
        )
        .highlight_style(Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD));
    f.render_widget(list, chunks[1]);

    // Footer hints
    let footer = Paragraph::new(
        Line::from("t: Toggle theme • a: Toggle animation • Esc: Back")
    )
    .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
    .block(
        Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(app.theme.frame)),
    );
    f.render_widget(footer, chunks[2]);
}
