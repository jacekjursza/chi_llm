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
use std::fs;
use reqwest::blocking::Client;
use reqwest::header::{AUTHORIZATION, HeaderMap, HeaderValue};
use dirs;

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
    // model browser
    model: Option<ModelBrowser>,
    selected_model_id: Option<String>,
    // readme viewer
    readme: Option<ReadmeState>,
    // select default provider
    defaultp: Option<DefaultProviderState>,
    // providers catalog
    providers: Option<ProvidersState>,
    // build config
    build: Option<BuildState>,
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
            model: None,
            selected_model_id: None,
            readme: None,
            defaultp: None,
            providers: None,
            build: None,
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

    // README keys
    if app.page == Page::Readme {
        if app.readme.is_none() {
            app.readme = Some(load_readme());
        }
        if let Some(rm) = &mut app.readme {
            match key.code {
                KeyCode::Up => rm.scroll_up(1),
                KeyCode::Down => rm.scroll_down(1),
                KeyCode::PageUp => rm.scroll_up(8),
                KeyCode::PageDown => rm.scroll_down(8),
                KeyCode::Char('h') | KeyCode::Char('H') => rm.show_toc = !rm.show_toc,
                _ => {}
            }
        }
    }

    // Model Browser keys
    if app.page == Page::ModelBrowser {
        if app.model.is_none() {
            match fetch_models(Duration::from_secs(5)) {
                Ok(m) => app.model = Some(m),
                Err(e) => app.last_error = Some(format!("Models failed: {e}")),
            }
        }
        if let Some(m) = &mut app.model {
            match key.code {
                KeyCode::Up => m.move_up(),
                KeyCode::Down => m.move_down(),
                KeyCode::Char('r') | KeyCode::Char('R') => m.toggle_downloaded_only(),
                KeyCode::Char('f') | KeyCode::Char('F') => m.cycle_tag(),
                KeyCode::Char('i') | KeyCode::Char('I') => m.show_info = !m.show_info,
                KeyCode::Enter => {
                    if let Some(cur) = m.current_entry() { app.selected_model_id = Some(cur.id.clone()); }
                    app.page = Page::Configure; // return to configure with selected model id
                }
                _ => {}
            }
        }
    }

    // Select Default provider keys
    if app.page == Page::SelectDefault {
        if app.defaultp.is_none() {
            match load_providers_scratch() {
                Ok(s) => app.defaultp = Some(s),
                Err(e) => app.last_error = Some(format!("Load providers failed: {e}")),
            }
        }
        if let Some(s) = &mut app.defaultp {
            match key.code {
                KeyCode::Up => { if !s.providers.is_empty() && s.selected > 0 { s.selected -= 1; } },
                KeyCode::Down => { if !s.providers.is_empty() && s.selected + 1 < s.providers.len() { s.selected += 1; } },
                KeyCode::Enter | KeyCode::Char('s') | KeyCode::Char('S') => {
                    if let Some(p) = s.providers.get(s.selected) {
                        s.current_default_id = Some(p.id.clone());
                        if let Err(e) = save_default_provider(&p.id) {
                            app.last_error = Some(format!("Save default failed: {e}"));
                        }
                    }
                }
                _ => {}
            }
        }
    }

    // Configure Providers keys
    if app.page == Page::Configure {
        if app.providers.is_none() {
            app.providers = Some(match load_providers_state() {
                Ok(s) => s,
                Err(e) => { app.last_error = Some(format!("Load providers failed: {e}")); ProvidersState::empty() }
            });
        }
        if let Some(st) = &mut app.providers {
            // Editing mode
            if let Some(edit) = &mut st.edit {
                match key.code {
                    KeyCode::Esc => { st.edit = None; }
                    KeyCode::Enter => {
                        if st.selected < st.entries.len() {
                            let entry = &mut st.entries[st.selected];
                            let val = match edit.field.as_str() {
                                "port" => edit.buffer.parse::<u16>().map(|n| Value::Number(n.into())).unwrap_or(Value::String(edit.buffer.clone())),
                                _ => Value::String(edit.buffer.clone()),
                            };
                            if let Some(obj) = entry.config.as_object_mut() {
                                obj.insert(edit.field.clone(), val);
                            }
                        }
                        st.edit = None;
                    }
                    KeyCode::Backspace => { edit.buffer.pop(); }
                    KeyCode::Char(c) => { edit.buffer.push(c); }
                    _ => {}
                }
                return;
            }

            match key.code {
                KeyCode::Up => { if st.selected > 0 { st.selected -= 1; } },
                KeyCode::Down => { if st.selected + 1 < st.len_with_add() { st.selected += 1; } },
                KeyCode::Enter => {
                    if st.is_add_row() { st.add_default(); }
                }
                KeyCode::Char('a') | KeyCode::Char('A') => { st.add_default(); }
                KeyCode::Char('d') | KeyCode::Char('D') => { st.delete_selected(); }
                KeyCode::Char('s') | KeyCode::Char('S') => {
                    if let Err(e) = st.save() { app.last_error = Some(format!("Save failed: {e}")); }
                }
                KeyCode::Char('m') | KeyCode::Char('M') => {
                    app.page = Page::ModelBrowser;
                }
                KeyCode::Char('e') | KeyCode::Char('E') => {
                    if st.selected < st.entries.len() {
                        let cur = st.entries[st.selected].config.get("model").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        st.edit = Some(EditState{ field: "model".to_string(), buffer: cur });
                    }
                }
                KeyCode::Char('h') | KeyCode::Char('H') => {
                    if st.selected < st.entries.len() {
                        let cur = st.entries[st.selected].config.get("host").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        st.edit = Some(EditState{ field: "host".to_string(), buffer: cur });
                    }
                }
                KeyCode::Char('p') | KeyCode::Char('P') => {
                    if st.selected < st.entries.len() {
                        let cur = st.entries[st.selected].config.get("port").map(|v| v.to_string()).unwrap_or_default();
                        st.edit = Some(EditState{ field: "port".to_string(), buffer: cur });
                    }
                }
                KeyCode::Char('k') | KeyCode::Char('K') => {
                    if st.selected < st.entries.len() {
                        let cur = st.entries[st.selected].config.get("api_key").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        st.edit = Some(EditState{ field: "api_key".to_string(), buffer: cur });
                    }
                }
                KeyCode::Char('b') | KeyCode::Char('B') => {
                    if st.selected < st.entries.len() {
                        let cur = st.entries[st.selected].config.get("base_url").and_then(|v| v.as_str()).unwrap_or("").to_string();
                        st.edit = Some(EditState{ field: "base_url".to_string(), buffer: cur });
                    }
                }
                KeyCode::Char('t') | KeyCode::Char('T') => {
                    if st.selected < st.entries.len() {
                        match probe_provider(&st.entries[st.selected]) {
                            Ok(msg) => st.test_status = Some(msg),
                            Err(e) => st.test_status = Some(format!("Error: {}", e)),
                        }
                    }
                }
                _ => {}
            }
            // If a model was picked in model browser, apply to selected provider
            if let Some(model_id) = app.selected_model_id.take() {
                st.apply_model_to_selected(&model_id);
            }
        }
    }

    // Build/Write Configuration keys
    if app.page == Page::Build {
        if app.build.is_none() {
            app.build = Some(BuildState::default());
        }
        if let Some(st) = &mut app.build {
            match key.code {
                KeyCode::Char('g') | KeyCode::Char('G') => { st.toggle_target(); }
                KeyCode::Enter => {
                    match write_active_config(st.target) {
                        Ok(path) => st.status = Some(format!("Written: {}", path)),
                        Err(e) => st.status = Some(format!("Error: {}", e)),
                    }
                }
                _ => {}
            }
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
        Page::Readme => draw_readme(f, chunks[1], app),
        Page::Configure => draw_providers_catalog(f, chunks[1], app),
        Page::SelectDefault => draw_select_default(f, chunks[1], app),
        Page::ModelBrowser => draw_model_browser(f, chunks[1], app),
        Page::Diagnostics => draw_diagnostics(f, chunks[1], app),
        Page::Build => draw_build_config(f, chunks[1], app),
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
        Page::Readme => "Up/Down scroll • PgUp/PgDn faster • h TOC • Esc back",
        Page::ModelBrowser => "Up/Down select • Enter choose • r downloaded-only • f tag filter • i info • Esc back",
        Page::Build => "g toggle target • Enter write • Esc back",
        Page::SelectDefault => "Up/Down select • Enter set default • Esc back",
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
        Line::from("Model Browser: r downloaded-only • f cycle tag • i info"),
        Line::from("Configure: Up/Down • Enter/A add • D delete • S save • m model • E model • H host • P port • K key • B base_url • T test"),
        Line::from("README: Up/Down/PgUp/PgDn scroll • h TOC"),
        Line::from("Build: g toggle Project/Global • Enter write"),
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

#[derive(Clone, Debug)]
struct ProviderEntry { id: String, name: String, ptype: String, tags: Vec<String> }

#[derive(Clone, Debug)]
struct DefaultProviderState {
    providers: Vec<ProviderEntry>,
    selected: usize,
    current_default_id: Option<String>,
}

fn load_providers_scratch() -> Result<DefaultProviderState> {
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{}".to_string());
    let v: Value = serde_json::from_str(&text)?;
    let mut providers: Vec<ProviderEntry> = Vec::new();
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = p.get("name").and_then(|x| x.as_str()).unwrap_or(&id).to_string();
            let ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let tags: Vec<String> = p.get("tags").and_then(|x| x.as_array()).map(|a| a.iter().filter_map(|t| t.as_str().map(|s| s.to_string())).collect()).unwrap_or_default();
            if !id.is_empty() { providers.push(ProviderEntry { id, name, ptype, tags }); }
        }
    }
    let current_default_id = v.get("default_provider_id").and_then(|x| x.as_str()).map(|s| s.to_string());
    Ok(DefaultProviderState { providers, selected: 0, current_default_id })
}

