package theme

import "github.com/charmbracelet/lipgloss/v2"

// Mode represents the theme mode (light/dark).
type Mode int

const (
    Light Mode = iota
    Dark
)

// Styles bundles lipgloss styles used by the TUI.
type Styles struct {
    Title     lipgloss.Style
    Subtitle  lipgloss.Style
    Normal    lipgloss.Style
    Highlight lipgloss.Style
    Help      lipgloss.Style
    Frame     lipgloss.Style
    Selected  lipgloss.Style
    Panel     lipgloss.Style
}

// New returns a Styles instance for provided mode.
func New(mode Mode) Styles {
    // Single cohesive dark theme (crush-inspired), regardless of mode.
    // Palette refs: base bg #0B0F16, text #E5E7EB, subtle #9CA3AF, accent violet/cyan.
    return Styles{
        Title:     lipgloss.NewStyle().Bold(true).Foreground(lipgloss.Color("#E5E7EB")),
        Subtitle:  lipgloss.NewStyle().Foreground(lipgloss.Color("#9CA3AF")).Bold(true),
        Normal:    lipgloss.NewStyle().Foreground(lipgloss.Color("#E5E7EB")),
        Highlight: lipgloss.NewStyle().Foreground(lipgloss.Color("#8B5CF6")).Bold(true),
        Help:      lipgloss.NewStyle().Foreground(lipgloss.Color("#94A3B8")).Faint(true),
        // No explicit background on frame; let terminal background show through.
        Frame:     lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("#334155")).Padding(1, 2),
        Selected:  lipgloss.NewStyle().Foreground(lipgloss.Color("#E5E7EB")).Background(lipgloss.Color("#1E1B4B")).Bold(true),
        Panel:     lipgloss.NewStyle().Border(lipgloss.RoundedBorder()).BorderForeground(lipgloss.Color("#3F3F46")).Padding(0, 1),
    }
}
