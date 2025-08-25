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
mod settings;

use app::{App, Page, WELCOME_ITEMS};
use build::{BuildState, BuildTarget, draw_build_config, write_active_config};
use settings::draw_settings;
use diagnostics::{draw_diagnostics, export_diagnostics, fetch_diagnostics};
use models::{fetch_models, draw_model_browser};
use providers::{ProvidersState, FormState, DropdownState, load_providers_state, draw_providers_catalog, probe_provider, load_providers_scratch, save_default_provider, draw_select_default};
use readme::{load_readme, draw_readme};
use util::{ensure_chi_llm, centered_rect, neon_gradient_line};

fn ensure_form_for_selected(st: &mut ProvidersState) {
    if st.selected >= st.entries.len() { st.form = None; return; }
    let entry = &st.entries[st.selected];
    let mut ff = Vec::new();
    if let Some(sfields) = st.schema_map.get(&entry.ptype) {
        for sc in sfields.iter() {
            let mut value = String::new();
            if let Some(cfg) = entry.config.as_object() {
                if let Some(v) = cfg.get(&sc.name) {
                    value = match v { Value::String(s) => s.clone(), other => other.to_string() };
                }
            }
            if value.is_empty() { if let Some(d) = &sc.default { value = d.clone(); } }
            ff.push(providers::FormField { schema: providers::FieldSchema { name: sc.name.clone(), ftype: sc.ftype.clone(), required: sc.required, default: sc.default.clone(), help: sc.help.clone(), options: sc.options.clone() }, buffer: value, cursor: 0 });
        }
    }
    let init_hash = providers::compute_form_hash(&ff);
    st.form = Some(FormState { fields: ff, selected: 0, editing: false, message: None, scroll: 0, initial_hash: init_hash, last_test_ok_hash: None });
}

fn focus_form_field(st: &mut ProvidersState, field_name: &str) {
    if st.selected >= st.entries.len() { return; }
    ensure_form_for_selected(st);
    if let Some(form) = &mut st.form {
        if let Some(idx) = form.fields.iter().position(|f| f.schema.name == field_name) {
            form.selected = idx;
            form.editing = true;
            st.focus_right = true;
        } else {
            st.focus_right = true;
        }
    }
}

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
        // Poll async test results (if any) before drawing to keep UI fresh
        if let Some(st) = &mut app.providers {
            if st.test_in_progress {
                if let Some(rx) = &st.test_result_rx {
                    if let Ok((ok, msg)) = rx.try_recv() {
                        st.test_in_progress = false;
                        st.test_result_rx = None;
                        st.test_status = Some(if ok { msg.clone() } else { format!("Error: {}", msg) });
                        if let Some(form) = &mut st.form {
                            form.message = st.test_status.clone();
                            if ok {
                                if let Some(h) = st.pending_test_hash.take() {
                                    form.last_test_ok_hash = Some(h);
                                }
                            } else {
                                form.last_test_ok_hash = None;
                                st.pending_test_hash = None;
                                // Auto-open logs popup on failure
                                st.show_test_popup = true;
                            }
                        } else {
                            st.pending_test_hash = None;
                        }
                    }
                }
            }
            // Drain progress logs if any
            if let Some(prx) = &st.test_progress_rx {
                while let Ok(line) = prx.try_recv() {
                    st.test_log.push(line);
                }
            }
        }
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
                        },
                        KeyCode::Char('r') | KeyCode::Char('R') => {
                            match fetch_diagnostics(Duration::from_secs(5)) {
                                Ok(d) => app.diag = Some(d),
                                Err(e) => app.last_error = Some(format!("Diagnostics failed: {e}")),
                            }
                            continue;
                        },
                        _ => {}
                    }
                }
                handle_key(&mut app, key);
            }
        }
        // Advance animation tick for spinners/headers
        app.tick = app.tick.wrapping_add(1);
        if app.should_quit { break; }
    }
    Ok(())
}