fn save_default_provider(id: &str) -> Result<()> {
    let path = "chi.tmp.json";
    let mut root: Value = if let Ok(text) = fs::read_to_string(path) { serde_json::from_str(&text).unwrap_or_else(|_| Value::Object(Default::default())) } else { Value::Object(Default::default()) };
    if !root.is_object() { root = Value::Object(Default::default()); }
    if let Some(obj) = root.as_object_mut() {
        obj.insert("default_provider_id".to_string(), Value::String(id.to_string()));
    }
    fs::write(path, serde_json::to_vec_pretty(&root)?)?;
    Ok(())
}

fn draw_select_default(f: &mut Frame, area: Rect, app: &App) {
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.defaultp {
        for (i, p) in st.providers.iter().enumerate() {
            let mut label = format!("{} {} [{}]", if i == st.selected {"›"} else {" "}, p.name, p.ptype);
            if let Some(cur) = &st.current_default_id { if cur == &p.id { label.push_str("  [default]"); } }
            if !p.tags.is_empty() { label.push_str(&format!("  [{}]", p.tags.join(","))); }
            let style = if i == st.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
            items.push(ListItem::new(Line::from(Span::styled(label, style))))
        }
        if st.providers.is_empty() {
            items.push(ListItem::new("No providers found in chi.tmp.json → Configure first."));
        }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Select Default Provider"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);
}

#[derive(Clone, Debug)]
struct TocEntry { level: u8, title: String, line: usize }

#[derive(Clone, Debug)]
struct ReadmeState {
    lines: Vec<String>,
    toc: Vec<TocEntry>,
    show_toc: bool,
    scroll: usize,
}

impl ReadmeState {
    fn scroll_up(&mut self, n: usize) { self.scroll = self.scroll.saturating_sub(n); }
    fn scroll_down(&mut self, n: usize) { self.scroll = self.scroll.saturating_add(n); }
}

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
enum BuildTarget { Project, Global }

#[derive(Clone, Debug, Default)]
struct BuildState { target: BuildTarget, status: Option<String> }

impl Default for BuildTarget { fn default() -> Self { BuildTarget::Project } }

impl BuildState { fn toggle_target(&mut self) { self.target = match self.target { BuildTarget::Project => BuildTarget::Global, BuildTarget::Global => BuildTarget::Project }; } }

fn draw_build_config(f: &mut Frame, area: Rect, app: &App) {
    let mut lines: Vec<Line> = Vec::new();
    let target = app.build.as_ref().map(|b| b.target).unwrap_or(BuildTarget::Project);
    lines.push(Line::from(Span::styled("Build/Write Configuration", Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))));
    lines.push(Line::from(match target { BuildTarget::Project => "Target: Project (.chi_llm.json)", BuildTarget::Global => "Target: Global (~/.cache/chi_llm/model_config.json)" }));
    // Show default provider summary
    match get_default_provider_summary() {
        Ok((id, ptype)) => lines.push(Line::from(format!("Default provider: {} [{}]", id, ptype))),
        Err(e) => lines.push(Line::from(Span::styled(format!("Default provider not set: {}", e), Style::default().fg(Color::Red)))),
    }
    if let Some(st) = &app.build { if let Some(msg) = &st.status { lines.push(Line::from(Span::styled(msg.clone(), Style::default().fg(app.theme.secondary)))); } }
    lines.push(Line::from("Press Enter to write; 'g' toggles target."));
    let p = Paragraph::new(lines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Build"))
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

fn get_default_provider_summary() -> Result<(String, String)> {
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).map_err(|e| anyhow!("{}", e))?;
    let v: Value = serde_json::from_str(&text)?;
    let def = v.get("default_provider_id").and_then(|x| x.as_str()).ok_or_else(|| anyhow!("no default_provider_id in chi.tmp.json"))?;
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("");
            if id == def {
                let ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
                return Ok((id.to_string(), ptype));
            }
        }
    }
    Err(anyhow!("default provider entry not found"))
}

