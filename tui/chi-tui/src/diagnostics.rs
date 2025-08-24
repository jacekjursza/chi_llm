use std::time::Duration;

use anyhow::Result;
use ratatui::layout::Rect;
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use ratatui::prelude::Frame;
use serde_json::Value;

use crate::app::App;
use crate::theme::Theme;
use crate::util::run_cli_json;

#[derive(Clone, Debug)]
pub struct DiagState {
    pub summary: Vec<String>,
    pub diagnostics: Value,
    pub model_explain: Value,
    pub saved_path: Option<String>,
}

pub fn fetch_diagnostics(timeout: Duration) -> Result<DiagState> {
    let diag = run_cli_json(&["diagnostics", "--json"], timeout)?;
    let explain = run_cli_json(&["models", "current", "--explain", "--json"], timeout)?;
    let mut summary = Vec::new();
    if let Some(py) = diag
        .get("python")
        .and_then(|v| v.get("version"))
        .and_then(|v| v.as_str())
    {
        summary.push(format!("python: {}", py));
    }
    if let Some(cfg_src) = explain.get("config_source").and_then(|v| v.as_str()) {
        summary.push(format!("config_source: {}", cfg_src));
    }
    if let Some(cur) = explain.get("current_model").and_then(|v| v.as_str()) {
        summary.push(format!("current_model: {}", cur));
    }
    if let Some(rec) = explain.get("recommended_model").and_then(|v| v.as_str()) {
        summary.push(format!("recommended_model: {}", rec));
    }
    if let Some(ram) = explain.get("available_ram_gb").and_then(|v| v.as_f64()) {
        summary.push(format!("available_ram_gb: {:.1}", ram));
    }
    Ok(DiagState {
        summary,
        diagnostics: diag,
        model_explain: explain,
        saved_path: None,
    })
}

pub fn export_diagnostics(d: &DiagState) -> Result<String> {
    let obj = serde_json::json!({
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "diagnostics": d.diagnostics,
        "model_explain": d.model_explain,
    });
    let path = "chi_llm_diagnostics.json".to_string();
    std::fs::write(&path, serde_json::to_vec_pretty(&obj)?)?;
    Ok(path)
}

pub fn draw_diagnostics(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = Vec::new();
    if let Some(err) = &app.last_error {
        lines.push(Line::from(Span::styled(
            err.clone(),
            Style::default().fg(Color::Red),
        )));
    }
    if let Some(diag) = &app.diag {
        lines.push(Line::from(Span::styled(
            "Diagnostics summary:",
            Style::default()
                .fg(app.theme.primary)
                .add_modifier(Modifier::BOLD),
        )));
        for s in &diag.summary {
            lines.push(Line::from(s.as_str()));
        }
        if let Some(path) = &diag.saved_path {
            lines.push(Line::from(Span::styled(
                format!("Exported: {}", path),
                Style::default().fg(app.theme.secondary),
            )));
        }
    } else {
        lines.push(Line::from("Loading diagnostics..."));
    }
    let p = Paragraph::new(lines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title("Diagnostics"),
        )
        .alignment(ratatui::layout::Alignment::Left)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