fn handle_key(app: &mut App, key: KeyEvent) {
    // Ctrl+C / q always quits
    if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) { app.should_quit = true; return; }
    // Intercept modal popups before global handling
    if app.page == Page::Configure {
        if let Some(st) = &mut app.providers {
            if st.show_test_popup {
                match key.code {
                    KeyCode::Esc | KeyCode::Char('l') | KeyCode::Char('L') => { st.show_test_popup = false; }
                    _ => {}
                }
                return;
            }
        }
    }
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
        },
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
            },
            _ => {}
        }
    }

    // README keys
    if app.page == Page::Readme {
        if app.readme.is_none() {
            app.readme = Some(load_readme());
        }
        if let Some(rm) = &mut app.readme {
            // When TOC visible, allow Tab to switch focus and Up/Down to navigate TOC
            match key.code {
                KeyCode::Char('h') | KeyCode::Char('H') => {
                    rm.show_toc = !rm.show_toc;
                    if !rm.show_toc { rm.focus_toc = false; }
                }
                KeyCode::Tab => {
                    if rm.show_toc { rm.focus_toc = !rm.focus_toc; }
                }
                KeyCode::BackTab => {
                    if rm.show_toc { rm.focus_toc = !rm.focus_toc; }
                }
                KeyCode::Up => {
                    if rm.show_toc && rm.focus_toc {
                        if rm.toc_selected > 0 { rm.toc_selected -= 1; }
                    } else {
                        rm.scroll_up(1);
                    }
                }
                KeyCode::Down => {
                    if rm.show_toc && rm.focus_toc {
                        if rm.toc_selected + 1 < rm.toc.len() { rm.toc_selected += 1; }
                    } else {
                        rm.scroll_down(1);
                    }
                }
                KeyCode::PageUp => rm.scroll_up(8),
                KeyCode::PageDown => rm.scroll_down(8),
                KeyCode::Enter => {
                    if rm.show_toc && rm.focus_toc {
                        if let Some(entry) = rm.toc.get(rm.toc_selected) {
                            rm.scroll = entry.line;
                            rm.focus_toc = false; // jump to content focus
                        }
                    }
                },
                _ => {}
            }
        }
    }

    // Settings keys
    if app.page == Page::Settings {
        match key.code {
            KeyCode::Up => { if app.settings_idx > 0 { app.settings_idx -= 1; } },
            KeyCode::Down => { if app.settings_idx < 1 { app.settings_idx += 1; } },
            KeyCode::Enter => {
                match app.settings_idx {
                    0 => app.theme.toggle(),
                    1 => app.anim = !app.anim,
                    _ => {}
                }
            },
            _ => {}
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
                },
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
                },
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
            // If logs popup is open, only allow closing it with L/Esc
            if st.show_test_popup {
                match key.code {
                    KeyCode::Esc | KeyCode::Char('l') | KeyCode::Char('L') => { st.show_test_popup = false; }
                    _ => {}
                }
                return;
            }
            // Dropdown handling (e.g., type selector)
            if let Some(dd) = &mut st.dropdown {
                match key.code {
                    KeyCode::Up => { if dd.selected > 0 { dd.selected -= 1; } },
                    KeyCode::Down => {
                        // bound by filtered length later during render; keep simple increment
                        dd.selected = dd.selected.saturating_add(1);
                    },
                    KeyCode::Enter => {
                        // Apply selection from filtered list
                        let filt = dd.filter.to_lowercase();
                        let mut filtered: Vec<usize> = Vec::new();
                        for (i, it) in dd.items.iter().enumerate() {
                            if filt.is_empty() || it.to_lowercase().contains(&filt) { filtered.push(i); }
                        }
                        if !filtered.is_empty() {
                            let sel = if dd.selected >= filtered.len() { filtered.len()-1 } else { dd.selected };
                            let chosen = dd.items[filtered[sel]].clone();
                            match dd.target_field {
                                None => {
                                    if st.selected < st.entries.len() {
                                        st.entries[st.selected].ptype = chosen.clone();
                                        ensure_form_for_selected(st);
                                        if let Some(form) = &mut st.form {
                                            form.selected = 1.min(form.fields.len());
                                            form.editing = false;
                                            form.message = Some("Type changed".to_string());
                                        }
                                    }
                                }
                                Some(fi) => {
                                    if let Some(form) = &mut st.form {
                                        if fi < form.fields.len() {
                                            form.fields[fi].buffer = chosen.clone();
                                            form.editing = false;
                                            form.message = Some(format!("{} set", form.fields[fi].schema.name));
                                        }
                                    }
                                }
                            }
                        }
                        st.dropdown = None;
					return;
                    },
                    KeyCode::Esc => { st.dropdown = None; return; },
                    KeyCode::Backspace => { if !dd.filter.is_empty() { let _ = dd.filter.pop(); dd.selected = 0; } return; },
                    _ => {
                        if let KeyCode::Char(c) = key.code { if !c.is_control() { dd.filter.push(c); dd.selected = 0; } }
                        return;
                    },
                }
                return;
            }
            // Pane focus shortcuts: Tab cycles focus between panes; Shift+Tab cycles backward
            match key.code {
                KeyCode::Tab => {
                    if !st.focus_right {
                        if st.is_add_row() { st.add_default(); }
                        if st.selected < st.entries.len() { ensure_form_for_selected(st); }
                        st.focus_right = true;
                    } else {
                        st.focus_right = false;
                    }
                },
                KeyCode::BackTab => {
                    if st.focus_right {
                        st.focus_right = false;
                    } else {
                        if st.is_add_row() { st.add_default(); }
                        if st.selected < st.entries.len() { ensure_form_for_selected(st); }
                        st.focus_right = true;
                    }
                },
                _ => {}
            }
            if st.focus_right {
                // Right pane: inline form
                if st.form.is_none() && st.selected < st.entries.len() { ensure_form_for_selected(st); }
                if let Some(form) = &mut st.form {
                    match key.code {
                        KeyCode::Esc => { if form.editing { form.editing = false; } else { st.focus_right = false; } },
                        // Up/Down navigate between form groups. Treat [Test|Save|Cancel] as one group.
                        KeyCode::Up => {
                            let fields_len = form.fields.len();
                            let test_idx = fields_len + 1;
                            let save_idx = fields_len + 2;
                            let cancel_idx = fields_len + 3;
                            if form.selected == test_idx || form.selected == save_idx || form.selected == cancel_idx {
                                // Jump to last field (or Type if no fields)
                                form.selected = if fields_len > 0 { fields_len } else { 0 };
                            } else if form.selected > 0 {
                                form.selected -= 1;
                            }
                        },
                        KeyCode::Down => {
                            let fields_len = form.fields.len();
                            let test_idx = fields_len + 1;
                            let save_idx = fields_len + 2;
                            let cancel_idx = fields_len + 3;
                            let total = fields_len + 4;
                            if form.selected == test_idx || form.selected == save_idx || form.selected == cancel_idx {
                                // Already in the last group; stay within group on Down
                            } else if form.selected + 1 < total {
                                form.selected += 1;
                            }
                        },
                        KeyCode::Enter => {
                            // If on Type row: open dropdown
                            if form.selected == 0 {
                                let current = st.entries.get(st.selected).map(|e| e.ptype.clone()).unwrap_or_default();
                                let idx = st.schema_types.iter().position(|t| *t == current).unwrap_or(0);
                                st.dropdown = Some(DropdownState { items: st.schema_types.clone(), selected: idx, title: "Select Provider Type".to_string(), target_field: None, filter: String::new(), downloaded: None });
                                return;
                            }
                            // If on Test/Save/Cancel buttons, act; else toggle/edit field
                            let test_idx = form.fields.len() + 1;
                            let save_idx = form.fields.len() + 2;
                            let cancel_idx = form.fields.len() + 3;
                            let total = form.fields.len() + 4;
                            if form.selected == test_idx {
                                if st.test_in_progress { return; }
                                // Async test: spawn thread and show spinner
                                if st.selected < st.entries.len() {
                                    let entry = st.entries[st.selected].clone();
                                    let (tx, rx) = std::sync::mpsc::channel::<(bool, String)>();
                                    let (txp, rxp) = std::sync::mpsc::channel::<String>();
                                    st.test_result_rx = Some(rx);
                                    st.test_in_progress = true;
                                    let cur_hash = providers::compute_form_hash(&form.fields);
                                    st.pending_test_hash = Some(cur_hash);
                                    st.test_progress_rx = Some(rxp);
                                    st.test_log.clear();
                                    // Auto-open logs for local-zeroconfig
                                    if entry.ptype == "local-zeroconfig" { st.show_test_popup = true; }
                                    form.message = Some("Testing connection… (L: logs)".to_string());
                                    std::thread::spawn(move || {
                                        // Build args
                                        let mut args: Vec<String> = vec!["providers".into(), "test".into(), "--type".into(), entry.ptype.clone(), "--e2e".into(), "--json".into()];
                                        match entry.ptype.as_str() {
                                            "local" => {}
                                            "local-custom" => {
                                                if let Some(path) = entry.config.get("model_path").and_then(|v| v.as_str()) {
                                                    args.push("--model-path".into()); args.push(path.into());
                                                }
                                            }
                                            "lmstudio" | "ollama" => {
                                                if let Some(host) = entry.config.get("host").and_then(|v| v.as_str()) {
                                                    args.push("--host".into()); args.push(host.into());
                                                }
                                                if let Some(port) = entry.config.get("port").and_then(|v| v.as_u64()) {
                                                    args.push("--port".into()); args.push(port.to_string());
                                                }
                                                if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                                    args.push("--model".into()); args.push(model.into());
                                                }
                                            }
                                            "openai" => {
                                                if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                                                    args.push("--base-url".into()); args.push(base.into());
                                                }
                                                if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                                                    args.push("--api-key".into()); args.push(key.into());
                                                }
                                                if let Some(org) = entry.config.get("org_id").and_then(|v| v.as_str()) {
                                                    if !org.is_empty() { args.push("--org-id".into()); args.push(org.into()); }
                                                }
                                                if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                                    args.push("--model".into()); args.push(model.into());
                                                }
                                            }
                                            "anthropic" => {
                                                if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                                                    args.push("--base-url".into()); args.push(base.into());
                                                }
                                                if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                                                    args.push("--api-key".into()); args.push(key.into());
                                                }
                                                if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                                    args.push("--model".into()); args.push(model.into());
                                                }
                                            }
                                            _ => {}
                                        }
                                        let timeout = if entry.ptype == "local-zeroconfig" { Duration::from_secs(90) } else if entry.ptype == "local" || entry.ptype == "local-custom" { Duration::from_secs(60) } else { Duration::from_secs(30) };
                                        // Pass timeout through to CLI so inner e2e doesn't early-timeout at 5s
                                        args.push("--timeout".into()); args.push(format!("{}", timeout.as_secs()));
                                        let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
                                        let res = util::run_cli_json_stream(&args_ref, timeout, txp);
                                        match res {
                                            Ok(v) => {
                                                let ok = v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false);
                                                let msg = v.get("message").and_then(|x| x.as_str()).unwrap_or("").to_string();
                                                let _ = tx.send((ok, if msg.is_empty() { if ok { "ok".to_string() } else { "failed".to_string() } } else { msg }));
                                            }
                                            Err(e) => {
                                                let _ = tx.send((false, e.to_string()));
                                            }
                                        }
                                    });
                                }
                            } else if form.selected == save_idx {
                                let mut missing: Vec<String> = Vec::new();
                                for ff in &form.fields { if ff.schema.required && ff.buffer.trim().is_empty() { missing.push(ff.schema.name.clone()); } }
                                if !missing.is_empty() {
                                    form.message = Some(format!("Missing required: {}", missing.join(", ")));
                                } else {
                                    // Enforce: if dirty and not tested ok, prevent save
                                    let cur_hash = providers::compute_form_hash(&form.fields);
                                    let dirty = cur_hash != form.initial_hash;
                                    let tested_ok = form.last_test_ok_hash.as_ref().map_or(false, |h| *h == cur_hash);
                                    if dirty && !tested_ok {
                                        form.message = Some("Run Test connection first".to_string());
                                        return;
                                    }
                                    // Apply field values to selected entry config
                                    if st.selected < st.entries.len() {
                                        if let Some(obj) = st.entries[st.selected].config.as_object_mut() {
                                            for ff in &form.fields.clone() {
                                                let key2 = ff.schema.name.clone();
                                                if ff.schema.ftype == "int" {
                                                    if let Ok(n) = ff.buffer.parse::<i64>() { obj.insert(key2, Value::Number(n.into())); } else { obj.insert(key2, Value::String(ff.buffer.clone())); }
                                                } else {
                                                    obj.insert(key2, Value::String(ff.buffer.clone()));
                                                }
                                            }
                                        }
                                    }
                                    // Drop form borrow before saving state
                                    std::mem::drop(form);
                                    let save_res = st.save();
                                    // Re-borrow to set message and hashes
                                    if let Some(form2) = &mut st.form {
                                        match save_res {
                                            Ok(_) => { form2.message = Some("Saved".to_string()); }
                                            Err(e) => { form2.message = Some(format!("Save failed: {}", e)); }
                                        }
                                        form2.initial_hash = cur_hash.clone();
                                        form2.last_test_ok_hash = Some(cur_hash);
                                    }
                                }
                            } else if form.selected == cancel_idx { // Cancel
                                form.editing = false;
                                st.focus_right = false;
                            } else {
                                // If field has options, open dropdown, else toggle edit
                                let fi = form.selected - 1; // map to fields index
                                if let Some(ff) = form.fields.get(fi) {
                                    // Special-case: dynamic model list using CLI for supported providers
                                    let ptype = st.entries.get(st.selected).map(|e| e.ptype.clone()).unwrap_or_default();
                                    if ff.schema.name == "model" && (ptype == "lmstudio" || ptype == "ollama" || ptype == "openai" || ptype == "anthropic" || ptype == "local" || ptype == "local-zeroconfig") {
                                        // Use CLI discover-models with provider-specific args
                                        let mut args: Vec<&str> = vec!["providers", "discover-models", "--type", &ptype, "--json"];    
                                        // Hold owned strings so borrowed &strs live long enough
                                        let (mut host, mut port, mut base, mut api_key, mut org) = (String::new(), String::new(), String::new(), String::new(), String::new());
                                        if ptype == "lmstudio" || ptype == "ollama" {
                                            host = form.fields.iter().find(|f| f.schema.name == "host").map(|f| f.buffer.clone()).unwrap_or_else(|| "localhost".to_string());
                                            port = form.fields.iter().find(|f| f.schema.name == "port").map(|f| f.buffer.clone()).unwrap_or_default();
                                            args.push("--host");
                                            args.push(host.as_str());
                                            if !port.is_empty() { args.push("--port"); args.push(port.as_str()); }
                                        } else if ptype == "openai" {
                                            base = form.fields.iter().find(|f| f.schema.name == "base_url").map(|f| f.buffer.clone()).unwrap_or_else(|| "https://api.openai.com".to_string());
                                            api_key = form.fields.iter().find(|f| f.schema.name == "api_key").map(|f| f.buffer.clone()).unwrap_or_default();
                                            org = form.fields.iter().find(|f| f.schema.name == "org_id").map(|f| f.buffer.clone()).unwrap_or_default();
                                            if !base.is_empty() { args.push("--base-url"); args.push(base.as_str()); }
                                            if !api_key.is_empty() { args.push("--api-key"); args.push(api_key.as_str()); }
                                            if !org.is_empty() { args.push("--org-id"); args.push(org.as_str()); }
                                        } else if ptype == "anthropic" {
                                            api_key = form.fields.iter().find(|f| f.schema.name == "api_key").map(|f| f.buffer.clone()).unwrap_or_default();
                                            if !api_key.is_empty() { args.push("--api-key"); args.push(api_key.as_str()); }
                                        }
                                        match util::run_cli_json(&args, Duration::from_secs(5)) {
                                            Ok(v) => {
                                                let mut items: Vec<String> = Vec::new();
                                                if let Some(arr) = v.get("models").and_then(|x| x.as_array()) {
                                                    for it in arr { if let Some(id) = it.get("id").and_then(|x| x.as_str()) { items.push(id.to_string()); } }
                                                }
                                                if items.is_empty() {
                                                    form.message = Some(format!("No models discovered for {}", ptype));
                                                } else {
                                                    let sel = items.iter().position(|x| *x == ff.buffer).unwrap_or(0);
                                                    // Annotate downloaded for local/local-zeroconfig using models list
                                                    let mut downloaded: Option<std::collections::HashSet<String>> = None;
                                                    if ptype == "local" || ptype == "local-zeroconfig" {
                                                        if let Ok(listv) = util::run_cli_json(&["models", "list", "--json"], Duration::from_secs(3)) {
                                                            let mut set = std::collections::HashSet::new();
                                                            if let Some(arr) = listv.as_array() {
                                                                for m in arr {
                                                                    if m.get("downloaded").and_then(|x| x.as_bool()).unwrap_or(false) {
                                                                        if let Some(id) = m.get("id").and_then(|x| x.as_str()) { set.insert(id.to_string()); }
                                                                    }
                                                                }
                                                            }
                                                            downloaded = Some(set);
                                                        }
                                                    }
                                                    st.dropdown = Some(DropdownState { items, selected: sel, title: format!("Select model ({}):", ptype), target_field: Some(fi), filter: String::new(), downloaded });
                                                    return;
                                                }
                                            }
                                            Err(e) => { form.message = Some(format!("Discover failed: {}", e)); }
                                        }
                                    } else if let Some(opts) = &ff.schema.options {
                                        let mut items = opts.clone();
                                        let current_val = ff.buffer.clone();
                                        let mut sel = 0usize;
                                        if let Some(i) = items.iter().position(|x| *x == current_val) { sel = i; }
                                        st.dropdown = Some(DropdownState { items, selected: sel, title: format!("Select {}", ff.schema.name), target_field: Some(fi), filter: String::new(), downloaded: None });
                                        return;
                                    } else if ff.schema.name == "model_path" && ptype == "local-custom" {
                                        // Discover local GGUF files via CLI (local-custom only)
                                        let args = vec!["providers", "discover-models", "--type", "local-custom", "--json"];    
                                        match util::run_cli_json(&args, Duration::from_secs(5)) {
                                            Ok(v) => {
                                                let mut items: Vec<String> = Vec::new();
                                                if let Some(arr) = v.get("models").and_then(|x| x.as_array()) {
                                                    for it in arr { if let Some(id) = it.get("id").and_then(|x| x.as_str()) { items.push(id.to_string()); } }
                                                }
                                                if items.is_empty() {
                                                    form.message = Some("No GGUF files discovered. Configure auto_discovery_gguf_paths or type path manually".to_string());
                                                } else {
                                                    let sel = items.iter().position(|x| *x == ff.buffer).unwrap_or(0);
                                                    st.dropdown = Some(DropdownState { items, selected: sel, title: "Select GGUF path".to_string(), target_field: Some(fi), filter: String::new(), downloaded: None });
                                                    return;
                                                }
                                            }
                                            Err(e) => { form.message = Some(format!("Discover failed: {}", e)); }
                                        }
                                    }
                                    form.editing = !form.editing;
                                }
                            }
                        },
                        // Left/Right: within button group, switch between Test/Save/Cancel. In fields, move cursor when editing.
                        KeyCode::Left => {
                            let fields_len = form.fields.len();
                            let test_idx = fields_len + 1;
                            let save_idx = fields_len + 2;
                            let cancel_idx = fields_len + 3;
                            if form.selected > test_idx {
                                form.selected -= 1;
                            } else if form.editing {
                                if let Some(ff) = form.fields.get_mut(form.selected) {
                                    if ff.cursor > 0 { ff.cursor -= 1; }
                                }
                            }
                        },
                        KeyCode::Right => {
                            let fields_len = form.fields.len();
                            let test_idx = fields_len + 1;
                            let save_idx = fields_len + 2;
                            let cancel_idx = fields_len + 3;
                            if form.selected >= test_idx && form.selected < cancel_idx {
                                form.selected += 1;
                            } else if form.editing {
                                if let Some(ff) = form.fields.get_mut(form.selected) {
                                    if ff.cursor < ff.buffer.chars().count() { ff.cursor += 1; }
                                }
                            }
                        },
                        KeyCode::Home => { if form.editing { if let Some(ff) = form.fields.get_mut(form.selected) { ff.cursor = 0; } } },
                        KeyCode::End => { if form.editing { if let Some(ff) = form.fields.get_mut(form.selected) { ff.cursor = ff.buffer.chars().count(); } } },
                        KeyCode::Backspace => { if form.editing { if let Some(ff) = form.fields.get_mut(form.selected) { if ff.cursor > 0 { let mut s = ff.buffer.clone(); let idx = s.char_indices().nth(ff.cursor-1).map(|(i, _)| i).unwrap_or(0); let idx2 = s.char_indices().nth(ff.cursor).map(|(i, _)| i).unwrap_or(s.len()); s.replace_range(idx..idx2, ""); ff.buffer = s; ff.cursor -= 1; form.last_test_ok_hash = None; } } } },
                        KeyCode::Delete => { if form.editing { if let Some(ff) = form.fields.get_mut(form.selected) { let len = ff.buffer.chars().count(); if ff.cursor < len { let mut s = ff.buffer.clone(); let idx = s.char_indices().nth(ff.cursor).map(|(i, _)| i).unwrap_or(s.len()); let idx2 = s.char_indices().nth(ff.cursor+1).map(|(i, _)| i).unwrap_or(s.len()); s.replace_range(idx..idx2, ""); ff.buffer = s; form.last_test_ok_hash = None; } } } },
                        KeyCode::Tab => { let total = form.fields.len() + 4; form.selected = (form.selected + 1) % total; },
                        KeyCode::BackTab => { let total = form.fields.len() + 4; form.selected = if form.selected == 0 { total - 1 } else { form.selected - 1 }; },
                        KeyCode::Char(c) => {
                            if form.editing {
                                if let Some(ff) = form.fields.get_mut(form.selected) {
                                    let mut s = ff.buffer.clone();
                                    let idx = s.char_indices().nth(ff.cursor).map(|(i, _)| i).unwrap_or(s.len());
                                    s.insert(idx, c);
                                    ff.buffer = s;
                                    ff.cursor += 1;
                                    form.last_test_ok_hash = None;
                                }
                            }
                        },
                        _ => {},
                    }
                }
                return;
            }

            // Left pane: list navigation and actions
            match key.code {
                KeyCode::Up => { if st.selected > 0 { st.selected -= 1; st.form = None; } },
                KeyCode::Down => { if st.selected + 1 < st.len_with_add() { st.selected += 1; st.form = None; } },
                KeyCode::Enter => {
                    if st.is_add_row() {
                        st.add_default();
                        ensure_form_for_selected(st);
                        st.focus_right = true;
                    } else {
                        ensure_form_for_selected(st);
                        st.focus_right = true;
                    }
                },
                KeyCode::Char('a') | KeyCode::Char('A') => { st.add_default(); ensure_form_for_selected(st); st.focus_right = true; },
                KeyCode::Char('d') | KeyCode::Char('D') => { st.delete_selected(); st.form = None; },
                KeyCode::Char('m') | KeyCode::Char('M') => { app.page = Page::ModelBrowser; },
                KeyCode::Char('l') | KeyCode::Char('L') => { if st.test_in_progress || !st.test_log.is_empty() { st.show_test_popup = !st.show_test_popup; } },
                KeyCode::Char('t') | KeyCode::Char('T') => {
                    if st.test_in_progress { return; }
                    if st.selected < st.entries.len() {
                        let entry = st.entries[st.selected].clone();
                        let (tx, rx) = std::sync::mpsc::channel::<(bool, String)>();
                        let (txp, rxp) = std::sync::mpsc::channel::<String>();
                        st.test_result_rx = Some(rx);
                        st.test_progress_rx = Some(rxp);
                        st.test_in_progress = true;
                        st.test_status = None;
                        st.test_log.clear();
                        // If we have a form, capture current hash for potential gating feedback
                        if let Some(form) = &st.form { st.pending_test_hash = Some(providers::compute_form_hash(&form.fields)); }
                        // Auto-open logs for local-zeroconfig
                        if entry.ptype == "local-zeroconfig" { st.show_test_popup = true; }
                        std::thread::spawn(move || {
                            let mut args: Vec<String> = vec!["providers".into(), "test".into(), "--type".into(), entry.ptype.clone(), "--e2e".into(), "--json".into()];
                            match entry.ptype.as_str() {
                                "local" => {}
                                "local-custom" => {
                                    if let Some(path) = entry.config.get("model_path").and_then(|v| v.as_str()) {
                                        args.push("--model-path".into()); args.push(path.into());
                                    }
                                }
                                "lmstudio" | "ollama" => {
                                    if let Some(host) = entry.config.get("host").and_then(|v| v.as_str()) {
                                        args.push("--host".into()); args.push(host.into());
                                    }
                                    if let Some(port) = entry.config.get("port").and_then(|v| v.as_u64()) {
                                        args.push("--port".into()); args.push(port.to_string());
                                    }
                                    if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                        args.push("--model".into()); args.push(model.into());
                                    }
                                }
                                "openai" => {
                                    if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                                        args.push("--base-url".into()); args.push(base.into());
                                    }
                                    if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                                        args.push("--api-key".into()); args.push(key.into());
                                    }
                                    if let Some(org) = entry.config.get("org_id").and_then(|v| v.as_str()) {
                                        if !org.is_empty() { args.push("--org-id".into()); args.push(org.into()); }
                                    }
                                    if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                        args.push("--model".into()); args.push(model.into());
                                    }
                                }
                                "anthropic" => {
                                    if let Some(base) = entry.config.get("base_url").and_then(|v| v.as_str()) {
                                        args.push("--base-url".into()); args.push(base.into());
                                    }
                                    if let Some(key) = entry.config.get("api_key").and_then(|v| v.as_str()) {
                                        args.push("--api-key".into()); args.push(key.into());
                                    }
                                    if let Some(model) = entry.config.get("model").and_then(|v| v.as_str()) {
                                        args.push("--model".into()); args.push(model.into());
                                    }
                                }
                                _ => {}
                            }
                            let timeout = if entry.ptype == "local-zeroconfig" { Duration::from_secs(90) } else if entry.ptype == "local" || entry.ptype == "local-custom" { Duration::from_secs(60) } else { Duration::from_secs(30) };
                            // Pass timeout through to CLI so inner e2e doesn't early-timeout at 5s
                            args.push("--timeout".into()); args.push(format!("{}", timeout.as_secs()));
                            let args_ref: Vec<&str> = args.iter().map(|s| s.as_str()).collect();
                            let res = util::run_cli_json_stream(&args_ref, timeout, txp);
                            match res {
                                Ok(v) => {
                                    let ok = v.get("ok").and_then(|x| x.as_bool()).unwrap_or(false);
                                    let msg = v.get("message").and_then(|x| x.as_str()).unwrap_or("").to_string();
                                    let _ = tx.send((ok, if msg.is_empty() { if ok { "ok".to_string() } else { "failed".to_string() } } else { msg }));
                                }
                                Err(e) => {
                                    let _ = tx.send((false, e.to_string()));
                                }
                            }
                        });
                    }
                },
                // Save from left pane
                KeyCode::Char('s') | KeyCode::Char('S') => { if let Err(e) = st.save() { app.last_error = Some(format!("Save failed: {e}")); } },
                _ => {},
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
                KeyCode::Char('g') | KeyCode::Char('G') => { st.toggle_target(); },
                KeyCode::Enter => {
                    match write_active_config(st.target) {
                        Ok(path) => st.status = Some(format!("Written: {}", path)),
                        Err(e) => st.status = Some(format!("Error: {}", e)),
                    }
                },
                _ => {},
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
        Page::Settings => draw_settings(f, chunks[1], app),
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
        Page::Readme => "Up/Down scroll • PgUp/PgDn • h TOC • Tab switch TOC/Content • Enter jump • Esc back",
        Page::ModelBrowser => "Up/Down select • Enter choose • r downloaded-only • f tag filter • i info • Esc back",
        Page::Configure => "Tab/Shift+Tab switch • ↑/↓ field • Enter edit/Test/Save/Cancel • ←/→/Home/End • Del/Backspace • L logs • Esc back",
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
        Line::from("Configure: Tab/Shift+Tab • ↑/↓ field • Enter edit/Test/Save/Cancel • ←/→/Home/End • Del/Backspace • L logs"),
        Line::from("README: Up/Down/PgUp/PgDn scroll • h TOC • Tab switch TOC/Content • Enter jump"),
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