fn write_active_config(target: BuildTarget) -> Result<String> {
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).map_err(|e| anyhow!("{}", e))?;
    let v: Value = serde_json::from_str(&text)?;
    let def = v.get("default_provider_id").and_then(|x| x.as_str()).ok_or_else(|| anyhow!("no default_provider_id in chi.tmp.json"))?;
    let arr = v.get("providers").and_then(|x| x.as_array()).ok_or_else(|| anyhow!("no providers array in chi.tmp.json"))?;
    let mut ptype = String::new();
    let mut cfg = serde_json::Map::new();
    for p in arr {
        let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("");
        if id == def {
            ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
            if let Some(c) = p.get("config").and_then(|x| x.as_object()) {
                for (k, val) in c {
                    if k == "type" { continue; }
                    // include only non-empty fields
                    let include = match val {
                        Value::Null => false,
                        Value::String(s) => !s.is_empty(),
                        _ => true,
                    };
                    if include { cfg.insert(k.clone(), val.clone()); }
                }
            }
            break;
        }
    }
    if ptype.is_empty() { return Err(anyhow!("default provider type missing")); }
    let mut out = serde_json::Map::new();
    let mut pmap = serde_json::Map::new();
    pmap.insert("type".to_string(), Value::String(ptype));
    for (k, v) in cfg { pmap.insert(k, v); }
    out.insert("provider".to_string(), Value::Object(pmap));
    let json = Value::Object(out);
    let written = match target {
        BuildTarget::Project => {
            let p = ".chi_llm.json";
            fs::write(p, serde_json::to_vec_pretty(&json)?)?;
            p.to_string()
        }
        BuildTarget::Global => {
            let home = dirs::home_dir().ok_or_else(|| anyhow!("home dir not found"))?;
            let dir = home.join(".cache").join("chi_llm");
            fs::create_dir_all(&dir)?;
            let p = dir.join("model_config.json");
            fs::write(&p, serde_json::to_vec_pretty(&json)?)?;
            p.to_string_lossy().to_string()
        }
    };
    Ok(written)
}

