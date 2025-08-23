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
        // purple-only gradient palette (dark -> light)
        palette: []string{
            "#2D0B45",
            "#4C1D95",
            "#6D28D9",
            "#7C3AED",
            "#8B5CF6",
            "#A78BFA",
            "#C4B5FD",
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

// RenderBanner builds 2 lines of moving neon blocks.
func (a *Animator) RenderBanner(width int) string {
    if width <= 0 {
        return ""
    }
    lines := make([]string, 2)
    for row := 0; row < 2; row++ {
        var sb strings.Builder
        i := 0
        slow := a.frame / bannerSpeedDiv
        for i < width {
            idx := (i + slow + row*2) % len(a.palette)
            color := lipgloss.Color(a.palette[idx])
            // group 2 columns per color for a chunkier look
            chunk := 2
            if i+chunk > width {
                chunk = width - i
            }
            seg := strings.Repeat(" ", chunk) // color via background
            sb.WriteString(lipgloss.NewStyle().Background(color).Render(seg))
            i += chunk
        }
        lines[row] = sb.String()
    }
    return strings.Join(lines, "\n")
}

// RenderGrid makes a simple moving horizon grid (2 lines) using box characters.
func (a *Animator) RenderGrid(width int) string {
    if width <= 0 {
        return ""
    }
    // shift pattern over time
    offset := a.frame % 4
    patterns := []string{"┈┈╱╲", "┈╱╲┈", "╱╲┈┈", "╲┈┈╱"}
    p := patterns[offset]
    line1 := repeatToWidth(p, width)
    // second line with different phase/color
    p2 := patterns[(offset+2)%len(patterns)]
    line2 := repeatToWidth(p2, width)
    style1 := lipgloss.NewStyle().Foreground(lipgloss.Color("#7C3AED")) // violet
    style2 := lipgloss.NewStyle().Foreground(lipgloss.Color("#06B6D4")).Faint(true) // cyan
    return style1.Render(line1) + "\n" + style2.Render(line2)
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

    // Gradient palette left→right (purple→violet→blue→cyan).
    grad := []color.Color{
        lipgloss.Color("#7C3AED"), // purple
        lipgloss.Color("#8B5CF6"), // violet
        lipgloss.Color("#3B82F6"), // blue
        lipgloss.Color("#06B6D4"), // cyan
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
                        gi := 0
                        if trimmedAW > 1 {
                            gi = (ax * (len(grad) - 1)) / (trimmedAW - 1)
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
        return 1<<30
    }
    aw := len(occ[0])
    best := 1<<30
    // Search within a small fixed radius for performance.
    maxR := 3
    for d := 1; d <= maxR; d++ {
        // candidate square around (ax,ay)
        for y := ay - d; y <= ay + d; y++ {
            if y < 0 || y >= ah {
                continue
            }
            for x := ax - d; x <= ax + d; x++ {
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
    return []string{
        "░█▀▀░█░█░▀█▀░░░░░░░░░█░░░█░░░█▄█",
        "░█░░░█▀█░░█░░░░▄▄▄░░░█░░░█░░░█░█",
        "░▀▀▀░▀░▀░▀▀▀░░░░░░░░░▀▀▀░▀▀▀░▀░▀",
    }
}

// visibleLen returns the naive visible width for plain ASCII content.
func visibleLen(s string) int { return utf8.RuneCountInString(s) }
