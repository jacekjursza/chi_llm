use std::io::{self, Stdout};
use std::time::{Duration, Instant};
use std::process::Command;
use std::process::Stdio;

use anyhow::{anyhow, Result};
use clap::Parser;
use crossterm::event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEvent, KeyModifiers};
use crossterm::execute;
use crossterm::terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Alignment, Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Borders, Clear, List, ListItem, Paragraph, Wrap};
use ratatui::Terminal;
use ratatui::prelude::Frame;
use serde_json::Value;
use wait_timeout::ChildExt;

#[derive(Parser, Debug)]
#[command(name = "chi-tui")] 
#[command(about = "Terminal UI for chi-llm (Rust/ratatui)", long_about = None)]
struct Args {
    /// Do not use alternate screen buffer
    #[arg(long = "no-alt")]
    no_alt: bool,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
enum Page {
    Welcome,
    Readme,
    Configure,
    SelectDefault,
    ModelBrowser,
    Diagnostics,
    Build,
    Settings,
}

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
enum ThemeMode { Light, Dark }

#[derive(Clone, Debug)]
struct Theme {
    mode: ThemeMode,
    bg: Color,
    fg: Color,
    primary: Color,
    secondary: Color,
    accent: Color,
    frame: Color,
    selected: Color,
}

impl Theme {
    fn synthwave_dark() -> Self {
        // Retro/synthwave palette
        Self {
            mode: ThemeMode::Dark,
            bg: Color::Rgb(10, 8, 20),
            fg: Color::Rgb(220, 220, 235),
            primary: Color::Rgb(255, 0, 153),   // neon magenta
            secondary: Color::Rgb(0, 255, 255), // cyan
            accent: Color::Rgb(64, 160, 255),   // electric blue
            frame: Color::Rgb(120, 80, 200),
            selected: Color::Rgb(255, 120, 0),  // neon orange
        }
    }
    fn toggle(&mut self) { self.mode = match self.mode { ThemeMode::Dark => ThemeMode::Light, ThemeMode::Light => ThemeMode::Dark }; }
}

struct App {
    page: Page,
    menu_idx: usize,
    show_help: bool,
    anim: bool,
    tick: u64,
    last_tick: Instant,
    theme: Theme,
    use_alt: bool,
    should_quit: bool,
    // diagnostics
    diag: Option<DiagState>,
    last_error: Option<String>,
}

impl App {
    fn new(use_alt: bool) -> Self {
        Self {
            page: Page::Welcome,
            menu_idx: 0,
            show_help: false,
            anim: true,
            tick: 0,
            last_tick: Instant::now(),
            theme: Theme::synthwave_dark(),
            use_alt,
            should_quit: false,
            diag: None,
            last_error: None,
        }
    }
}

fn main() -> Result<()> {
    let args = Args::parse();
    ensure_chi_llm()?;

    // Terminal setup
    if !args.no_alt { enable_raw_mode()?; } else { enable_raw_mode()?; }
    let mut stdout = io::stdout();
    if !args.no_alt { execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?; } else { execute!(stdout, EnableMouseCapture)?; }
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let res = run_app(&mut terminal, App::new(!args.no_alt));

    // Restore terminal
    disable_raw_mode()?;
    let mut stdout = io::stdout();
    if !args.no_alt { execute!(stdout, LeaveAlternateScreen, DisableMouseCapture)?; } else { execute!(stdout, DisableMouseCapture)?; }
    terminal.show_cursor()?;

    if let Err(err) = res { eprintln!("\nError: {err}"); std::process::exit(1); }
    Ok(())
}

fn ensure_chi_llm() -> Result<()> {
    match Command::new("chi-llm").arg("--version").output() {
        Ok(_) => Ok(()),
        Err(e) if e.kind() == io::ErrorKind::NotFound => Err(anyhow!(
            "Required CLI 'chi-llm' not found in PATH.\n\nInstall: pip install -e .[full] (inside repo) or pip install chi-llm (when published)."
        )),
        Err(e) => Err(anyhow!("Failed to execute 'chi-llm --version': {e}")),
    }
}

fn run_app(terminal: &mut Terminal<CrosstermBackend<Stdout>>, mut app: App) -> Result<()> {
    let tick_rate = Duration::from_millis(100);
    loop {
        terminal.draw(|f| ui(f, &app))?;
        // ticks
        let timeout = tick_rate.saturating_sub(app.last_tick.elapsed());
        if event::poll(timeout)? {
            if let Event::Key(key) = event::read()? {
                // Diagnostics page extra keys
                if app.page == Page::Diagnostics {
                    match key.code {
                        KeyCode::Char('e') | KeyCode::Char('E') => {
                            if let Some(diag) = &app.diag {
                                match export_diagnostics(diag) {
                                    Ok(path) => {
                                        if let Some(d) = &mut app.diag.clone() {
                                            let mut d2 = d.clone();
                                            d2.saved_path = Some(path);
                                            app.diag = Some(d2);
                                        }
                                    }
                                    Err(e) => app.last_error = Some(format!("Export failed: {e}")),
                                }
                            }
                            continue;
                        }
                        KeyCode::Char('r') | KeyCode::Char('R') => {
                            match fetch_diagnostics(Duration::from_secs(5)) {
                                Ok(d) => app.diag = Some(d),
                                Err(e) => app.last_error = Some(format!("Diagnostics failed: {e}")),
                            }
                            continue;
                        }
                        _ => {}
                    }
                }
                handle_key(&mut app, key);
            }
        }
        if app.last_tick.elapsed() >= tick_rate {
            app.tick = app.tick.wrapping_add(1);
            app.last_tick = Instant::now();
        }
        if app.should_quit { break; }
    }
    Ok(())
}

fn handle_key(app: &mut App, key: KeyEvent) {
    // Ctrl+C / q always quits
    if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) { app.should_quit = true; return; }
    match key.code {
        KeyCode::Char('q') => { app.should_quit = true; }
        KeyCode::Char('?') => { app.show_help = !app.show_help; }
        KeyCode::Char('t') => { app.theme.toggle(); }
        KeyCode::Char('a') => { app.anim = !app.anim; }
        KeyCode::Char('1') => app.page = Page::Readme,
        KeyCode::Char('2') => app.page = Page::Configure,
        KeyCode::Char('3') => app.page = Page::SelectDefault,
        KeyCode::Char('4') => {
            app.page = Page::Diagnostics;
            if app.diag.is_none() {
                match fetch_diagnostics(Duration::from_secs(5)) {
                    Ok(d) => app.diag = Some(d),
                    Err(e) => app.last_error = Some(format!("Diagnostics failed: {e}")),
                }
            }
        }
        KeyCode::Char('b') | KeyCode::Char('B') => app.page = Page::Build,
        KeyCode::Char('s') | KeyCode::Char('S') => app.page = Page::Settings,
        KeyCode::Esc => {
            if app.show_help { app.show_help = false; }
            else if app.page != Page::Welcome { app.page = Page::Welcome; }
            else { app.should_quit = true; }
        }
        _ => {}
    }