fn load_readme() -> ReadmeState {
    let content = fs::read_to_string("README.md").unwrap_or_else(|_| "# README not found\n\nPlace a README.md in the current directory.".to_string());
    let mut lines = Vec::new();
    let mut toc = Vec::new();
    for (idx, raw) in content.lines().enumerate() {
        let mut level = 0u8;
        let mut title = raw.to_string();
        if let Some(stripped) = raw.strip_prefix("### ") { level = 3; title = stripped.to_string(); }
        else if let Some(stripped) = raw.strip_prefix("## ") { level = 2; title = stripped.to_string(); }
        else if let Some(stripped) = raw.strip_prefix("# ") { level = 1; title = stripped.to_string(); }
        if level > 0 { toc.push(TocEntry { level, title: title.clone(), line: idx }); }
        lines.push(raw.to_string());
    }
    ReadmeState { lines, toc, show_toc: false, scroll: 0 }
}

fn draw_readme(f: &mut Frame, area: Rect, app: &App) {
    // Ensure loaded
    let mut rm = app.readme.clone().unwrap_or_else(load_readme);
    let show_toc = rm.show_toc;
    let chunks = if show_toc {
        Layout::default().direction(Direction::Horizontal).constraints([Constraint::Percentage(25), Constraint::Percentage(75)]).split(area)
    } else {
        Layout::default().direction(Direction::Horizontal).constraints([Constraint::Percentage(100)]).split(area)
    };

    if show_toc {
        let mut toc_items: Vec<ListItem> = Vec::new();
        for e in &rm.toc {
            let indent = match e.level { 1 => "", 2 => "  ", _ => "    " };
            toc_items.push(ListItem::new(format!("{}- {}", indent, e.title)));
        }
        let list = List::new(toc_items)
            .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("TOC"));
        f.render_widget(list, chunks[0]);
    }

    // Render content with simple styling for headings
    let mut vlines: Vec<Line> = Vec::new();
    let start = rm.scroll.min(rm.lines.len());
    let max_rows = area.height.saturating_sub(2) as usize; // rough, accounting for borders
    for raw in rm.lines.iter().skip(start).take(max_rows) {
        if let Some(s) = raw.strip_prefix("# ") {
            vlines.push(Line::from(Span::styled(s.to_string(), Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))))
        } else if let Some(s) = raw.strip_prefix("## ") {
            vlines.push(Line::from(Span::styled(s.to_string(), Style::default().fg(app.theme.accent).add_modifier(Modifier::BOLD))))
        } else if let Some(s) = raw.strip_prefix("### ") {
            vlines.push(Line::from(Span::styled(s.to_string(), Style::default().fg(app.theme.secondary))))
        } else {
            vlines.push(Line::from(raw.as_str()));
        }
    }
    let p = Paragraph::new(vlines)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("README"))
        .alignment(Alignment::Left)
        .wrap(Wrap { trim: true });
    let content_area = if show_toc { chunks[1]} else { chunks[0] };
    f.render_widget(p, content_area);

    // Persist potential changes back to app state (scroll/toc flag)
    let mut new_rm = rm.clone();
    if let Some(orig) = &app.readme { new_rm.scroll = rm.scroll.max(orig.scroll); new_rm.show_toc = rm.show_toc; }
    // Update app state: this function has &App, so we can't mutate here. Caller updates via key handler.
}

