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
        Page::Configure => draw_stub(f, chunks[1], app, &format!("Configure Providers (stub) — A/S/D/T/m to be implemented{}", match &app.selected_model_id { Some(id) => format!(" • selected model: {}", id), None => String::new() })),
        Page::SelectDefault => draw_stub(f, chunks[1], app, "Select Default (stub) — Enter to set"),
        Page::ModelBrowser => draw_model_browser(f, chunks[1], app),
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
        Page::Readme => "Up/Down scroll • PgUp/PgDn faster • h TOC • Esc back",
        Page::ModelBrowser => "Up/Down select • Enter choose • r downloaded-only • f tag filter • i info • Esc back",
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
        Line::from("README: Up/Down/PgUp/PgDn scroll • h TOC"),
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
