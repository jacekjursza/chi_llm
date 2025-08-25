use anyhow::{anyhow, Result};
use ratatui::layout::Rect;
use ratatui::prelude::Frame;
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Paragraph, Wrap};
use serde_json::Value;

use crate::app::App;

#[derive(Copy, Clone, Debug, PartialEq, Eq, Default)]
pub enum BuildTarget {
    #[default]
    Project,
    Global,
}

#[derive(Clone, Debug, Default)]
pub struct BuildState {
    pub target: BuildTarget,
    pub status: Option<String>,
}

impl BuildState {
    pub fn toggle_target(&mut self) {
        self.target = match self.target {
            BuildTarget::Project => BuildTarget::Global,
            BuildTarget::Global => BuildTarget::Project,
        };
    }
}

pub fn draw_build_config(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = Vec::new();
    let target = app
        .build
        .as_ref()
        .map(|b| b.target)
        .unwrap_or(BuildTarget::Project);
    lines.push(Line::from(Span::styled(
        "Build/Write Configuration",
        Style::default()
            .fg(app.theme.primary)
            .add_modifier(Modifier::BOLD),
    )));
    lines.push(Line::from(match target {
        BuildTarget::Project => "Target: Project (.chi_llm.json)",
        BuildTarget::Global => "Target: Global (~/.cache/chi_llm/model_config.json)",
    }));
    // Show default provider summary
    match get_default_provider_summary() {
        Ok((id, ptype)) => lines.push(Line::from(format!(
            "Default provider: {} [{}]",
            id, ptype
        ))),
        Err(e) => lines.push(Line::from(Span::styled(
            format!("Default provider not set: {}", e),
            Style::default().fg(Color::Red),
        ))),
    }
    if let Some(st) = &app.build {
        if let Some(msg) = &st.status {
            lines.push(Line::from(Span::styled(
                msg.clone(),
                Style::default().fg(app.theme.secondary),
            )));
        }
    }
    lines.push(Line::from(
        "Press Enter to write; 'g' toggles target.",
    ));
    let p = Paragraph::new(lines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .border_style(Style::default().fg(app.theme.frame))
                .title("Build"),
        )
        .alignment(ratatui::layout::Alignment::Left)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

pub fn get_default_provider_summary() -> Result<(String, String)> {
    let path = ".chi_llm.tmp.json";
    let text = std::fs::read_to_string(path).map_err(|e| anyhow!("{}", e))?;
    let v: Value = serde_json::from_str(&text)?;
    let def = v
        .get("default_provider_id")
        .and_then(|x| x.as_str())
        .ok_or_else(|| anyhow!("no default_provider_id in .chi_llm.tmp.json"))?;
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("");
            if id == def {
                let ptype = p
                    .get("type")
                    .and_then(|x| x.as_str())
                    .unwrap_or("")
                    .to_string();
                return Ok((id.to_string(), ptype));
            }
        }
    }
    Err(anyhow!("default provider entry not found"))
}

pub fn write_active_config(target: BuildTarget) -> Result<String> {
    let path = ".chi_llm.tmp.json";
    let text = std::fs::read_to_string(path).map_err(|e| anyhow!("{}", e))?;
    let v: Value = serde_json::from_str(&text)?;
    let def = v
        .get("default_provider_id")
        .and_then(|x| x.as_str())
        .ok_or_else(|| anyhow!("no default_provider_id in .chi_llm.tmp.json"))?;
    let arr = v
        .get("providers")
        .and_then(|x| x.as_array())
        .ok_or_else(|| anyhow!("no providers array in .chi_llm.tmp.json"))?;
    let mut ptype = String::new();
    let mut cfg = serde_json::Map::new();
    for p in arr {
        let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("");
        if id == def {
            ptype = p
                .get("type")
                .and_then(|x| x.as_str())
                .unwrap_or("")
                .to_string();
            if let Some(c) = p.get("config").and_then(|x| x.as_object()) {
                for (k, val) in c {
                    if k == "type" {
                        continue;
                    }
                    // include only non-empty fields
                    let include = match val {
                        Value::Null => false,
                        Value::String(s) => !s.is_empty(),
                        _ => true,
                    };
                    if include {
                        cfg.insert(k.clone(), val.clone());
                    }
                }
            }
            break;
        }
    }
    if ptype.is_empty() {
        return Err(anyhow!("default provider type missing"));
    }
    // Map UI-specific local variants to canonical type for config
    let ptype_out = match ptype.as_str() {
        "local-zeroconfig" | "local-custom" => "local".to_string(),
        other => other.to_string(),
    };
    let mut out = serde_json::Map::new();
    let mut pmap = serde_json::Map::new();
    pmap.insert("type".to_string(), Value::String(ptype_out));
    for (k, v) in cfg {
        pmap.insert(k, v);
    }
    out.insert("provider".to_string(), Value::Object(pmap));
    let json = Value::Object(out);
    let written = match target {
        BuildTarget::Project => {
            let p = ".chi_llm.json";
            std::fs::write(p, serde_json::to_vec_pretty(&json)?)?;
            p.to_string()
        }
        BuildTarget::Global => {
            let home = dirs::home_dir().ok_or_else(|| anyhow!("home dir not found"))?;
            let dir = home.join(".cache").join("chi_llm");
            std::fs::create_dir_all(&dir)?;
            let p = dir.join("model_config.json");
            std::fs::write(&p, serde_json::to_vec_pretty(&json)?)?;
            p.to_string_lossy().to_string()
        }
    };
    Ok(written)
}
