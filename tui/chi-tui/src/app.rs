use std::time::Instant;

use crate::build::BuildState;
use crate::diagnostics::DiagState;
use crate::models::ModelBrowser;
use crate::providers::{DefaultProviderState, ProvidersState};
use crate::readme::ReadmeState;
use crate::theme::Theme;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum Page {
    Welcome,
    Readme,
    Configure,
    SelectDefault,
    ModelBrowser,
    Diagnostics,
    Build,
    Settings,
}

pub struct App {
    pub page: Page,
    pub menu_idx: usize,
    pub show_help: bool,
    pub anim: bool,
    pub settings_idx: usize,
    pub tick: u64,
    pub last_tick: Instant,
    pub theme: Theme,
    pub use_alt: bool,
    pub should_quit: bool,
    pub diag: Option<DiagState>,
    pub last_error: Option<String>,
    pub model: Option<ModelBrowser>,
    pub selected_model_id: Option<String>,
    pub readme: Option<ReadmeState>,
    pub defaultp: Option<DefaultProviderState>,
    pub providers: Option<ProvidersState>,
    pub build: Option<BuildState>,
}

impl App {
    pub fn new(use_alt: bool) -> Self {
        Self {
            page: Page::Welcome,
            menu_idx: 0,
            show_help: false,
            anim: true,
            settings_idx: 0,
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

pub const WELCOME_ITEMS: &[(&str, Page)] = &[
    ("README", Page::Readme),
    ("Configure Providers", Page::Configure),
    ("Select Default", Page::SelectDefault),
    ("Diagnostics", Page::Diagnostics),
    ("Build Configuration", Page::Build),
    ("Settings", Page::Settings),
    ("Model Browser", Page::ModelBrowser),
    ("EXIT", Page::Welcome),
];
