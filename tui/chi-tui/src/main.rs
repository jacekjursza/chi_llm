use std::io::{self, Stdout};
use std::time::{Duration, Instant};
use std::process::Command;

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
            if let Event::Key(key) = event::read()? { handle_key(&mut app, key); }
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
        KeyCode::Char('4') => app.page = Page::Diagnostics,
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

fn ui(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, app: &App) {
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
        Page::Diagnostics => draw_stub(f, chunks[1], app, "Diagnostics (stub) — e to export"),
        Page::Build => draw_stub(f, chunks[1], app, "Build Config (stub) — Project/Global"),
        Page::Settings => draw_stub(f, chunks[1], app, "Settings (stub) — t/a toggles"),
    }
    draw_footer(f, chunks[2], app);

    if app.show_help { draw_help_overlay(f, app); }
}

fn draw_header(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, area: Rect, app: &App) {
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

fn draw_footer(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, area: Rect, app: &App) {
    let msg = Line::from(Span::styled(
        "Esc: back • q: quit • 1/2/3/4/b/s: sections • ?: help",
        Style::default().fg(app.theme.secondary),
    ));
    let p = Paragraph::new(msg)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default())
        .alignment(Alignment::Center);
    f.render_widget(p, area);
}

fn draw_welcome(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, area: Rect, app: &App) {
    let items: Vec<ListItem> = WELCOME_ITEMS.iter().enumerate().map(|(i, (label, _))| {
        let style = if i == app.menu_idx { Style::default().fg(app.theme.selected).add_modifier(Modifier::BOLD) } else { Style::default().fg(app.theme.fg) };
        ListItem::new(Line::from(Span::styled(format!("{} {}", if i == app.menu_idx {"›"} else {" "}, label), style)))
    }).collect();
    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)).title("Welcome"))
        .highlight_style(Style::default().fg(app.theme.selected));
    f.render_widget(list, area);
}

fn draw_stub(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, area: Rect, app: &App, text: &str) {
    let p = Paragraph::new(text)
        .style(Style::default().bg(app.theme.bg).fg(app.theme.fg))
        .block(Block::default().borders(Borders::ALL).border_style(Style::default().fg(app.theme.frame)))
        .alignment(Alignment::Center)
        .wrap(Wrap { trim: true });
    f.render_widget(p, area);
}

fn draw_help_overlay(f: &mut Terminal<CrosstermBackend<Stdout>>::Frame, app: &App) {
    let area = centered_rect(70, 60, f.size());
    let lines = vec![
        Line::from(Span::styled("Global keys:", Style::default().fg(app.theme.primary).add_modifier(Modifier::BOLD))),
        Line::from("Up/Down: navigate • Enter: select • Esc: back • q/Ctrl+C: quit"),
        Line::from("1: README • 2: Configure • 3: Select Default • 4: Diagnostics • b: Build • s: Settings"),
        Line::from("?: help overlay • t: theme • a: animation"),
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

