package tui

import (
    "fmt"
    "os"
    "path/filepath"
    "regexp"
    "strings"
    "time"

    "github.com/charmbracelet/bubbles/v2/key"
    help "github.com/charmbracelet/bubbles/v2/help"
    "github.com/charmbracelet/bubbles/v2/spinner"
    "github.com/charmbracelet/bubbles/v2/viewport"
    tea "github.com/charmbracelet/bubbletea/v2"
    "github.com/charmbracelet/lipgloss/v2"

    "go-chi/internal/theme"
    "go-chi/internal/discovery"
)

// TOCItem represents a section in the table of contents
type TOCItem struct {
    Level   int    // Header level (1-6)
    Title   string // Header text
    Content string // Section content (from this header to next)
    Line    int    // Original line number
}

// Model implements the Bubble Tea model for provider selection.
type Model struct {
    keys      KeyMap
    mode      theme.Mode
    styles    theme.Styles
    providers []string
    index     int
    choice    string
    quitting  bool
    width     int
    height    int
    anim      Animator
    autoQuit  bool
    spin      spinner.Model
    help      help.Model
    showHelp  bool
    page      Page
    welcome   string
    vp        viewport.Model
    rebuildIx int
    // lastSaved holds the last config write path (if any)
    lastSaved string
    // model browser state
    providerForModels string
    modelItems        []modelItem
    modelIndex        int
    modelStatus       string
    providerModel     string
    // key highlight experiment
    lastKey    string
    lastKeyAt  time.Time
    // diagnostics
    diag      Diagnostics
    // TOC state
    tocItems      []TOCItem
    tocIndex      int  // Currently selected TOC item
    tocFocused    bool // Whether TOC has focus (vs content viewport)
    showTOC       bool // Toggle TOC visibility
    currentSection int  // Current section being displayed
}

// NewModel constructs a new Model instance.
func NewModel(providers []string, mode theme.Mode, autoQuit bool) Model {
    sp := spinner.New()
    sp.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#8B5CF6")).Bold(true)
    hp := help.New()
    vp := viewport.New(viewport.WithWidth(0), viewport.WithHeight(0))
    vp.MouseWheelEnabled = true
    wtxt := loadWelcome()
    toc := parseTOC(wtxt)
    return Model{
        keys:      DefaultKeyMap(),
        mode:      mode,
        styles:    theme.New(mode),
        providers: providers,
        index:     0,
        anim:      NewAnimator(true),
        autoQuit:  autoQuit,
        spin:      sp,
        help:      hp,
        page:      PageWelcome,
        welcome:   wtxt,
        vp:        vp,
        tocItems:  toc,
        showTOC:   true,
        tocIndex:  0,
        currentSection: 0,
    }
}

// Init is the Bubble Tea init function.
func (m Model) Init() tea.Cmd {
    cmds := []tea.Cmd{m.anim.Tick(), m.spin.Tick}
    if m.autoQuit {
        cmds = append(cmds, tea.Quit)
    }
    return tea.Batch(cmds...)
}

