use ratatui::style::Color;

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum ThemeMode {
    Light,
    Dark,
}

#[derive(Clone, Debug)]
pub struct Theme {
    pub mode: ThemeMode,
    pub bg: Color,
    pub fg: Color,
    pub primary: Color,
    pub secondary: Color,
    pub accent: Color,
    pub frame: Color,
    pub selected: Color,
}

impl Theme {
    pub fn synthwave_dark() -> Self {
        Self {
            mode: ThemeMode::Dark,
            bg: Color::Rgb(10, 8, 20),
            fg: Color::Rgb(220, 220, 235),
            primary: Color::Rgb(255, 0, 153),
            secondary: Color::Rgb(0, 255, 255),
            accent: Color::Rgb(64, 160, 255),
            frame: Color::Rgb(120, 80, 200),
            selected: Color::Rgb(255, 120, 0),
        }
    }

    pub fn toggle(&mut self) {
        self.mode = match self.mode {
            ThemeMode::Dark => ThemeMode::Light,
            ThemeMode::Light => ThemeMode::Dark,
        };
    }
}

