use std::io;
use std::process::{Command, Stdio};
use std::time::Duration;

use anyhow::{anyhow, Result};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen};
use crossterm::{execute, event};
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Modifier, Style};
use ratatui::text::Span;
use ratatui::text::Line;
use serde_json::Value;

use crate::theme::Theme;

pub fn ensure_chi_llm() -> Result<()> {
    match Command::new("chi-llm").arg("--version").output() {
        Ok(_) => Ok(()),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Err(anyhow!(
            "Required CLI 'chi-llm' not found in PATH.\n\nInstall: pip install -e .[full] (inside repo) or pip install chi-llm (when published)."
        )),
        Err(e) => Err(anyhow!("Failed to execute 'chi-llm --version': {e}")),
    }
}

pub fn centered_rect(pct_x: u16, pct_y: u16, r: Rect) -> Rect {
    let popup_layout = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Percentage((100 - pct_y) / 2),
            Constraint::Percentage(pct_y),
            Constraint::Percentage((100 - pct_y) / 2),
        ])
        .split(r);
    let area = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage((100 - pct_x) / 2),
            Constraint::Percentage(pct_x),
            Constraint::Percentage((100 - pct_x) / 2),
        ])
        .split(popup_layout[1])[1];
    area
}

pub fn neon_gradient_line(text: &str, theme: &Theme) -> Line<'static> {
    let colors = [theme.primary, theme.accent, theme.secondary, theme.frame];
    let spans: Vec<Span> = text
        .chars()
        .enumerate()
        .map(|(i, ch)| {
            let c = colors[i % colors.len()];
            Span::styled(
                ch.to_string(),
                Style::default().fg(c).add_modifier(Modifier::BOLD),
            )
        })
        .collect();
    Line::from(spans)
}

pub fn run_cli_json(args: &[&str], timeout: Duration) -> Result<Value> {
    use wait_timeout::ChildExt;
    let mut cmd = Command::new("chi-llm");
    cmd.args(args).stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = cmd.spawn()?;
    match child.wait_timeout(timeout)? {
        Some(status) => {
            if !status.success() {
                let stderr = child
                    .stderr
                    .take()
                    .map(|mut s| {
                        use std::io::Read;
                        let mut buf = Vec::new();
                        let _ = s.read_to_end(&mut buf);
                        String::from_utf8_lossy(&buf).to_string()
                    })
                    .unwrap_or_default();
                return Err(anyhow!("chi-llm {:?} failed: {}", args, stderr));
            }
        }
        None => {
            let _ = child.kill();
            return Err(anyhow!("chi-llm {:?} timed out after {:?}", args, timeout));
        }
    }
    let output = child.wait_with_output()?;
    let val: Value = serde_json::from_slice(&output.stdout)?;
    Ok(val)
}