// Update handles messages.
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
    switch msg := msg.(type) {
    case tea.WindowSizeMsg:
        m.width, m.height = msg.Width, msg.Height
        // keep help width sensible
        fw, _ := m.styles.Frame.GetFrameSize()
        m.help.Width = max(0, m.width-fw)
        // Ensure welcome viewport has non-zero dimensions early
        if m.page == PageWelcome {
            m = m.ensureWelcomeViewportSize()
        }
        return m, nil
    case tea.KeyPressMsg:
        // record last key for highlight
        m.lastKey = strings.ToLower(msg.String())
        m.lastKeyAt = time.Now()
        // Welcome explicit scroll handling to avoid any mapping quirks
        if m.page == PageWelcome {
            // ensure viewport has dimensions before attempting scroll
            m = m.ensureWelcomeViewportSize()
            switch m.lastKey {
            case "h":
                // Toggle TOC visibility (empty panel)
                m.showTOC = !m.showTOC
                return m, nil
            case "up", "k":
                // Scroll content
                m.vp.SetYOffset(m.vp.YOffset() - 1)
                return m, nil
            case "down", "j":
                // Scroll content
                m.vp.SetYOffset(m.vp.YOffset() + 1)
                return m, nil
            case "pgup", "b":
                m.vp.PageUp()
                return m, nil
            case "pgdown", "space", "f":
                m.vp.PageDown()
                return m, nil
            case "u", "ctrl+u":
                m.vp.HalfPageUp()
                return m, nil
            case "d", "ctrl+d":
                m.vp.HalfPageDown()
                return m, nil
            }
        }
        switch {
        case key.Matches(msg, m.keys.Quit):
            m.quitting = true
            return m, tea.Quit
        case key.Matches(msg, m.keys.Back):
            // ESC key now goes back to Welcome from any page
            if m.page != PageWelcome {
                m.page = PageWelcome
                return m, nil
            }
            return m, nil
        case key.Matches(msg, m.keys.Sec1):
            m.page = PageWelcome
            return m, nil
        case key.Matches(msg, m.keys.Sec2):
            m.page = PageConfigure
            return m, nil
        case key.Matches(msg, m.keys.Sec3):
            m.page = PageDiagnostics
            m.diag = CollectDiagnostics()
            return m, nil
        case key.Matches(msg, m.keys.Sec4):
            m.page = PageRebuild
            return m, nil
        case key.Matches(msg, m.keys.Models):
            if m.page == PageConfigure {
                if len(m.providers) == 0 {
                    return m, nil
                }
                p := m.providers[m.index]
                // Allow model browsing for local, lmstudio, and ollama
                if p == "local" || p == "lmstudio" || p == "ollama" {
                    m.providerForModels = p
                    m.modelItems = nil
                    m.modelIndex = 0
                    m.modelStatus = "Loading models…"
                    m.page = PageModelBrowser
                    return m, fetchModelsCmd(p)
                }
                // For other providers, show a message
                if p == "openai" || p == "claude-cli" || p == "openai-cli" {
                    m.modelStatus = "Model browsing not available for " + p
                }
            }
            return m, nil
        case key.Matches(msg, m.keys.Help):
            m.showHelp = !m.showHelp
            m.help.ShowAll = m.showHelp
            return m, nil
        case key.Matches(msg, m.keys.Export):
            if m.page == PageDiagnostics {
                if p, err := ExportDiagnostics("", m.diag); err == nil {
                    m.lastSaved = p
                } else {
                    m.lastSaved = "(error)"
                }
                return m, nil
            }
            return m, nil
        case key.Matches(msg, m.keys.Anim):
            m.anim.Enabled = !m.anim.Enabled
            if m.anim.Enabled {
                return m, m.anim.Tick()
            }
            return m, nil
        case key.Matches(msg, m.keys.Toggle):
            if m.mode == theme.Light {
                m.mode = theme.Dark
            } else {
                m.mode = theme.Light
            }
            m.styles = theme.New(m.mode)
            return m, nil
        case key.Matches(msg, m.keys.Up):
            switch m.page {
            case PageWelcome:
                // Let viewport handle scroll on Welcome
                var cmd tea.Cmd
                m.vp, cmd = m.vp.Update(msg)
                return m, cmd
            case PageConfigure:
                if m.index > 0 {
                    m.index--
                }
            case PageRebuild:
                if m.rebuildIx > 0 {
                    m.rebuildIx--
                }
            case PageModelBrowser:
                if m.modelIndex > 0 { m.modelIndex-- }
            }
            return m, nil
        case key.Matches(msg, m.keys.Down):
            switch m.page {
            case PageWelcome:
                // Let viewport handle scroll on Welcome
                var cmd tea.Cmd
                m.vp, cmd = m.vp.Update(msg)
                return m, cmd
            case PageConfigure:
                if m.index < len(m.providers)-1 {
                    m.index++
                }
            case PageRebuild:
                if m.rebuildIx < 1 { // two options
                    m.rebuildIx++
                }
            case PageModelBrowser:
                if m.modelIndex < len(m.modelItems)-1 { m.modelIndex++ }
            }
            return m, nil
        case key.Matches(msg, m.keys.Enter):
            switch m.page {
            case PageConfigure:
                if len(m.providers) > 0 {
                    m.choice = m.providers[m.index]
                }
                m.page = PageRebuild
                return m, nil
            case PageModelBrowser:
                if len(m.modelItems) > 0 {
                    m.providerModel = m.modelItems[m.modelIndex].ID
                }
                m.page = PageConfigure
                return m, nil
            case PageRebuild:
                // Write local project config for now
                prov := m.choice
                if prov == "" && len(m.providers) > 0 {
                    prov = m.providers[m.index]
                }
                if prov == "" {
                    prov = "llamacpp"
                }
                if m.rebuildIx == 0 {
                    // project .chi_llm.json in CWD
                    if p, err := WriteProjectConfig(prov, m.providerModel); err == nil {
                        m.lastSaved = p
                    } else {
                        m.lastSaved = "(error)"
                    }
                } else {
                    // Global path follow-up; noop for now
                    m.lastSaved = "(global save: todo)"
                }
                m.quitting = true
                return m, tea.Quit
            default:
                // default behavior: quit with current selection
                if len(m.providers) > 0 {
                    m.choice = m.providers[m.index]
                }
                m.quitting = true
                return m, tea.Quit
            }
        default:
            // If we're on Welcome and the key wasn't handled above, let the viewport process it
            if m.page == PageWelcome {
                var cmd tea.Cmd
                m.vp, cmd = m.vp.Update(msg)
                return m, cmd
            }
        }
    case tickMsg:
        if m.anim.Enabled {
            m.anim.Next()
            return m, m.anim.Tick()
        }
    case spinner.TickMsg:
        var cmd tea.Cmd
        m.spin, cmd = m.spin.Update(msg)
        return m, cmd
    case modelListMsg:
        if msg.Err != "" {
            m.modelStatus = msg.Err
            m.modelItems = nil
        } else {
            m.modelStatus = ""
            m.modelItems = msg.Items
        }
        return m, nil
    case tea.MouseWheelMsg:
        if m.page == PageWelcome {
            var cmd tea.Cmd
            m.vp, cmd = m.vp.Update(msg)
            return m, cmd
        }
        mbtn := msg.Mouse().Button
        switch mbtn {
        case tea.MouseWheelDown:
            if m.page == PageModelBrowser {
                if m.modelIndex < len(m.modelItems)-1 { m.modelIndex++ }
            } else if m.index < len(m.providers)-1 { m.index++ }
            return m, nil
        case tea.MouseWheelUp:
            if m.page == PageModelBrowser {
                if m.modelIndex > 0 { m.modelIndex-- }
            } else if m.index > 0 { m.index-- }
            return m, nil
        }
    }
    return m, nil
}