    // Welcome-specific navigation
    if app.page == Page::Welcome {
        match key.code {
            KeyCode::Up => { if app.menu_idx > 0 { app.menu_idx -= 1; } },
            KeyCode::Down => { if app.menu_idx < WELCOME_ITEMS.len() - 1 { app.menu_idx += 1; } },
            KeyCode::Enter => {
                app.page = WELCOME_ITEMS[app.menu_idx].1;
                if app.page == Page::Diagnostics && app.diag.is_none() {
                    match fetch_diagnostics(Duration::from_secs(5)) {
                        Ok(d) => app.diag = Some(d),
                        Err(e) => app.last_error = Some(format!("Diagnostics failed: {e}")),
                    }
                }
            }
            _ => {}
        }
    }
}

const WELCOME_ITEMS: &[(&str, Page)] = &[
    ("README", Page::Readme),
    ("Configure Providers", Page::Configure),
    ("Select Default", Page::SelectDefault),
    ("Diagnostics", Page::Diagnostics),
    ("Build Configuration", Page::Build),
    ("Settings", Page::Settings),
    ("Model Browser", Page::ModelBrowser),
    ("EXIT", Page::Welcome),
];

fn ui(f: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(6), // header with animation space
            Constraint::Min(3),
            Constraint::Length(1), // footer
        ]).split(f.size());

    draw_header(f, chunks[0], app);
    match app.page {
        Page::Welcome => draw_welcome(f, chunks[1], app),
        Page::Readme => draw_stub(f, chunks[1], app, "README Viewer (stub) — use 1/2/3/4/b/s or Esc"),
        Page::Configure => draw_stub(f, chunks[1], app, "Configure Providers (stub) — A/S/D/T/m to be implemented"),
        Page::SelectDefault => draw_stub(f, chunks[1], app, "Select Default (stub) — Enter to set"),
        Page::ModelBrowser => draw_stub(f, chunks[1], app, "Model Browser (stub) — r/f/i filters, Enter to select"),
        Page::Diagnostics => draw_diagnostics(f, chunks[1], app),
        Page::Build => draw_stub(f, chunks[1], app, "Build Config (stub) — Project/Global"),
        Page::Settings => draw_stub(f, chunks[1], app, "Settings (stub) — t/a toggles"),
    }
    draw_footer(f, chunks[2], app);

    if app.show_help { draw_help_overlay(f, app); }
}

