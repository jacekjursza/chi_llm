use std::io::{self, Stdout};
use std::time::Duration;

use anyhow::Result;
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

mod theme;
mod util;
mod app;
mod diagnostics;
mod readme;
mod models;
mod providers;
mod build;

use app::{App, Page, WELCOME_ITEMS};
use build::{BuildState, BuildTarget, draw_build_config, write_active_config};
use diagnostics::{draw_diagnostics, export_diagnostics, fetch_diagnostics};
use models::{fetch_models, draw_model_browser};
use providers::{ProvidersState, EditState, FormState, load_providers_state, draw_providers_catalog, probe_provider, load_providers_scratch, save_default_provider, draw_select_default};
use readme::{load_readme, draw_readme};
use util::{ensure_chi_llm, centered_rect, neon_gradient_line};

#[derive(Parser, Debug)]
#[command(name = "chi-tui")] 
#[command(about = "Terminal UI for chi-llm (Rust/ratatui)", long_about = None)]
struct Args {
    /// Do not use alternate screen buffer
    #[arg(long = "no-alt")]
    no_alt: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();
    ensure_chi_llm()?;

    // Terminal setup
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    if !args.no_alt {
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    } else {
        execute!(stdout, EnableMouseCapture)?;
    }
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;
    let res = run_app(&mut terminal, App::new(!args.no_alt));

    // Restore terminal
    disable_raw_mode()?;
    let mut stdout = io::stdout();
    if !args.no_alt {
        execute!(stdout, LeaveAlternateScreen, DisableMouseCapture)?;
    } else {
        execute!(stdout, DisableMouseCapture)?;
    }
    terminal.show_cursor()?;

    if let Err(err) = res {
        eprintln!("\nError: {err}");
        std::process::exit(1);
    }
    Ok(())
}

fn run_app(terminal: &mut Terminal<CrosstermBackend<Stdout>>, mut app: App) -> Result<()> {
    let tick_rate = Duration::from_millis(100);
    loop {
        terminal.draw(|f| ui(f, &app))?;
        if event::poll(tick_rate)? {
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
            // Schema-driven form mode
            if let Some(form) = &mut st.form {
                match key.code {
                    KeyCode::Esc => { st.form = None; }
                    KeyCode::Up => { if form.selected > 0 { form.selected -= 1; } }
                    KeyCode::Down => { if form.selected + 1 < form.fields.len() { form.selected += 1; } }
                    KeyCode::Enter => { form.editing = !form.editing; }
                    KeyCode::Backspace => { if form.editing { if let Some(ch) = form.fields.get_mut(form.selected) { ch.buffer.pop(); } } }
                    KeyCode::Tab => { if form.selected + 1 < form.fields.len() { form.selected += 1; } else { form.selected = 0; } }
                    KeyCode::Char('s') | KeyCode::Char('S') => {
                        // Save back to selected provider config
                        if st.selected < st.entries.len() {
                            if let Some(obj) = st.entries[st.selected].config.as_object_mut() {
                                for ff in &form.fields {
                                    let key = ff.schema.name.clone();
                                    if ff.schema.ftype == "int" {
                                        if let Ok(n) = ff.buffer.parse::<i64>() { obj.insert(key, Value::Number(n.into())); } else { obj.insert(key, Value::String(ff.buffer.clone())); }
                                    } else {
                                        obj.insert(key, Value::String(ff.buffer.clone()));
                                    }
                                }
                            }
                        }
                        st.form = None;
                    }
                    KeyCode::Char(c) => { if form.editing { if let Some(ch) = form.fields.get_mut(form.selected) { ch.buffer.push(c); } } }
                    _ => { }
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
                KeyCode::Char('f') | KeyCode::Char('F') => {
                    // Open dynamic form based on schema
                    if st.selected < st.entries.len() {
                        let ptype = st.entries[st.selected].ptype.clone();
                        if let Some(fields) = st.schema_map.get(&ptype) {
                            let mut ff = Vec::new();
                            for sc in fields.iter() {
                                let mut value = String::new();
                                if let Some(cfg) = st.entries[st.selected].config.as_object() {
                                    if let Some(v) = cfg.get(&sc.name) {
                                        value = match v { Value::String(s) => s.clone(), other => other.to_string() };
                                    }
                                }
                                if value.is_empty() { if let Some(d) = &sc.default { value = d.clone(); } }
                                ff.push(providers::FormField { schema: providers::FieldSchema { name: sc.name.clone(), ftype: sc.ftype.clone(), required: sc.required, default: sc.default.clone(), help: sc.help.clone() }, buffer: value });
                            }
                            st.form = Some(FormState { fields: ff, selected: 0, editing: false });
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
    let title = neon_gradient_line(" chi_llm — micro‑LLM • TUI vNext ", &app.theme);
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