// renderMenu renders the left menu panel
func (m Model) renderMenu(width, height int) string {
    if !m.showTOC {
        return ""
    }
    
    var lines []string
    
    // Title
    titleStyle := m.styles.Subtitle
    lines = append(lines, titleStyle.Render("Menu"))
    lines = append(lines, strings.Repeat("─", min(width, 30)))
    lines = append(lines, "") // spacer
    
    // Menu items
    menuItems := []struct {
        key   string
        label string
        page  Page
    }{
        {"1", "Welcome", PageWelcome},
        {"2", "Configure Provider", PageConfigure},
        {"3", "Diagnostics", PageDiagnostics},
    }
    
    for _, item := range menuItems {
        style := m.styles.Normal
        prefix := "  "
        
        // Highlight current page
        if item.page == m.page {
            style = m.styles.Selected
            prefix = "▸ "
        }
        
        line := fmt.Sprintf("%s[%s] %s", prefix, item.key, item.label)
        lines = append(lines, style.Render(line))
    }
    
    lines = append(lines, "") // spacer
    lines = append(lines, strings.Repeat("─", min(width, 30)))
    lines = append(lines, "") // spacer
    
    // Actions section
    lines = append(lines, m.styles.Help.Render("Actions:"))
    
    actionItems := []struct {
        key   string
        label string
        desc  string
    }{
        {"b", "Build", "Build configuration"},
        {"?", "Help", "Toggle help"},
        {"q", "Quit", "Exit application"},
    }
    
    for _, item := range actionItems {
        line := fmt.Sprintf("  [%s] %s", item.key, item.label)
        lines = append(lines, m.styles.Normal.Render(line))
    }
    
    // Fill the rest with empty lines
    for len(lines) < height {
        lines = append(lines, "")
    }
    
    // Join and return
    return strings.Join(lines, "\n")
}