#[derive(Clone, Debug)]
struct ProviderScratchEntry { id: String, name: String, ptype: String, tags: Vec<String>, config: Value }

#[derive(Clone, Debug)]
struct ProvidersState {
    entries: Vec<ProviderScratchEntry>,
    selected: usize,
    schema_types: Vec<String>,
    edit: Option<EditState>,
    test_status: Option<String>,
}

impl ProvidersState {
    fn empty() -> Self { Self { entries: Vec::new(), selected: 0, schema_types: Vec::new(), edit: None, test_status: None } }
    fn len_with_add(&self) -> usize { self.entries.len() + 1 }
    fn is_add_row(&self) -> bool { self.selected >= self.entries.len() }
    fn add_default(&mut self) {
        let ptype = self.schema_types.get(0).cloned().unwrap_or_else(|| "local".to_string());
        let id = format!("p{}", self.entries.len() + 1);
        let name = format!("{}", &ptype);
        let mut cfg = serde_json::json!({"type": ptype});
        self.entries.push(ProviderScratchEntry { id, name, ptype: cfg.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string(), tags: Vec::new(), config: cfg });
        self.selected = self.entries.len().saturating_sub(1);
    }
    fn delete_selected(&mut self) {
        if self.selected < self.entries.len() { self.entries.remove(self.selected); if self.selected > 0 { self.selected -= 1; } }
    }
    fn apply_model_to_selected(&mut self, model_id: &str) {
        if self.selected < self.entries.len() {
            if let Some(obj) = self.entries[self.selected].config.as_object_mut() {
                obj.insert("model".to_string(), Value::String(model_id.to_string()));
            }
        }
    }
    fn save(&self) -> Result<()> {
        // Preserve default_provider_id if present
        let path = "chi.tmp.json";
        let mut root: Value = if let Ok(text) = fs::read_to_string(path) { serde_json::from_str(&text).unwrap_or_else(|_| serde_json::json!({})) } else { serde_json::json!({}) };
        let mut providers: Vec<Value> = Vec::new();
        for e in &self.entries {
            providers.push(serde_json::json!({
                "id": e.id,
                "name": e.name,
                "type": e.ptype,
                "tags": e.tags,
                "config": e.config,
            }));
        }
        if !root.is_object() { root = serde_json::json!({}); }
        if let Some(obj) = root.as_object_mut() {
            obj.insert("providers".to_string(), Value::Array(providers));
        }
        fs::write(path, serde_json::to_vec_pretty(&root)?)?;
        Ok(())
    }
}