fn draw_header(f: &mut Frame, area: Rect, app: &App) {
    let title = neon_gradient_line(" chi_llm — micro‑LLM • TUI vNext ", app);
    let sub = Line::from(vec![
        Span::styled("  retro/synthwave • arrows + enter • ? help ", Style::default().fg(app.theme.secondary)),
    ]);
    let block = Block::default()
        .borders(Borders::BOTTOM)
        .border_style(Style::default().fg(app.theme.frame))
        .title(Span::styled("CHI_TUI", Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD)))
        .title_alignment(Alignment::Center);
    let v = vec![title, sub];
    let p = Paragraph::new(v)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(block)
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

fn draw_footer(f: &mut Frame, area: Rect, app: &App) {
    let msg_text = match app.page {
        Page::Diagnostics => "Esc: back • q: quit • e: export • r: refresh • ?: help",
        _ => "Esc: back • q: quit • 1/2/3/4/b/s: sections • ?: help",
    };
    let msg = Line::from(Span::styled(msg_text, Style::default().fg(app.theme.secondary)));
    let p = Paragraph::new(msg)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default())
        .alignment(Alignment::Center);
    f.render_widget(p, area);
}

fn draw_welcome(f: &mut Frame, area: Rect, app: &App) {
    let items: Vec<ListItem> = WELCOME_ITEMS.iter().enumerate().map(|(i, (label, _))| {
        let style = if i == app.menu_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
        ListItem::new(Line::from(Span::styled(format!("{} {}", if i == app.menu_idx {"›"} else {" "}, label), style)))
    }).collect();
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Welcome"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);
}

fn draw_stub(f: &mut Frame, area: Rect, app: &App, text: &str) {
    let p = Paragraph::new(text)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)))
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

fn draw_help_overlay(f: &mut Frame, app: &App) {
    let area = centered_rect(70, 60, f.size());
    let lines = vec![
        Line::from(Span::styled("Global keys:", Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))),
        Line::from("Up/Down: navigate • Enter: select • Esc: back • q/Ctrl+C: quit"),
        Line::from("1: README • 2: Configure • 3: Select Default • 4: Diagnostics • b: Build • s: Settings"),
        Line::from("?: help overlay • t: theme • a: animation"),
        Line::from("Diagnostics: e export • r refresh"),
        Line::from("Welcome: Up/Down + Enter to open a section"),
        Line::from("—").style(Style::default().fg(app.theme.frame)),
        Line::from("This is a scaffold. Pages will be implemented in tasks 003–009."),
    ];
    let block = Block::default().title("Help").borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame));
    let content = Paragraph::new(lines).style(Style::default().bg(app.theme.bg).fg(app.theme.fg)).alignment(Alignment::Left).wrap(Wrap { trim: true }).block(block);
    f.render_widget(Clear, area);
    f.render_widget(content, area);
}