// View renders the UI.
func (m Model) View() string {
    // Compute inner content area (minus frame border/padding)
    frameW, frameH := m.styles.Frame.GetFrameSize()
    innerW := max(0, m.width-frameW)
    innerH := max(0, m.height-frameH)
    if innerW == 0 { // first render before WindowSizeMsg
        innerW = 60
    }
    if innerH == 0 {
        innerH = 20
    }

    // Sections
    // Grid split into top/bottom lines
    gtop, gbottom := "", ""
    if g := m.anim.RenderGrid(innerW); g != "" {
        parts := strings.SplitN(g, "\n", 2)
        gtop = parts[0]
        if len(parts) > 1 {
            gbottom = parts[1]
        }
    }
    // Compact hero: scale=1 (no extra vertical margin)
    hero := m.anim.RenderHero(innerW, 1)
    heroLines := 0
    if hero != "" { heroLines = len(strings.Split(hero, "\n")) }
    // Title and subtitle are overlaid inside hero; no separate lines here
    // Compute overlay subtitle text (unstyled padding not required)
    overlaySubtitle := m.styles.Subtitle.Render(m.subtitle())

    // list (for configure page)
    items := make([]string, 0, len(m.providers))
    if m.page == PageConfigure {
        items = make([]string, len(m.providers))
        for i, p := range m.providers {
            style := m.styles.Normal
            pointer := "  "
            if i == m.index {
                style = m.styles.Selected
                pointer = m.styles.Highlight.Render("› ")
            }
            items[i] = padANSI(style.Render(pointer+p), innerW)
        }
    }

    // Help legend with pressed-key highlight
    help := padANSI(m.renderLegend(innerW), innerW)
    themeLbl := padANSI(m.styles.Help.Render(fmt.Sprintf("anim: %v", m.anim.Enabled)), innerW)

    // Build content lines
    var lines []string
    // Place top grid line above hero (if present)
    if gtop != "" { lines = append(lines, gtop) }
    if hero != "" { lines = append(lines, strings.Split(hero, "\n")...) }
    // Place bottom grid line directly under hero
    if gbottom != "" { lines = append(lines, gbottom) }
    // One spacer line under the animation before content; pages add their own content
    lines = append(lines, strings.Repeat(" ", innerW))
    // Body per page
    // header height (top grid + hero + bottom grid + spacer)
    headerLines := 0
    if gtop != "" { headerLines++ }
    headerLines += heroLines
    if gbottom != "" { headerLines++ }
    headerLines++ // spacer under grid

    switch m.page {
    case PageWelcome:
        bodyHeight := max(3, innerH-headerLines-2) // leave lines for help/theme
        
        // Calculate TOC and content widths
        tocWidth := 0
        if m.showTOC && len(m.tocItems) > 0 {
            tocWidth = innerW / 3 // 33% for TOC (was 25%)
            if tocWidth < 25 {
                tocWidth = 25 // Minimum width (was 20)
            }
            if tocWidth > 50 {
                tocWidth = 50 // Maximum width (was 40)
            }
        }
        contentWidth := innerW - tocWidth
        if tocWidth > 0 {
            contentWidth -= 3 // Space for separator " │ "
        }
        
        // Set viewport size and content first
        pw, ph := m.styles.Panel.GetFrameSize()
        vpWidth := max(0, contentWidth-pw)
        vpHeight := max(1, bodyHeight-ph)
        if m.vp.Width() != vpWidth { m.vp.SetWidth(vpWidth) }
        if m.vp.Height() != vpHeight { m.vp.SetHeight(vpHeight) }
        
        // Always show full content, not sections
        m.vp.SetContent(m.welcome)
        
        // Build the display line by line
        if m.showTOC {
            // Render both panels
            menuLines := strings.Split(m.renderMenu(tocWidth, bodyHeight), "\n")
            contentPanel := m.styles.Panel.Render(m.vp.View())
            contentLines := strings.Split(contentPanel, "\n")
            
            // Ensure both have same number of lines
            for len(menuLines) < bodyHeight {
                menuLines = append(menuLines, "")
            }
            for len(contentLines) < bodyHeight {
                contentLines = append(contentLines, "")
            }
            
            // Combine line by line with proper padding
            for i := 0; i < bodyHeight && i < len(menuLines) && i < len(contentLines); i++ {
                // Pad menu line to fixed width
                menuLine := padANSI(menuLines[i], tocWidth)
                // Combine with separator and content
                line := menuLine + " │ " + contentLines[i]
                lines = append(lines, line)
            }
        } else {
            // No TOC, just show content panel
            contentPanel := m.styles.Panel.Render(m.vp.View())
            lines = append(lines, strings.Split(contentPanel, "\n")...)
        }
        
        // Simple status line
        status := "h: toggle menu | arrows/pgup/pgdn: scroll | 1-4: navigate sections"
        lines = append(lines, padANSI(m.styles.Help.Render(status), innerW))
    case PageConfigure:
        bodyHeight := max(3, innerH-headerLines-2) // leave lines for help/theme
        
        // Calculate menu and content widths (same as Welcome)
        menuWidth := 0
        if m.showTOC {
            menuWidth = innerW / 3
            if menuWidth < 25 {
                menuWidth = 25
            }
            if menuWidth > 50 {
                menuWidth = 50
            }
        }
        contentWidth := innerW - menuWidth
        if menuWidth > 0 {
            contentWidth -= 3 // Space for separator " │ "
        }
        
        // Build provider list with details
        var providerLines []string
        providerLines = append(providerLines, m.styles.Subtitle.Render("Select Provider"))
        providerLines = append(providerLines, "")
        
        for i, p := range m.providers {
            style := m.styles.Normal
            pointer := "  "
            if i == m.index {
                style = m.styles.Selected
                pointer = "▸ "
            }
            
            // Add provider name with description
            providerName := p
            switch p {
            case "local":
                providerName = "Local (GGUF models)"
            case "lmstudio":
                providerName = "LM Studio (server)"
            case "ollama":
                providerName = "Ollama (server)"
            case "openai":
                providerName = "OpenAI (API)"
            case "claude-cli":
                providerName = "Claude CLI (bridge)"
            case "openai-cli":
                providerName = "OpenAI CLI (bridge)"
            }
            
            providerLines = append(providerLines, style.Render(pointer+providerName))
        }
        
        // Add provider details section
        if len(m.providers) > 0 && m.index < len(m.providers) {
            providerLines = append(providerLines, "")
            providerLines = append(providerLines, m.styles.Subtitle.Render("Details"))
            
            selected := m.providers[m.index]
            switch selected {
            case "local":
                providerLines = append(providerLines, m.styles.Help.Render("Uses local GGUF models"))
                providerLines = append(providerLines, m.styles.Help.Render("No server required"))
            case "lmstudio", "ollama":
                providerLines = append(providerLines, m.styles.Help.Render("Host: localhost"))
                port := "1234"
                if selected == "ollama" {
                    port = "11434"
                }
                providerLines = append(providerLines, m.styles.Help.Render("Port: "+port))
                providerLines = append(providerLines, m.styles.Help.Render("Press 'm' to browse models"))
            case "openai", "claude-cli", "openai-cli":
                providerLines = append(providerLines, m.styles.Help.Render("Requires API key"))
                providerLines = append(providerLines, m.styles.Help.Render("Set in environment"))
            }
            
            if m.providerModel != "" {
                providerLines = append(providerLines, "")
                providerLines = append(providerLines, m.styles.Normal.Render("Selected model: ")+m.providerModel)
            }
        }
        
        // Add actions hint
        providerLines = append(providerLines, "")
        providerLines = append(providerLines, m.styles.Help.Render("Actions:"))
        providerLines = append(providerLines, m.styles.Help.Render("  [Enter] Select provider"))
        providerLines = append(providerLines, m.styles.Help.Render("  [m] Browse models (if available)"))
        providerLines = append(providerLines, m.styles.Help.Render("  [b] Build configuration"))
        
        // Ensure content fits in available space
        for len(providerLines) < bodyHeight {
            providerLines = append(providerLines, "")
        }
        
        // Build the display with menu panel
        if m.showTOC {
            menuLines := strings.Split(m.renderMenu(menuWidth, bodyHeight), "\n")
            
            // Ensure both have same number of lines
            for len(menuLines) < bodyHeight {
                menuLines = append(menuLines, "")
            }
            for len(providerLines) < bodyHeight {
                providerLines = append(providerLines, "")
            }
            
            // Combine line by line with proper padding
            for i := 0; i < bodyHeight && i < len(menuLines) && i < len(providerLines); i++ {
                menuLine := padANSI(menuLines[i], menuWidth)
                contentLine := padANSI(providerLines[i], contentWidth)
                line := menuLine + " │ " + contentLine
                lines = append(lines, line)
            }
        } else {
            // No menu, just show provider content
            for _, line := range providerLines {
                lines = append(lines, padANSI(line, innerW))
            }
        }
    case PageRebuild:
        lines = append(lines, strings.Repeat(" ", innerW))
        opts := []string{
            fmt.Sprintf("This directory (%s)", cwdBase()),
            "Globally (~/.chi_llm.json)",
        }
        for i, o := range opts {
            style := m.styles.Normal
            pointer := "  "
            if i == m.rebuildIx {
                style = m.styles.Selected
                pointer = m.styles.Highlight.Render("› ")
            }
            lines = append(lines, padANSI(style.Render(pointer+o), innerW))
        }
    case PageDiagnostics:
        lines = append(lines, padANSI(m.styles.Subtitle.Render("Diagnostics"), innerW))
        if m.diag.ConfigPath != "" {
            lines = append(lines, padANSI(m.styles.Normal.Render("config: ")+m.diag.ConfigPath, innerW))
        } else {
            lines = append(lines, padANSI(m.styles.Normal.Render("config: (none)"), innerW))
        }
        if m.diag.ProviderType != "" {
            lines = append(lines, padANSI(m.styles.Normal.Render("provider: ")+m.diag.ProviderType, innerW))
        }
        if m.diag.ProviderModel != "" {
            lines = append(lines, padANSI(m.styles.Normal.Render("model: ")+m.diag.ProviderModel, innerW))
        }
        if len(m.diag.Env) > 0 {
            lines = append(lines, padANSI(m.styles.Subtitle.Render("env"), innerW))
            for k, v := range m.diag.Env {
                lines = append(lines, padANSI(m.styles.Help.Render(k+": ")+v, innerW))
            }
        }
        if len(m.diag.Hints) > 0 {
            lines = append(lines, padANSI(m.styles.Subtitle.Render("hints"), innerW))
            for _, h := range m.diag.Hints {
                lines = append(lines, padANSI(m.styles.Help.Render("- ")+h, innerW))
            }
        }
        if m.lastSaved != "" {
            lines = append(lines, padANSI(m.styles.Help.Render("saved: ")+m.lastSaved, innerW))
        } else {
            lines = append(lines, padANSI(m.styles.Help.Render("press 'e' to export"), innerW))
        }
    case PageModelBrowser:
        lines = append(lines, padANSI(m.styles.Subtitle.Render("Browse models for ")+m.providerForModels, innerW))
        if m.modelStatus != "" {
            lines = append(lines, padANSI(m.styles.Help.Render(m.modelStatus), innerW))
        }
        if len(m.modelItems) == 0 && m.modelStatus == "" {
            lines = append(lines, padANSI(m.styles.Help.Render("No models"), innerW))
        }
        for i, it := range m.modelItems {
            style := m.styles.Normal
            pointer := "  "
            if i == m.modelIndex {
                style = m.styles.Selected
                pointer = m.styles.Highlight.Render("› ")
            }
            label := it.ID
            if it.SizeMB > 0 {
                label = fmt.Sprintf("%s  (%d MB)", it.ID, it.SizeMB)
            }
            lines = append(lines, padANSI(style.Render(pointer+label), innerW))
        }
    }
    lines = append(lines, strings.Repeat(" ", innerW), help, themeLbl)

    // Fill remaining height so frame renders full-screen
    need := innerH - len(lines)
    for i := 0; i < max(0, need); i++ {
        lines = append(lines, strings.Repeat(" ", innerW))
    }

    // Build header/body and compose using lipgloss v2 layers

    header := strings.Join(lines[:headerLines], "\n")
    body := strings.Join(lines[headerLines:], "\n")

    layers := []*lipgloss.Layer{
        lipgloss.NewLayer(body).X(0).Y(headerLines),
        lipgloss.NewLayer(header).X(0).Y(0),
    }
    // Overlay title and subtitle inside hero region, aligned to the left
    if m.headerTitle() != "" {
        overlayLine := m.styles.Title.Render(m.headerTitle())
        overlayY := 0
        if gtop != "" { overlayY++ }
        if heroLines > 0 { overlayY += heroLines / 2 }
        layers = append(layers, lipgloss.NewLayer(overlayLine).X(0).Y(overlayY))
        // subtitle directly under title
        if overlaySubtitle != "" {
            layers = append(layers, lipgloss.NewLayer(overlaySubtitle).X(0).Y(overlayY+1))
        }
    }
    canvas := lipgloss.NewCanvas(layers...)
    content := canvas.Render()
    // Expand frame to full terminal size
    return m.styles.Frame.Width(m.width).Height(m.height).Render(content)
}

