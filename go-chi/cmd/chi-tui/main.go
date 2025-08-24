package main

import (
	"flag"
	"fmt"

	tea "github.com/charmbracelet/bubbletea/v2"

	"go-chi/internal/providers"
	"go-chi/internal/theme"
	"go-chi/internal/tui"
)

func main() {
	once := flag.Bool("once", false, "render one frame and quit (non-interactive)")
	noAlt := flag.Bool("no-alt", false, "disable alt screen")
	flag.Parse()

	ptypes := providers.List()
	if len(ptypes) == 0 {
		fmt.Println("chi-llm CLI required: no providers available. Ensure 'chi-llm' is installed and on PATH.")
		return
	}
	m := tui.NewModel(ptypes, theme.Light, *once)
	opts := []tea.ProgramOption{tea.WithMouseCellMotion(), tea.WithMouseAllMotion()}
	if !*noAlt {
		opts = append(opts, tea.WithAltScreen())
	}
	p := tea.NewProgram(m, opts...)
	finalModel, err := p.Run()
	if err != nil {
		fmt.Println("error:", err)
		return
	}
	if fm, ok := finalModel.(tui.Model); ok {
		if fm.Selected() != "" {
			fmt.Println("selected:", fm.Selected())
		}
	}
}
