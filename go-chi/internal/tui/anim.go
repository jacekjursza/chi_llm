package tui

import (
	"image/color"
	"strings"
	"time"
	"unicode/utf8"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
)

type tickMsg time.Time
type hideBannerMsg time.Time

const tickInterval = 100 * time.Millisecond
const bannerSpeedDiv = 4 // slower banner shift (every 4 ticks)

// Animator renders a small retro-wave vibe: neon banner + horizon grid.
type Animator struct {
	Enabled bool
	frame   int
	palette []string
}

func NewAnimator(enabled bool) Animator {
	return Animator{
		Enabled: enabled,
		frame:   0,
		// purple-to-blue gradient palette (purple top -> blue bottom)
		palette: []string{
			"#9333EA", // Purple-600
			"#A855F7", // Purple-500
			"#C084FC", // Purple-400
			"#D8B4FE", // Purple-300
			"#818CF8", // Indigo-400
			"#6366F1", // Indigo-500
			"#4F46E5", // Indigo-600
			"#3730A3", // Indigo-800
			"#3B82F6", // Blue-500
			"#2563EB", // Blue-600
			"#1D4ED8", // Blue-700
			"#1E40AF", // Blue-800
		},
	}
}

func (a *Animator) Tick() tea.Cmd {
	if !a.Enabled {
		return nil
	}
	return tea.Tick(tickInterval, func(t time.Time) tea.Msg { return tickMsg(t) })
}

func (a *Animator) Next() { a.frame++ }

// RenderBanner builds 2 lines of moving gradient blocks.
func (a *Animator) RenderBanner(width int) string {
	if width <= 0 {
		return ""
	}
	lines := make([]string, 2)
	slow := a.frame / bannerSpeedDiv

	for row := 0; row < 2; row++ {
		var sb strings.Builder
		i := 0

		for i < width {
			// Use different parts of palette for each row
			// Top row uses purple shades (0-5), bottom uses blue shades (6-11)
			paletteOffset := 0
			paletteSize := 6
			if row == 1 {
				paletteOffset = 6
			}

			idx := ((i + slow) % paletteSize) + paletteOffset
			if idx >= len(a.palette) {
				idx = paletteOffset
			}

			color := lipgloss.Color(a.palette[idx])

			// Use block characters for more interesting texture
			blockChar := "█"
			if (i+slow)%3 == 0 {
				blockChar = "▓"
			} else if (i+slow)%3 == 1 {
				blockChar = "▒"
			}

			// Apply color as foreground with blocks
			style := lipgloss.NewStyle().Foreground(color)
			sb.WriteString(style.Render(blockChar))
			i++
		}
		lines[row] = sb.String()
	}
	return strings.Join(lines, "\n")
}

// RenderGrid makes a simple moving horizon grid (2 lines) using ASCII squares.
func (a *Animator) RenderGrid(width int) string {
	if width <= 0 {
		return ""
	}

	// Calculate logo position (centered)
	logoWidth := 37 // Width of animated area (33 + 2 gradient chars on each side)
	logoStart := 0
	logoEnd := width
	if width > logoWidth {
		logoStart = (width - logoWidth) / 2 // Centered without offset
		logoEnd = logoStart + logoWidth
	}

	// Use ASCII block characters for squares effect - compact 3-char gradient
	// █ = full block, ▓ = dark shade, ▒ = medium shade
	blocks := []string{"█", "▓", "▒", "▓"}
	staticBlock := "░" // Static light gray block for non-animated areas

	// Create animated pattern with blocks
	offset := (a.frame / 2) % len(blocks) // Slower animation

	var line1, line2 strings.Builder

	// Build lines character by character
	for i := 0; i < width; i++ {
		var char1, char2 string

		// Determine if we're in the logo area
		if i >= logoStart && i < logoEnd {
			// Animated area - use moving blocks
			blockIdx1 := (i + offset) % len(blocks)
			blockIdx2 := (i + offset + 2) % len(blocks) // Smaller offset for tighter gradient
			char1 = blocks[blockIdx1]
			char2 = blocks[blockIdx2]
		} else {
			// Static area - use static blocks
			char1 = staticBlock
			char2 = staticBlock
		}

		line1.WriteString(char1)
		line2.WriteString(char2)
	}

	// Build styled result
	var result strings.Builder
	// Use same logo gradient colors for both static and animated areas
	purpleStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#7C3AED")) // Logo purple for top
	blueStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#3B82F6"))   // Logo blue for bottom

	// Render line 1 (top) - all purple
	line1Str := line1.String()
	result.WriteString(purpleStyle.Render(line1Str))

	result.WriteString("\n")

	// Render line 2 (bottom) - all blue
	line2Str := line2.String()
	result.WriteString(blueStyle.Render(line2Str))

	return result.String()
}