// headerTitle by page
func (m Model) headerTitle() string {
    switch m.page {
    case PageWelcome:
        return "chi-llm • welcome"
    case PageConfigure:
        return "chi-llm • configure provider"
    case PageRebuild:
        return "chi-llm • (re)build configuration"
    case PageDiagnostics:
        return "chi-llm • diagnostics"
    case PageModelBrowser:
        return "chi-llm • provider models"
    default:
        return "chi-llm"
    }
}

func (m Model) subtitle() string {
    switch m.page {
    case PageWelcome:
        return "Readme excerpt"
    case PageConfigure:
        return "Choose your provider"
    case PageRebuild:
        return "Where to write configuration?"
    case PageDiagnostics:
        return "Provider status and environment"
    case PageModelBrowser:
        return "Pick a model for the provider"
    default:
        return ""
    }
}

// Page enumerates app sections
type Page int

const (
    PageWelcome Page = iota
    PageConfigure
    PageRebuild
    PageDiagnostics
    PageModelBrowser
)

func loadWelcome() string {
    // Try README.md (or docs/CLI.md) from current dir or parents
    start, _ := os.Getwd()
    dir := start
    for i := 0; i < 8; i++ { // search more levels up for safety
        candidates := []string{
            filepath.Join(dir, "README.md"),
            filepath.Join(dir, "docs", "CLI.md"),
        }
        for _, p := range candidates {
            if b, err := os.ReadFile(p); err == nil && len(b) > 0 {
                // Return full content without truncation
                return string(b)
            }
        }
        nd := filepath.Dir(dir)
        if nd == dir { break }
        dir = nd
    }
    // Fallback content with multiple lines to ensure scrolling works
    var sb strings.Builder
    sb.WriteString("Welcome to chi-llm! Use 2 to configure provider and 3 to write configuration.\n\n")
    for i := 1; i <= 150; i++ {
        sb.WriteString(fmt.Sprintf("Line %03d — press PgDn/PgUp to test scrolling\n", i))
    }
    return sb.String()
}