fn load_providers_state() -> Result<ProvidersState> {
    // Load schema types
    let schema = run_cli_json(&["providers", "schema", "--json"], Duration::from_secs(5))?;
    let mut types: Vec<String> = Vec::new();
    if let Some(obj) = schema.as_object() {
        for k in obj.keys() { types.push(k.to_string()); }
        types.sort();
    }
    // Load scratch file
    let path = "chi.tmp.json";
    let text = fs::read_to_string(path).unwrap_or_else(|_| "{}".to_string());
    let v: Value = serde_json::from_str(&text)?;
    let mut entries: Vec<ProviderScratchEntry> = Vec::new();
    if let Some(arr) = v.get("providers").and_then(|x| x.as_array()) {
        for p in arr {
            let id = p.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = p.get("name").and_then(|x| x.as_str()).unwrap_or(&id).to_string();
            let ptype = p.get("type").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let tags: Vec<String> = p.get("tags").and_then(|x| x.as_array()).map(|a| a.iter().filter_map(|t| t.as_str().map(|s| s.to_string())).collect()).unwrap_or_default();
            let config = p.get("config").cloned().unwrap_or_else(|| serde_json::json!({"type": ptype}));
            entries.push(ProviderScratchEntry { id, name, ptype, tags, config });
        }
    }
    Ok(ProvidersState { entries, selected: 0, schema_types: types, edit: None, test_status: None })
}

fn draw_providers_catalog(f: &mut Frame, area: Rect, app: &App) {
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(st) = &app.providers {
        for (i, e) in st.entries.iter().enumerate() {
            let mut label = format!("{} {} [{}]", if i == st.selected {"›"} else {" "}, e.name, e.ptype);
            if let Some(model) = e.config.get("model").and_then(|v| v.as_str()) { label.push_str(&format!("  [model:{}]", model)); }
            if !e.tags.is_empty() { label.push_str(&format!("  [{}]", e.tags.join(","))); }
            let style = if i == st.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
            items.push(ListItem::new(Line::from(Span::styled(label, style))));
        }
        // Add provider row
        let add_style = if st.is_add_row() { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.accent) };
        items.push(ListItem::new(Line::from(Span::styled("+ Add provider", add_style))));
        if let Some(status) = &st.test_status { items.push(ListItem::new(Line::from(Span::styled(format!("Status: {}", status), Style::default().fg(app.theme.secondary))))); }
    } else {
        items.push(ListItem::new("Loading providers..."));
    }
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Configure Providers"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);

    // Input overlay for editing provider field
    if let Some(st) = &app.providers { if let Some(edit) = &st.edit {
        let area_pop = centered_rect(60, 30, area);
        let prompt = format!("Edit {}: {}", edit.field, edit.buffer);
        let p = Paragraph::new(prompt)
            .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
            .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Edit Field (Enter=save, Esc=cancel)"))
            .alignment(Alignment::Left)
            .wrap(Wrap { trim: true });
        f.render_widget(Clear, area_pop);
        f.render_widget(p, area_pop);
    }}
}