fn centered_rect(pct_x: u16, pct_y: u16, r: Rect) -> Rect {
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

fn neon_gradient_line(text: &str, app: &App) -> Line<'static> {
    // Simple alternating gradient across characters
    let colors = [app.theme.primary, app.theme.accent, app.theme.secondary, app.theme.frame];
    let spans: Vec<Span> = text.chars().enumerate().map(|(i, ch)| {
        let c = colors[i % colors.len()];
        Span::styled(ch.to_string(), Style::default().fg(c).add_modifier(Modifier::BOLD))
    }).collect();
    Line::from(spans)
}

#[derive(Clone, Debug)]
struct DiagState {
    summary: Vec<String>,
    diagnostics: Value,
    model_explain: Value,
    saved_path: Option<String>,
}

fn fetch_diagnostics(timeout: Duration) -> Result<DiagState> {
    let diag = run_cli_json(&["diagnostics", "--json"], timeout)?;
    let explain = run_cli_json(&["models", "current", "--explain", "--json"], timeout)?;
    // Build a few summary lines
    let mut summary = Vec::new();
    if let Some(py) = diag.get("python").and_then(|v| v.get("version")).and_then(|v| v.as_str()) {
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
    Ok(DiagState { summary, diagnostics: diag, model_explain: explain, saved_path: None })
}

fn export_diagnostics(d: &DiagState) -> Result<String> {
    let obj = serde_json::json!({
        "timestamp": chrono::Utc::now().to_rfc3339(),
        "diagnostics": d.diagnostics,
        "model_explain": d.model_explain,
    });
    let path = "chi_llm_diagnostics.json".to_string();
    std::fs::write(&path, serde_json::to_vec_pretty(&obj)?)?;
    Ok(path)
}

fn run_cli_json(args: &[&str], timeout: Duration) -> Result<Value> {
    let mut cmd = Command::new("chi-llm");
    cmd.args(args).stdout(Stdio::piped()).stderr(Stdio::piped());
    let mut child = cmd.spawn()?;
    match child.wait_timeout(timeout)? {
        Some(status) => {
            if !status.success() {
                let stderr = child.stderr.take().map(|mut s| {
                    use std::io::Read; let mut buf = Vec::new(); let _ = s.read_to_end(&mut buf); String::from_utf8_lossy(&buf).to_string()
                }).unwrap_or_default();
                return Err(anyhow!("chi-llm {:?} failed: {}", args, stderr));
            }
        }
        None => {
            // timed out
            let _ = child.kill();
            return Err(anyhow!("chi-llm {:?} timed out after {:?}", args, timeout));
        }
    }
    let output = child.wait_with_output()?;
    let val: Value = serde_json::from_slice(&output.stdout)?;
    Ok(val)
}

fn draw_diagnostics(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = Vec::new();
    if let Some(err) = &app.last_error { lines.push(Line::from(Span::styled(err.clone(), Style::default().fg(Color::Red)))); }
    if let Some(diag) = &app.diag {
        lines.push(Line::from(Span::styled("Diagnostics summary:", Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))));
        for s in &diag.summary { lines.push(Line::from(s.as_str())); }
        if let Some(path) = &diag.saved_path { lines.push(Line::from(Span::styled(format!("Exported: {}", path), Style::default().fg(app.theme.secondary)))); }
    } else {
        lines.push(Line::from("Loading diagnostics..."));
    }
    let p = Paragraph::new(lines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Diagnostics"))
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}