func repeatToWidth(pattern string, width int) string {
	if width <= 0 || pattern == "" {
		return ""
	}
	pr := []rune(pattern)
	out := make([]rune, 0, width)
	for len(out) < width {
		out = append(out, pr...)
	}
	if len(out) > width {
		out = out[:width]
	}
	return string(out)
}

// RenderHero renders a centered ASCII logo with a horizontal gradient
// (crush-inspired), with compact height.
func (a *Animator) RenderHero(width int, scale int) string {
	if width <= 0 {
		return ""
	}
	if scale < 1 {
		scale = 1
	}
	ascii := asciiCHI_LLM()
	// Convert to runes per line and compute dimensions.
	lines := make([][]rune, len(ascii))
	aw := 0
	for i, s := range ascii {
		r := []rune(s)
		lines[i] = r
		if len(r) > aw {
			aw = len(r)
		}
	}
	ah := len(lines)
	// Hero height with optional breathing room (0 when scale=1).
	margin := max(0, scale-1)
	height := ah + 2*margin
	if height < ah {
		height = ah
	}
	// Center horizontally.
	trimmedAW := aw
	if trimmedAW > width {
		trimmedAW = width
	}
	startX := 0
	if width > trimmedAW {
		startX = (width - trimmedAW) / 2
	}
	// Vertical centering.
	vpad := (height - ah) / 2

	// Gradient palette left→right (purple→violet→blue).
	grad := []color.Color{
		lipgloss.Color("#7C3AED"), // purple
		lipgloss.Color("#8B5CF6"), // violet
		lipgloss.Color("#3B82F6"), // blue
		lipgloss.Color("#3B82F6"), // blue (stay blue, no cyan)
	}

	rows := make([]string, height)
	for r := 0; r < height; r++ {
		var sb strings.Builder
		for c := 0; c < width; c++ {
			ch := " "
			ay := r - vpad
			ax := c - startX
			if ay >= 0 && ay < ah && ax >= 0 {
				row := lines[ay]
				if ax < len(row) {
					ru := row[ax]
					if ru != ' ' {
						ch = string(ru)
						// Map horizontal position within the text to gradient index.
						// Adjust mapping so purple ends earlier and LLM is fully blue
						gi := 0
						if trimmedAW > 1 {
							// Scale position to make transition happen earlier
							// We want purple to end around position 23 (one char earlier, before LLM starts)
							adjustedPos := ax * 125 / 100 // Scale up position more to shift blue earlier
							if adjustedPos > trimmedAW-1 {
								adjustedPos = trimmedAW - 1
							}
							gi = (adjustedPos * (len(grad) - 1)) / (trimmedAW - 1)
						}
						st := lipgloss.NewStyle().Foreground(grad[gi]).Bold(true)
						sb.WriteString(st.Render(ch))
						continue
					}
				}
			}
			sb.WriteString(ch)
		}
		rows[r] = sb.String()
	}
	return strings.Join(rows, "\n")
}

// nearestDistChebyshev returns the Chebyshev distance from (ax,ay) to the
// nearest true cell in occ; returns a large number if none found.
func nearestDistChebyshev(occ [][]bool, ax, ay int) int {
	ah := len(occ)
	if ah == 0 {
		return 1 << 30
	}
	aw := len(occ[0])
	best := 1 << 30
	// Search within a small fixed radius for performance.
	maxR := 3
	for d := 1; d <= maxR; d++ {
		// candidate square around (ax,ay)
		for y := ay - d; y <= ay+d; y++ {
			if y < 0 || y >= ah {
				continue
			}
			for x := ax - d; x <= ax+d; x++ {
				if x < 0 || x >= aw {
					continue
				}
				if occ[y][x] {
					// Chebyshev distance
					dy := y - ay
					if dy < 0 {
						dy = -dy
					}
					dx := x - ax
					if dx < 0 {
						dx = -dx
					}
					dist := dx
					if dy > dist {
						dist = dy
					}
					if dist < best {
						best = dist
					}
				}
			}
		}
		if best != 1<<30 {
			return best
		}
	}
	return best
}

// asciiCHI_LLM returns the compact Pagga-style ASCII logo (3 lines).
func asciiCHI_LLM() []string {
	// Extend the logo two characters on both sides with a fading ASCII gradient
	// to create a subtle trailing background. We use light (░) and medium (▒)
	// shade blocks that visually fade away from the heavy (▓) edge of the logo.
	// Left side:  "░▒" + original; Right side: original + "▒░"
	return []string{
		"░▒▓▒░█▀▀░█░█░▀█▀░░░░░░░░░█░░░█░░░█▄█░▒▓▒░",
		"░▒▓▒░█░░░█▀█░░█░░░░▄▄▄░░░█░░░█░░░█░█░▒▓▒░",
		"░▒▓▒░▀▀▀░▀░▀░▀▀▀░░░░░░░░░▀▀▀░▀▀▀░▀░▀░▒▓▒░",
	}
}

// visibleLen returns the naive visible width for plain ASCII content.
func visibleLen(s string) int { return utf8.RuneCountInString(s) }