func cwdBase() string {
    wd, _ := os.Getwd()
    return filepath.Base(wd)
}

// parseTOC parses markdown content and extracts headers with their sections
func parseTOC(content string) []TOCItem {
    if content == "" {
        return nil
    }
    
    var items []TOCItem
    lines := strings.Split(content, "\n")
    headerRegex := regexp.MustCompile(`^(#{1,6})\s+(.+)$`)
    
    // First pass: find all headers
    type headerInfo struct {
        level int
        title string
        line  int
    }
    var headers []headerInfo
    
    inCodeBlock := false
    for i, line := range lines {
        // Check for code block markers
        if strings.HasPrefix(line, "```") {
            inCodeBlock = !inCodeBlock
            continue
        }
        
        // Skip headers inside code blocks
        if inCodeBlock {
            continue
        }
        
        if matches := headerRegex.FindStringSubmatch(line); matches != nil {
            level := len(matches[1])
            title := matches[2]
            
            // Skip headers that look like comments in code
            // (they often follow patterns like "# Basic installation")
            if level == 1 && i > 0 {
                prevLine := lines[i-1]
                // If previous line is ``` or empty after ```, likely a code comment
                if strings.HasPrefix(prevLine, "```") || (i > 1 && strings.HasPrefix(lines[i-2], "```")) {
                    continue
                }
            }
            
            headers = append(headers, headerInfo{
                level: level,
                title: title,
                line:  i,
            })
        }
    }
    
    // If no headers found, return the whole content as a single section
    if len(headers) == 0 {
        return []TOCItem{{
            Level:   1,
            Title:   "Document",
            Content: content,
            Line:    0,
        }}
    }
    
    // Second pass: extract content for each section
    for i, h := range headers {
        startLine := h.line
        var endLine int
        if i < len(headers)-1 {
            endLine = headers[i+1].line
        } else {
            endLine = len(lines)
        }
        
        // Extract section content (from current header to next header)
        sectionLines := lines[startLine:endLine]
        sectionContent := strings.Join(sectionLines, "\n")
        
        items = append(items, TOCItem{
            Level:   h.level,
            Title:   h.title,
            Content: sectionContent,
            Line:    startLine,
        })
    }
    
    return items
}

