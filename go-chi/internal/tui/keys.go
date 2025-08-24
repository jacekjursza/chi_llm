package tui

import "github.com/charmbracelet/bubbles/v2/key"

// KeyMap defines key bindings for the TUI.
type KeyMap struct {
	Up       key.Binding
	Down     key.Binding
	Enter    key.Binding
	Quit     key.Binding
	Back     key.Binding
	Models   key.Binding
	Export   key.Binding
	Toggle   key.Binding
	Anim     key.Binding
	Help     key.Binding
	Sec1     key.Binding
	Sec2     key.Binding
	Sec3     key.Binding
	Sec4     key.Binding
	Sec5     key.Binding
	Settings key.Binding
	Tab      key.Binding
	Test     key.Binding
	Add      key.Binding
	Save     key.Binding
	Delete   key.Binding
	Filter   key.Binding
	Tag      key.Binding
	Info     key.Binding
}

// DefaultKeyMap returns the default key bindings.
func DefaultKeyMap() KeyMap {
	return KeyMap{
		Up: key.NewBinding(
			key.WithKeys("up", "k"),
			key.WithHelp("↑/k", "up"),
		),
		Down: key.NewBinding(
			key.WithKeys("down", "j"),
			key.WithHelp("↓/j", "down"),
		),
		Enter: key.NewBinding(
			key.WithKeys("enter"),
			key.WithHelp("enter", "select"),
		),
		Quit: key.NewBinding(
			key.WithKeys("q", "ctrl+c"),
			key.WithHelp("q", "quit"),
		),
		Back: key.NewBinding(
			key.WithKeys("esc"),
			key.WithHelp("esc", "back"),
		),
		Models: key.NewBinding(
			key.WithKeys("m"),
			key.WithHelp("m", "browse models"),
		),
		Export: key.NewBinding(
			key.WithKeys("e"),
			key.WithHelp("e", "export diagnostics"),
		),
		Toggle: key.NewBinding(
			key.WithKeys("t"),
			key.WithHelp("t", "toggle theme"),
		),
		Anim: key.NewBinding(
			key.WithKeys("a"),
			key.WithHelp("a", "toggle animation"),
		),
		Help: key.NewBinding(
			key.WithKeys("?"),
			key.WithHelp("?", "help"),
		),
		Sec1: key.NewBinding(
			key.WithKeys("1"),
			key.WithHelp("1", "readme"),
		),
		Sec2: key.NewBinding(
			key.WithKeys("2"),
			key.WithHelp("2", "configure"),
		),
		Sec3: key.NewBinding(
			key.WithKeys("3"),
			key.WithHelp("3", "select default"),
		),
		Sec4: key.NewBinding(
			key.WithKeys("4"),
			key.WithHelp("4", "diagnostics"),
		),
		Sec5: key.NewBinding(
			key.WithKeys("b"),
			key.WithHelp("b", "build"),
		),
		Settings: key.NewBinding(
			key.WithKeys("s"),
			key.WithHelp("s", "settings"),
		),
		Tab: key.NewBinding(
			key.WithKeys("tab"),
			key.WithHelp("tab", "next field"),
		),
		Test: key.NewBinding(
			key.WithKeys("T"),
			key.WithHelp("T", "test connection"),
		),
		Add: key.NewBinding(
			key.WithKeys("A", "a"),
			key.WithHelp("A/a", "add provider"),
		),
		Save: key.NewBinding(
			key.WithKeys("S"),
			key.WithHelp("S", "save provider"),
		),
		Delete: key.NewBinding(
			key.WithKeys("D"),
			key.WithHelp("D", "delete provider"),
		),
		Filter: key.NewBinding(
			key.WithKeys("r"),
			key.WithHelp("r", "downloaded only"),
		),
		Tag: key.NewBinding(
			key.WithKeys("f"),
			key.WithHelp("f", "filter by tag"),
		),
		Info: key.NewBinding(
			key.WithKeys("i"),
			key.WithHelp("i", "model details"),
		),
	}
}

// ShortHelp and FullHelp implement bubbles help keymap interface.
func (k KeyMap) ShortHelp() []key.Binding {
	return []key.Binding{k.Sec1, k.Sec2, k.Sec3, k.Sec4, k.Up, k.Down, k.Enter, k.Models, k.Export, k.Add, k.Save, k.Test, k.Filter, k.Tag, k.Info, k.Back, k.Anim, k.Quit}
}

func (k KeyMap) FullHelp() [][]key.Binding {
	return [][]key.Binding{
		{k.Sec1, k.Sec2, k.Sec3, k.Sec4, k.Up, k.Down, k.Enter},
		{k.Models, k.Export, k.Add, k.Save, k.Test, k.Filter, k.Tag, k.Info, k.Delete, k.Back, k.Anim, k.Toggle, k.Help, k.Quit},
	}
}