fn probe_provider(entry: &ProviderScratchEntry) -> Result<String> {
    let ptype = entry.ptype.as_str();
    if ptype == "local" { return Ok("local: no network test".to_string()); }
    let client = Client::builder().timeout(Duration::from_secs(3)).build()?;
    match ptype {
        "lmstudio" => {
            let host = entry.config.get("host").and_then(|v| v.as_str()).unwrap_or("127.0.0.1");
            let port = entry.config.get("port").and_then(|v| v.as_u64()).unwrap_or(1234);
            let url = format!("http://{}:{}/v1/models", host, port);
            let resp = client.get(&url).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v.get("data").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0);
                Ok(format!("lmstudio: {} models", count))
            } else { Ok(format!("lmstudio: HTTP {}", status)) }
        }
        "ollama" => {
            let host = entry.config.get("host").and_then(|v| v.as_str()).unwrap_or("127.0.0.1");
            let port = entry.config.get("port").and_then(|v| v.as_u64()).unwrap_or(11434);
            let url = format!("http://{}:{}/api/tags", host, port);
            let resp = client.get(&url).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v.get("models").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0);
                Ok(format!("ollama: {} tags", count))
            } else { Ok(format!("ollama: HTTP {}", status)) }
        }
        "openai" => {
            let base = entry.config.get("base_url").and_then(|v| v.as_str()).unwrap_or("https://api.openai.com");
            let url = format!("{}/v1/models", base.trim_end_matches('/'));
            let key = entry.config.get("api_key").and_then(|v| v.as_str()).unwrap_or("");
            let org = entry.config.get("org_id").and_then(|v| v.as_str());
            if key.is_empty() { return Ok("openai: missing api_key".to_string()); }
            let mut headers = HeaderMap::new();
            let authv = format!("Bearer {}", key);
            headers.insert(AUTHORIZATION, HeaderValue::from_str(&authv).unwrap_or(HeaderValue::from_static("")));
            if let Some(o) = org { headers.insert("OpenAI-Organization", HeaderValue::from_str(o).unwrap_or(HeaderValue::from_static(""))); }
            let resp = client.get(&url).headers(headers).send()?;
            let status = resp.status();
            if status.is_success() {
                let v: Value = resp.json()?;
                let count = v.get("data").and_then(|d| d.as_array()).map(|a| a.len()).unwrap_or(0);
                Ok(format!("openai: {} models", count))
            } else { Ok(format!("openai: HTTP {}", status)) }
        }
        _ => Ok(format!("{}: no test implemented", ptype)),
    }
}

#[derive(Clone, Debug)]
struct EditState { field: String, buffer: String }

#[derive(Clone, Debug)]
struct ModelEntry {
    id: String,
    name: String,
    size: Option<String>,
    file_size_mb: Option<u64>,
    context_window: Option<u64>,
    tags: Vec<String>,
    downloaded: bool,
    current: bool,
    raw: Value,
}

#[derive(Clone, Debug)]
struct ModelBrowser {
    entries: Vec<ModelEntry>,
    filtered: Vec<usize>,
    selected: usize, // index in filtered
    downloaded_only: bool,
    tag_filter: Option<String>,
    show_info: bool,
    all_tags: Vec<String>,
}

impl ModelBrowser {
    fn compute_filtered(&mut self) {
        self.filtered.clear();
        for (i, e) in self.entries.iter().enumerate() {
            if self.downloaded_only && !e.downloaded { continue; }
            if let Some(tag) = &self.tag_filter {
                if !e.tags.iter().any(|t| t == tag) { continue; }
            }
            self.filtered.push(i);
        }
        if self.filtered.is_empty() { self.selected = 0; } else if self.selected >= self.filtered.len() { self.selected = self.filtered.len() - 1; }
    }
    fn move_up(&mut self) { if !self.filtered.is_empty() && self.selected > 0 { self.selected -= 1; } }
    fn move_down(&mut self) { if !self.filtered.is_empty() && self.selected + 1 < self.filtered.len() { self.selected += 1; } }
    fn toggle_downloaded_only(&mut self) { self.downloaded_only = !self.downloaded_only; self.compute_filtered(); }
    fn cycle_tag(&mut self) {
        if self.all_tags.is_empty() { return; }
        match &self.tag_filter {
            None => { self.tag_filter = Some(self.all_tags[0].clone()); }
            Some(cur) => {
                let mut idx = self.all_tags.iter().position(|t| t == cur).unwrap_or(0);
                idx = (idx + 1) % (self.all_tags.len() + 1); // +1 to allow none state
                if idx >= self.all_tags.len() { self.tag_filter = None; } else { self.tag_filter = Some(self.all_tags[idx].clone()); }
            }
        }
        self.compute_filtered();
    }
    fn current_entry(&self) -> Option<&ModelEntry> { self.filtered.get(self.selected).map(|&i| &self.entries[i]) }
}