// Selected returns the chosen provider or empty string.
func (m Model) Selected() string { return m.choice }

// WritePath returns the last config write path (if any).
func (m Model) WritePath() string { return m.lastSaved }

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

// padANSI pads s with spaces to target width, accounting for printable width.
func padANSI(s string, width int) string {
    w := lipgloss.Width(s)
    if w >= width {
        return s
    }
    return s + strings.Repeat(" ", width-w)
}

// modelItem is a simple item to render in the model browser list.
type modelItem struct {
    ID     string
    SizeMB int64
}

// modelListMsg carries async discovery results into the update loop.
type modelListMsg struct {
    Items []modelItem
    Err   string
}

// fetchModelsCmd asynchronously discovers models for a provider.
func fetchModelsCmd(provider string) tea.Cmd {
    return func() tea.Msg {
        infos, err := discovery.Discover(provider, "", 0)
        if err != nil {
            return modelListMsg{Err: err.Error()}
        }
        items := make([]modelItem, 0, len(infos))
        for _, inf := range infos {
            items = append(items, modelItem{ID: inf.ID, SizeMB: inf.SizeMB()})
        }
        return modelListMsg{Items: items}
    }
}

// ensureWelcomeViewportSize computes and sets a reasonable viewport size for Welcome page.
func (m Model) ensureWelcomeViewportSize() Model {
    frameW, frameH := m.styles.Frame.GetFrameSize()
    innerW := max(0, m.width-frameW)
    innerH := max(0, m.height-frameH)
    if innerW <= 0 || innerH <= 0 {
        return m
    }
    // Estimate header lines similarly to View
    g := m.anim.RenderGrid(innerW)
    gtop, gbottom := 0, 0
    if g != "" {
        parts := strings.SplitN(g, "\n", 2)
        if len(parts) > 0 && parts[0] != "" { gtop = 1 }
        if len(parts) > 1 && parts[1] != "" { gbottom = 1 }
    }
    hero := m.anim.RenderHero(innerW, 1)
    heroLines := 0
    if hero != "" { heroLines = len(strings.Split(hero, "\n")) }
    headerLines := gtop + heroLines + gbottom + 1 // + spacer
    bodyHeight := max(3, innerH-headerLines-2)    // reserve lines for legend/status
    if m.vp.Width() != innerW { m.vp.SetWidth(innerW) }
    if m.vp.Height() != bodyHeight { m.vp.SetHeight(bodyHeight) }
    // Ensure content is set when viewport size changes
    if m.vp.GetContent() == "" {
        m.vp.SetContent(m.welcome)
    }
    return m
}

// renderLegend builds a one-line legend using KeyMap, highlighting the last pressed key
// for a short duration.
func (m Model) renderLegend(width int) string {
    // active window for highlight
    const ttl = 800 * time.Millisecond
    active := false
    key := m.lastKey
    if !m.lastKeyAt.IsZero() && time.Since(m.lastKeyAt) < ttl {
        active = true
    }
    // row from ShortHelp bindings
    bindings := m.keys.ShortHelp()
    parts := make([]string, 0, len(bindings))
    for _, b := range bindings {
        if !b.Enabled() { continue }
        h := b.Help()
        keyLabel := h.Key
        // Highlight if the last pressed key matches any of this binding's keys
        style := m.styles.Help
        if active {
            for _, k := range b.Keys() {
                if strings.ToLower(k) == key {
                    style = m.styles.Selected
                    break
                }
            }
        }
        // Render as [key] desc
        part := style.Render("[" + keyLabel + "]") + " " + m.styles.Help.Render(h.Desc)
        parts = append(parts, part)
    }
    s := strings.Join(parts, "  ")
    if width > 0 { s = padANSI(s, width) }
    return s
}