fn fetch_models(timeout: Duration) -> Result<ModelBrowser> {
    let arr = run_cli_json(&["models", "list", "--json"], timeout)?;
    let mut entries: Vec<ModelEntry> = Vec::new();
    let mut tagset: std::collections::BTreeSet<String> = std::collections::BTreeSet::new();
    if let Some(list) = arr.as_array() {
        for v in list {
            let id = v.get("id").and_then(|x| x.as_str()).unwrap_or("").to_string();
            let name = v.get("name").and_then(|x| x.as_str()).unwrap_or(&id).to_string();
            let size = v.get("size").and_then(|x| x.as_str()).map(|s| s.to_string());
            let file_size_mb = v.get("file_size_mb").and_then(|x| x.as_u64());
            let context_window = v.get("context_window").and_then(|x| x.as_u64());
            let tags: Vec<String> = v.get("tags").and_then(|x| x.as_array()).map(|a| a.iter().filter_map(|t| t.as_str().map(|s| s.to_string())).collect()).unwrap_or_default();
            for t in &tags { tagset.insert(t.clone()); }
            let downloaded = v.get("downloaded").and_then(|x| x.as_bool()).unwrap_or(false);
            let current = v.get("current").and_then(|x| x.as_bool()).unwrap_or(false);
            entries.push(ModelEntry { id, name, size, file_size_mb, context_window, tags, downloaded, current, raw: v.clone() });
        }
    }
    let all_tags = tagset.into_iter().collect();
    let mut mb = ModelBrowser { entries, filtered: Vec::new(), selected: 0, downloaded_only: false, tag_filter: None, show_info: false, all_tags };
    mb.compute_filtered();
    Ok(mb)
}

fn draw_model_browser(f: &mut Frame, area: Rect, app: &App) {
    let mut upper = area;
    let mut lower = area;
    let show_info = app.model.as_ref().map(|m| m.show_info).unwrap_or(false);
    if show_info { // split 70/30
        let chunks = Layout::default().direction(Direction::Vertical).constraints([Constraint::Percentage(70), Constraint::Percentage(30)]).split(area);
        upper = chunks[0]; lower = chunks[1];
    }
    let mut items: Vec<ListItem> = Vec::new();
    if let Some(mb) = &app.model {
        for (pos, &idx) in mb.filtered.iter().enumerate() {
            let e = &mb.entries[idx];
            let mut label = format!("{} {}", if pos == mb.selected {"›"} else {" "}, e.name);
            if e.current { label.push_str("  [current]"); }
            if e.downloaded { label.push_str("  [downloaded]"); }
            if let Some(ref tag) = mb.tag_filter { label.push_str(&format!("  [tag:{}]", tag)); }
            let style = if pos == mb.selected { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
            items.push(ListItem::new(Line::from(Span::styled(label, style))));
        }
    } else {
        items.push(ListItem::new("Loading models..."));
    }
    let title = if let Some(mb) = &app.model {
        let mut t = String::from("Models");
        if mb.downloaded_only { t.push_str(" • downloaded-only"); }
        if let Some(tag) = &mb.tag_filter { t.push_str(&format!(" • tag:{}", tag)); }
        t
    } else { String::from("Models") };
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title(title))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, upper);

    if show_info {
        let mut lines: Vec<Line> = Vec::new();
        if let Some(mb) = &app.model { if let Some(e) = mb.current_entry() {
            lines.push(Line::from(Span::styled(format!("{} ({})", e.name, e.id), Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))));
            if let Some(s) = &e.size { lines.push(Line::from(format!("size: {}", s))); }
            if let Some(fs) = e.file_size_mb { lines.push(Line::from(format!("file_size_mb: {}", fs))); }
            if let Some(ctx) = e.context_window { lines.push(Line::from(format!("context_window: {}", ctx))); }
            if !e.tags.is_empty() { lines.push(Line::from(format!("tags: {}", e.tags.join(", ")))); }
        }}
        let p = Paragraph::new(lines)
            .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
            .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Info"))
            .alignment(Alignment::Left)
            .wrap(Wrap { trim: true });
        f.render_widget(p, lower);
    }
}
