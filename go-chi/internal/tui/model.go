package tui

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	help "github.com/charmbracelet/bubbles/v2/help"
	"github.com/charmbracelet/bubbles/v2/key"
	"github.com/charmbracelet/bubbles/v2/spinner"
	"github.com/charmbracelet/bubbles/v2/textinput"
	"github.com/charmbracelet/bubbles/v2/viewport"
	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/glamour"
	"github.com/charmbracelet/lipgloss/v2"

	"go-chi/internal/discovery"
	"go-chi/internal/theme"
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
	// save banner state
	showSaveBanner bool      // Whether to show save success banner
	saveBannerMsg  string    // Banner message to display
	saveBannerAt   time.Time // When banner was shown
	// model browser state
	providerForModels   string
	modelItems          []modelItem
	modelAllItems       []modelItem
	modelIndex          int
	modelStatus         string
	providerModel       string
	modelDownloadedOnly bool
	modelTagFilter      string
	modelTagIndex       int
	availableRAMGB      float64
	// key highlight experiment
	lastKey   string
	lastKeyAt time.Time
	// diagnostics
	diag Diagnostics
	// TOC state
	tocItems       []TOCItem
	tocIndex       int  // Currently selected TOC item
	tocFocused     bool // Whether TOC has focus (vs content viewport)
	showTOC        bool // Toggle TOC visibility
	currentSection int  // Current section being displayed
	// Menu cache to prevent flickering
	cachedMenu       string // Cached rendered menu
	cachedMenuWidth  int    // Width the menu was cached for
	cachedMenuHeight int    // Height the menu was cached for
	cachedMenuPage   Page   // Page the menu was cached for
	// Multi-provider configuration state
	configuredProviders []ConfiguredProvider // Configured providers from chi.tmp.json
	selectedProviderIdx int                  // Currently selected configured provider
	availableTags       []string             // Available tags from chi_llm
	defaultProviderID   string               // ID of the default provider

	// Provider management
	addingProvider    bool     // Whether we're in "add provider" mode
	newProviderType   string   // Type of provider being added
	availableTypes    []string // Available provider types to add
	typeDropdownIndex int      // Index in provider type dropdown

	// Provider editing state
	editingProvider      bool                // Whether we're editing an existing provider
	editingProviderIndex int                 // Index of provider being edited
	tempProvider         *ConfiguredProvider // Temporary provider during editing

	// Text inputs for configuration
	hostInput    textinput.Model
	portInput    textinput.Model
	apiKeyInput  textinput.Model
	baseURLInput textinput.Model
	orgIDInput   textinput.Model
	nameInput    textinput.Model // Provider name input

	// Tag management
	selectedTags     []string // Currently selected tags for provider
	tagDropdownIndex int      // Index in tags dropdown
	showingTags      bool     // Whether tag dropdown is shown

	// Field editing state
	editingField string // Which field is being edited ("host", "port", "api_key", etc.)
	fieldIndex   int    // Index of currently selected field

	// Connection testing state
	isTestingConnection bool
	connectionStatus    ConnectionStatus
	lastTestTime        time.Time

	// Cached layout for Welcome page
	welcomeTOCWidth int // cached TOC width to keep widths stable across frames

	// Start menu (Welcome) state
	startMenuItems []startMenuItem
	startMenuIndex int
}

// resumeAnimMsg signals that we should re-enable animation after a short pause
// used to prevent flicker while actively scrolling content.
type resumeAnimMsg struct{}

func resumeAnimAfterDelay() tea.Cmd {
	return tea.Tick(220*time.Millisecond, func(time.Time) tea.Msg { return resumeAnimMsg{} })
}

// startMenuItem represents an entry on the Welcome screen.
type startMenuItem struct {
	Label string
	Page  Page
	Help  string
}

// welcomeHeaderLines defines the fixed number of header rows on the Welcome
// page: 2 lines of grid + 3 lines of hero + 1 spacer = 6 total. Using a
// constant prevents +/-1 oscillations that can cause the menu to "jump" when
// scrolling or when the animation ticks.
const welcomeHeaderLines = 6

// NewModel constructs a new Model instance.
func NewModel(providers []string, mode theme.Mode, autoQuit bool) Model {
	sp := spinner.New()
	sp.Style = lipgloss.NewStyle().Foreground(lipgloss.Color("#8B5CF6")).Bold(true)
	hp := help.New()
	vp := viewport.New(viewport.WithWidth(0), viewport.WithHeight(0))
	vp.MouseWheelEnabled = true
	wtxt := loadWelcome()
	// Render markdown once during initialization with a reasonable default width
	wtxtRendered := renderMarkdown(wtxt, 80)
	toc := parseTOC(wtxt) // Parse TOC from raw markdown, not rendered

	// Set viewport content once during initialization
	vp.SetContent(wtxtRendered)

	// Load configured providers and default provider ID
	configuredProviders, defaultProviderID, _ := ReadMultiProviderConfigWithDefault()

	// Load available tags
	availableTags, _ := GetAvailableTags()

	// Initialize text inputs
	hostInput := textinput.New()
	hostInput.Placeholder = "localhost"

	portInput := textinput.New()
	portInput.Placeholder = "1234"

	apiKeyInput := textinput.New()
	apiKeyInput.Placeholder = "sk-..."
	apiKeyInput.EchoMode = textinput.EchoPassword

	baseURLInput := textinput.New()
	baseURLInput.Placeholder = "https://api.openai.com"

	orgIDInput := textinput.New()
	orgIDInput.Placeholder = "org-..."

	nameInput := textinput.New()
	nameInput.Placeholder = "Provider Name"

	// Define start menu items
	sm := []startMenuItem{
		{Label: "README.md", Page: PageReadme, Help: "Project overview"},
		{Label: "Configure Providers", Page: PageConfigure, Help: "Add/edit providers"},
		{Label: "Select Default", Page: PageSelectDefault, Help: "Choose default provider"},
		{Label: "Diagnostics", Page: PageDiagnostics, Help: "Environment and status"},
		{Label: "Build Configuration", Page: PageRebuild, Help: "Write project config"},
		{Label: "Settings", Page: PageSettings, Help: "General preferences"},
		{Label: "EXIT", Page: PageExit, Help: "Quit application"},
	}

	return Model{
		keys:           DefaultKeyMap(),
		mode:           mode,
		styles:         theme.New(mode),
		providers:      providers,
		index:          0,
		anim:           NewAnimator(true),
		autoQuit:       autoQuit,
		spin:           sp,
		help:           hp,
		page:           PageWelcome,
		welcome:        wtxtRendered, // Store the rendered markdown
		vp:             vp,
		tocItems:       toc,
		showTOC:        true,
		tocIndex:       0,
		currentSection: 0,
		// Multi-provider configuration
		configuredProviders: configuredProviders,
		selectedProviderIdx: 0,
		availableTags:       availableTags,
		defaultProviderID:   defaultProviderID,
		availableTypes:      providers, // Use the providers passed to constructor
		// Text inputs
		hostInput:    hostInput,
		portInput:    portInput,
		apiKeyInput:  apiKeyInput,
		baseURLInput: baseURLInput,
		orgIDInput:   orgIDInput,
		nameInput:    nameInput,
		// Start menu
		startMenuItems: sm,
		startMenuIndex: 0,
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
		// Ensure viewport has stable dimensions early for pages using it
		if m.page == PageWelcome || m.page == PageReadme {
			m = m.ensureWelcomeViewportSize()
		}
		return m, nil
	case connectionTestMsg:
		// Handle connection test results
		m.isTestingConnection = false
		m.connectionStatus = msg.status
		return m, nil
	case tea.KeyPressMsg:
		// Handle text input if we're editing a field
		if m.page == PageConfigure && m.editingField != "" {
			var cmd tea.Cmd
			switch m.editingField {
			case "host":
				m.hostInput, cmd = m.hostInput.Update(msg)
			case "port":
				m.portInput, cmd = m.portInput.Update(msg)
			case "api_key":
				m.apiKeyInput, cmd = m.apiKeyInput.Update(msg)
			case "base_url":
				m.baseURLInput, cmd = m.baseURLInput.Update(msg)
			case "org_id":
				m.orgIDInput, cmd = m.orgIDInput.Update(msg)
			}

			// Handle ESC to cancel editing
			if key.Matches(msg, key.NewBinding(key.WithKeys("esc"))) {
				m.editingField = ""
				m.hostInput.Blur()
				m.portInput.Blur()
				m.apiKeyInput.Blur()
				m.baseURLInput.Blur()
				m.orgIDInput.Blur()
				return m, nil
			}

			return m, cmd
		}

		// record last key for highlight
		m.lastKey = strings.ToLower(msg.String())
		m.lastKeyAt = time.Now()
		// Welcome explicit handling: navigate the start menu
		if m.page == PageWelcome {
			switch m.lastKey {
			case "h":
				// Toggle TOC (not shown on Welcome, but keep behavior consistent)
				m.showTOC = !m.showTOC
				m = m.ensureWelcomeViewportSize()
				return m, nil
			case "up", "k":
				if m.startMenuIndex > 0 {
					m.startMenuIndex--
				}
				return m, nil
			case "down", "j":
				if m.startMenuIndex < len(m.startMenuItems)-1 {
					m.startMenuIndex++
				}
				return m, nil
			case "pgup":
				m.startMenuIndex = 0
				return m, nil
			case "pgdown", "space", "f":
				if len(m.startMenuItems) > 0 {
					m.startMenuIndex = len(m.startMenuItems) - 1
				}
				return m, nil
			case "enter":
				if len(m.startMenuItems) > 0 {
					sel := m.startMenuItems[m.startMenuIndex]
					if sel.Page == PageExit {
						m.quitting = true
						return m, tea.Quit
					}
					m.page = sel.Page
				}
				return m, nil
			}
		}
		switch {
		case key.Matches(msg, m.keys.Quit):
			m.quitting = true
			return m, tea.Quit
		case key.Matches(msg, m.keys.Back):
			// ESC key handling - priority: tags > edit mode > adding mode > page navigation
			if m.page == PageConfigure {
				if m.showingTags {
					// Exit tags selection mode
					m.showingTags = false
					return m, nil
				} else if m.editingProvider {
					// Exit provider editing mode
					m.editingProvider = false
					m.tempProvider = nil
					m.editingProviderIndex = -1
					m.editingField = ""
					m.showingTags = false // Reset tags dropdown state
					return m, nil
				} else if m.addingProvider {
					// Exit add provider mode
					m.addingProvider = false
					return m, nil
				}
			}

			// Default: go back to Welcome from any page
			if m.page != PageWelcome {
				m.page = PageWelcome
				// Ensure viewport dimensions when entering Welcome
				m = m.ensureWelcomeViewportSize()
				return m, nil
			}
			return m, nil
		case key.Matches(msg, m.keys.Sec1):
			m.page = PageReadme
			// Ensure viewport dimensions when entering README
			m = m.ensureWelcomeViewportSize()
			return m, nil
		case key.Matches(msg, m.keys.Sec2):
			m.page = PageConfigure
			return m, nil
		case key.Matches(msg, m.keys.Sec3):
			m.page = PageSelectDefault
			return m, nil
		case key.Matches(msg, m.keys.Sec4):
			m.page = PageDiagnostics
			m.diag = CollectDiagnostics()
			return m, nil
		case key.Matches(msg, m.keys.Sec5):
			m.page = PageRebuild
			return m, nil
		case key.Matches(msg, m.keys.Settings):
			m.page = PageSettings
			return m, nil
		case key.Matches(msg, m.keys.Test):
			// Test connection for server-based providers
			if m.page == PageConfigure && m.editingProvider && m.tempProvider != nil {
				if NeedsConfiguration(m.tempProvider.Type) && !m.isTestingConnection {
					m.isTestingConnection = true
					m.lastTestTime = time.Now()

					// Update temp provider with current field values before testing
					testConfig := m.tempProvider.Config
					testConfig.Host = m.hostInput.Value()
					testConfig.Port = m.portInput.Value()
					testConfig.APIKey = m.apiKeyInput.Value()
					testConfig.BaseURL = m.baseURLInput.Value()
					testConfig.OrgID = m.orgIDInput.Value()

					return m, testConnectionCmd(testConfig)
				}
			}
			return m, nil
		case key.Matches(msg, m.keys.Add):
			// Toggle add provider mode
			if m.page == PageConfigure {
				if !m.editingProvider { // Only allow if not currently editing
					m.addingProvider = !m.addingProvider
					if m.addingProvider {
						m.typeDropdownIndex = 0
					}
				}
			}
			return m, nil
		case key.Matches(msg, m.keys.Save):
			// Save provider configuration
			if m.page == PageConfigure {
				if m.editingProvider && m.tempProvider != nil {
					// Update temp provider from input fields
					m.tempProvider.Config.Host = m.hostInput.Value()
					m.tempProvider.Config.Port = m.portInput.Value()
					m.tempProvider.Config.APIKey = m.apiKeyInput.Value()
					m.tempProvider.Config.BaseURL = m.baseURLInput.Value()
					m.tempProvider.Config.OrgID = m.orgIDInput.Value()
					m.tempProvider.Name = m.nameInput.Value()
					if m.nameInput.Value() == "" {
						m.tempProvider.Name = m.tempProvider.Type + " provider"
					}
					m.tempProvider.Tags = append([]string{}, m.selectedTags...)

					// Basic validation
					validationError := ""
					switch m.tempProvider.Type {
					case "openai":
						if m.tempProvider.Config.APIKey == "" {
							validationError = "API Key is required for OpenAI provider"
						}
					case "ollama", "lmstudio":
						if m.tempProvider.Config.Host == "" {
							validationError = "Host is required for " + m.tempProvider.Type
						}
					}

					if validationError != "" {
						m.lastSaved = "(validation error: " + validationError + ")"
						return m, nil
					}

					// Save to configured providers
					if m.editingProviderIndex == -1 {
						// New provider - add to list
						m.configuredProviders = append(m.configuredProviders, *m.tempProvider)
						m.selectedProviderIdx = len(m.configuredProviders) - 1
					} else {
						// Update existing provider
						if m.editingProviderIndex < len(m.configuredProviders) {
							m.configuredProviders[m.editingProviderIndex] = *m.tempProvider
						}
					}

					// Write to file
					if p, err := WriteMultiProviderConfigWithDefault(m.configuredProviders, m.defaultProviderID); err == nil {
						m.lastSaved = p
					} else {
						m.lastSaved = "(error)"
					}

					// Exit editing mode
					m.editingProvider = false
					m.tempProvider = nil
					m.editingProviderIndex = -1
					m.editingField = "" // Clear any field editing
				} else if len(m.configuredProviders) > 0 {
					// Fallback: save all configured providers
					if p, err := WriteMultiProviderConfigWithDefault(m.configuredProviders, m.defaultProviderID); err == nil {
						m.lastSaved = p
					} else {
						m.lastSaved = "(error)"
					}
				}
			}
			return m, nil
		case key.Matches(msg, m.keys.Delete):
			// Delete selected provider
			if m.page == PageConfigure && len(m.configuredProviders) > 0 {
				if m.selectedProviderIdx < len(m.configuredProviders) {
					// Remove provider from slice
					m.configuredProviders = append(
						m.configuredProviders[:m.selectedProviderIdx],
						m.configuredProviders[m.selectedProviderIdx+1:]...,
					)
					// Adjust selection index
					if m.selectedProviderIdx >= len(m.configuredProviders) && len(m.configuredProviders) > 0 {
						m.selectedProviderIdx = len(m.configuredProviders) - 1
					}
				}
			}
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
				if m.startMenuIndex > 0 {
					m.startMenuIndex--
				}
				return m, nil
			case PageReadme:
				var cmd tea.Cmd
				m.vp, cmd = m.vp.Update(msg)
				return m, cmd
			case PageConfigure:
				if m.showingTags {
					// Navigate tags dropdown
					if m.tagDropdownIndex > 0 {
						m.tagDropdownIndex--
					}
				} else if m.addingProvider {
					// Navigate provider type dropdown
					if m.typeDropdownIndex > 0 {
						m.typeDropdownIndex--
					}
				} else if len(m.configuredProviders) > 0 {
					// Navigate configured providers list
					if m.selectedProviderIdx > 0 {
						m.selectedProviderIdx--
					}
				}
			case PageSelectDefault:
				if len(m.configuredProviders) > 0 && m.selectedProviderIdx > 0 {
					m.selectedProviderIdx--
				}
			case PageRebuild:
				if m.rebuildIx > 0 {
					m.rebuildIx--
				}
			case PageModelBrowser:
				if m.modelIndex > 0 {
					m.modelIndex--
				}
			}
			return m, nil
		case key.Matches(msg, m.keys.Down):
			switch m.page {
			case PageWelcome:
				if m.startMenuIndex < len(m.startMenuItems)-1 {
					m.startMenuIndex++
				}
				return m, nil
			case PageReadme:
				var cmd tea.Cmd
				m.vp, cmd = m.vp.Update(msg)
				return m, cmd
			case PageConfigure:
				if m.showingTags {
					// Navigate tags dropdown
					if m.tagDropdownIndex < len(m.availableTags)-1 {
						m.tagDropdownIndex++
					}
				} else if m.addingProvider {
					// Navigate provider type dropdown
					if m.typeDropdownIndex < len(m.availableTypes)-1 {
						m.typeDropdownIndex++
					}
				} else if len(m.configuredProviders) > 0 {
					// Navigate configured providers list
					if m.selectedProviderIdx < len(m.configuredProviders)-1 {
						m.selectedProviderIdx++
					}
				}
			case PageSelectDefault:
				if len(m.configuredProviders) > 0 && m.selectedProviderIdx < len(m.configuredProviders)-1 {
					m.selectedProviderIdx++
				}
			case PageRebuild:
				if m.rebuildIx < 1 { // two options
					m.rebuildIx++
				}
			case PageModelBrowser:
				if m.modelIndex < len(m.modelItems)-1 {
					m.modelIndex++
				}
			}
			return m, nil
		case key.Matches(msg, m.keys.Filter):
			// Toggle downloaded-only filter in model browser (local only)
			if m.page == PageModelBrowser && m.providerForModels == "local" {
				m.modelDownloadedOnly = !m.modelDownloadedOnly
				if len(m.modelAllItems) > 0 {
					if m.modelDownloadedOnly {
						filtered := make([]modelItem, 0, len(m.modelAllItems))
						for _, it := range m.modelAllItems {
							if it.Downloaded {
								filtered = append(filtered, it)
							}
						}
						m.modelItems = filtered
					} else {
						m.modelItems = m.modelAllItems
					}
					if m.modelIndex >= len(m.modelItems) {
						m.modelIndex = max(0, len(m.modelItems)-1)
					}
				}
				return m, nil
			}
			return m, nil
		case key.Matches(msg, m.keys.Tag):
			// Cycle tag filter for local provider
			if m.page == PageModelBrowser && m.providerForModels == "local" && len(m.modelAllItems) > 0 {
				// Build unique tag list from items
				uniq := map[string]struct{}{}
				order := []string{}
				for _, it := range m.modelAllItems {
					for _, t := range it.Tags {
						if _, ok := uniq[t]; !ok {
							uniq[t] = struct{}{}
							order = append(order, t)
						}
					}
				}
				if len(order) == 0 {
					return m, nil
				}
				// Advance tag index
				m.modelTagIndex = (m.modelTagIndex + 1) % (len(order) + 1) // include "no filter" state
				if m.modelTagIndex == 0 {
					m.modelTagFilter = ""
					m.modelStatus = ""
					// Apply filters
					base := m.modelAllItems
					if m.modelDownloadedOnly {
						tmp := make([]modelItem, 0, len(base))
						for _, it := range base {
							if it.Downloaded {
								tmp = append(tmp, it)
							}
						}
						base = tmp
					}
					m.modelItems = base
				} else {
					m.modelTagFilter = order[m.modelTagIndex-1]
					m.modelStatus = "Filter: tag=" + m.modelTagFilter
					// Apply filters
					base := m.modelAllItems
					if m.modelDownloadedOnly {
						tmp := make([]modelItem, 0, len(base))
						for _, it := range base {
							if it.Downloaded {
								tmp = append(tmp, it)
							}
						}
						base = tmp
					}
					filtered := make([]modelItem, 0, len(base))
					for _, it := range base {
						for _, t := range it.Tags {
							if t == m.modelTagFilter {
								filtered = append(filtered, it)
								break
							}
						}
					}
					m.modelItems = filtered
				}
				if m.modelIndex >= len(m.modelItems) {
					m.modelIndex = max(0, len(m.modelItems)-1)
				}
				return m, nil
			}
			return m, nil
		case key.Matches(msg, m.keys.Info):
			if m.page == PageModelBrowser && len(m.modelItems) > 0 {
				it := m.modelItems[m.modelIndex]
				m.modelStatus = fmt.Sprintf("%s | id=%s | size=%s | %dMB | RAM=%.1fGB | ctx=%d | tags=%s", it.Name, it.ID, it.Size, it.FileSizeMB, it.RecommendedRAMGB, it.ContextWindow, strings.Join(it.Tags, ","))
				return m, nil
			}
			return m, nil
		case key.Matches(msg, m.keys.Tab):
			// Tab navigation between fields on Configure page
			if m.page == PageConfigure && m.editingField == "" {
				if m.editingProvider && m.tempProvider != nil {
					// Navigate between fields in editing mode
					fields := GetConfigurableFields(m.tempProvider.Type)
					if len(fields) > 0 {
						m.fieldIndex = (m.fieldIndex + 1) % len(fields)
					}
				}
			}
			return m, nil

		case key.Matches(msg, m.keys.Enter):
			switch m.page {
			case PageWelcome:
				if len(m.startMenuItems) > 0 {
					sel := m.startMenuItems[m.startMenuIndex]
					m.page = sel.Page
				}
				return m, nil
			case PageConfigure:
				if m.showingTags {
					// Toggle tag selection
					if m.tagDropdownIndex < len(m.availableTags) {
						selectedTag := m.availableTags[m.tagDropdownIndex]

						// Check if tag is already selected
						tagExists := false
						for i, tag := range m.selectedTags {
							if tag == selectedTag {
								// Remove tag
								m.selectedTags = append(m.selectedTags[:i], m.selectedTags[i+1:]...)
								tagExists = true
								break
							}
						}

						if !tagExists {
							// Add tag
							m.selectedTags = append(m.selectedTags, selectedTag)
						}
					}
					return m, nil
				} else if m.editingField != "" {
					// Save the field being edited and exit edit mode
					m.updateCurrentProviderFromFields()
					// Blur the appropriate input
					switch m.editingField {
					case "host":
						m.hostInput.Blur()
					case "port":
						m.portInput.Blur()
					case "api_key":
						m.apiKeyInput.Blur()
					case "base_url":
						m.baseURLInput.Blur()
					case "org_id":
						m.orgIDInput.Blur()
					case "name":
						m.nameInput.Blur()
					}
					m.editingField = "" // Exit edit mode
					return m, nil
				}

				// Start editing a field in provider editing mode
				if m.editingProvider && m.tempProvider != nil && m.editingField == "" {
					fields := GetConfigurableFields(m.tempProvider.Type)
					if m.fieldIndex < len(fields) {
						selectedField := fields[m.fieldIndex]

						// Handle model field specially - open model browser
						if selectedField == "model" {
							// Allow model browsing for local, lmstudio, and ollama
							if m.tempProvider.Type == "local" || m.tempProvider.Type == "lmstudio" || m.tempProvider.Type == "ollama" {
								m.providerForModels = m.tempProvider.Type
								m.modelItems = nil
								m.modelIndex = 0
								m.modelStatus = "Loading models…"
								m.page = PageModelBrowser
								return m, fetchModelsCmd(m.tempProvider.Type)
							}
						} else if selectedField == "tags" {
							// Handle tags field - toggle tag selection mode
							m.showingTags = true
							m.tagDropdownIndex = 0
						} else if selectedField == "host" || selectedField == "port" || selectedField == "api_key" ||
							selectedField == "base_url" || selectedField == "org_id" || selectedField == "name" {
							// Handle text input fields
							m.editingField = selectedField

							// Focus the appropriate input
							switch selectedField {
							case "host":
								m.hostInput.Focus()
							case "port":
								m.portInput.Focus()
							case "api_key":
								m.apiKeyInput.Focus()
							case "base_url":
								m.baseURLInput.Focus()
							case "org_id":
								m.orgIDInput.Focus()
							case "name":
								m.nameInput.Focus()
							}
						}
					}
					return m, nil
				}

				// New multi-provider Enter logic
				if m.addingProvider {
					// Complete adding provider - create new provider and start editing
					if m.typeDropdownIndex < len(m.availableTypes) {
						provType := m.availableTypes[m.typeDropdownIndex]
						newProvider := ConfiguredProvider{
							ID:     GenerateProviderID(provType, ""),
							Name:   provType + " provider",
							Type:   provType,
							Tags:   []string{},
							Config: GetDefaultConfig(provType),
						}

						// Start editing this new provider
						m.tempProvider = &newProvider
						m.editingProvider = true
						m.editingProviderIndex = -1 // -1 indicates new provider
						m.addingProvider = false

						// Populate input fields with default config
						m.populateInputsFromProvider(&newProvider)
					}
					return m, nil
				}

				// Edit existing provider
				if len(m.configuredProviders) > 0 && m.selectedProviderIdx < len(m.configuredProviders) {
					selectedProvider := m.configuredProviders[m.selectedProviderIdx]

					// Create a copy for editing
					tempProvider := selectedProvider
					m.tempProvider = &tempProvider
					m.editingProvider = true
					m.editingProviderIndex = m.selectedProviderIdx

					// Populate input fields with current config
					m.populateInputsFromProvider(&selectedProvider)
				}
				return m, nil
			case PageModelBrowser:
				if len(m.modelItems) > 0 {
					// Update the model in the temp provider (if editing) or current provider
					selectedModel := m.modelItems[m.modelIndex].ID
					if m.editingProvider && m.tempProvider != nil {
						// Update model in temp provider being edited
						m.tempProvider.Config.Model = selectedModel
					} else {
						// Fallback: update current provider model (old behavior)
						m.providerModel = selectedModel
					}
				}
				m.page = PageConfigure
				return m, nil
			case PageSelectDefault:
				// Set selected provider as default
				if len(m.configuredProviders) > 0 && m.selectedProviderIdx < len(m.configuredProviders) {
					m.defaultProviderID = m.configuredProviders[m.selectedProviderIdx].ID
					providerName := m.configuredProviders[m.selectedProviderIdx].Name
					if providerName == "" {
						providerName = m.configuredProviders[m.selectedProviderIdx].Type
					}

					// Persist to config file
					if _, err := WriteMultiProviderConfigWithDefault(m.configuredProviders, m.defaultProviderID); err == nil {
						m.lastSaved = "Default provider set: " + providerName
						m = m.showSaveSuccessBanner("⭐ Default provider set: " + providerName)
						return m, hideSaveBannerAfterDelay()
					} else {
						m.lastSaved = "(error saving default provider)"
						m = m.showSaveSuccessBanner("❌ Error setting default provider")
						return m, hideSaveBannerAfterDelay()
					}
				}
				return m, nil
			case PageRebuild:
				// Find the default provider to save
				var defaultProvider *ConfiguredProvider
				if m.defaultProviderID != "" {
					for _, p := range m.configuredProviders {
						if p.ID == m.defaultProviderID {
							defaultProvider = &p
							break
						}
					}
				}

				// Fallback to first configured provider if no default set
				if defaultProvider == nil && len(m.configuredProviders) > 0 {
					defaultProvider = &m.configuredProviders[0]
				}

				if defaultProvider == nil {
					m.lastSaved = "(no configured providers to save)"
				} else if m.rebuildIx == 0 {
					// Save to local directory (.chi_llm.json)
					if p, err := WriteProjectConfigFull(defaultProvider.Config); err == nil {
						m.lastSaved = p + " (local project config)"
						m = m.showSaveSuccessBanner("✅ Saved " + p)
						// Don't quit - go back to welcome page instead
						m.page = PageWelcome
						m = m.ensureWelcomeViewportSize()
						return m, hideSaveBannerAfterDelay()
					} else {
						m.lastSaved = "(error writing to current directory)"
						m = m.showSaveSuccessBanner("❌ Error saving config")
						// Don't quit - go back to welcome page instead
						m.page = PageWelcome
						m = m.ensureWelcomeViewportSize()
						return m, hideSaveBannerAfterDelay()
					}
				} else {
					// Save to global config (~/.cache/chi_llm/model_config.json)
					// For now, just write to current directory with note about global
					if p, err := WriteProjectConfigFull(defaultProvider.Config); err == nil {
						m.lastSaved = p + " (note: should be global config)"
						m = m.showSaveSuccessBanner("✅ Saved " + p + " (global)")
						// Don't quit - go back to welcome page instead
						m.page = PageWelcome
						m = m.ensureWelcomeViewportSize()
						return m, hideSaveBannerAfterDelay()
					} else {
						m.lastSaved = "(error writing config file)"
						m = m.showSaveSuccessBanner("❌ Error saving config")
						// Don't quit - go back to welcome page instead
						m.page = PageWelcome
						m = m.ensureWelcomeViewportSize()
						return m, hideSaveBannerAfterDelay()
					}
				}
			default:
				// default behavior: quit with current selection
				if len(m.providers) > 0 {
					m.choice = m.providers[m.index]
				}
				m.quitting = true
				return m, tea.Quit
			}
		default:
			// If we're on a viewport page and the key wasn't handled above, let the viewport process it
			if m.page == PageReadme {
				var cmd tea.Cmd
				m.vp, cmd = m.vp.Update(msg)
				return m, cmd
			}
		}
	case hideBannerMsg:
		m.showSaveBanner = false
		return m, nil
	case tickMsg:
		if m.anim.Enabled {
			m.anim.Next()
			return m, m.anim.Tick()
		}
	case spinner.TickMsg:
		var cmd tea.Cmd
		m.spin, cmd = m.spin.Update(msg)
		return m, cmd
	case resumeAnimMsg:
		if !m.anim.Enabled {
			m.anim.Enabled = true
			return m, m.anim.Tick()
		}
		return m, nil
	case modelListMsg:
		if msg.Err != "" {
			m.modelStatus = msg.Err
			m.modelItems = nil
		} else {
			m.modelStatus = ""
			// Keep a full copy to support filters
			m.modelAllItems = msg.Items
			if msg.AvailableRAMGB > 0 {
				m.availableRAMGB = msg.AvailableRAMGB
			}
			if m.providerForModels == "local" && m.modelDownloadedOnly {
				// Filter downloaded-only
				filtered := make([]modelItem, 0, len(msg.Items))
				for _, it := range msg.Items {
					if it.Downloaded {
						filtered = append(filtered, it)
					}
				}
				m.modelItems = filtered
			} else {
				m.modelItems = msg.Items
			}
			if m.modelIndex >= len(m.modelItems) {
				m.modelIndex = max(0, len(m.modelItems)-1)
			}
		}
		return m, nil
	case tea.MouseWheelMsg:
		if m.page == PageWelcome {
			// Navigate menu with wheel
			mbtn := msg.Mouse().Button
			if mbtn == tea.MouseWheelDown {
				if m.startMenuIndex < len(m.startMenuItems)-1 {
					m.startMenuIndex++
				}
			} else if mbtn == tea.MouseWheelUp {
				if m.startMenuIndex > 0 {
					m.startMenuIndex--
				}
			}
			return m, nil
		} else if m.page == PageReadme {
			var cmd tea.Cmd
			m.vp, cmd = m.vp.Update(msg)
			return m, cmd
		}
		mbtn := msg.Mouse().Button
		switch mbtn {
		case tea.MouseWheelDown:
			if m.page == PageModelBrowser {
				if m.modelIndex < len(m.modelItems)-1 {
					m.modelIndex++
				}
			} else if m.index < len(m.providers)-1 {
				m.index++
			}
			return m, nil
		case tea.MouseWheelUp:
			if m.page == PageModelBrowser {
				if m.modelIndex > 0 {
					m.modelIndex--
				}
			} else if m.index > 0 {
				m.index--
			}
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

	// Selected Provider section at the top (skip on Configure page)
	if m.page != PageConfigure {
		lines = append(lines, m.styles.Subtitle.Render("Selected Provider"))

		// Check if current differs from saved
		// TODO: Implement change detection for multi-provider
		hasChanges := false

		providerText := "None"
		if m.defaultProviderID != "" {
			// Find default provider by ID
			for _, provider := range m.configuredProviders {
				if provider.ID == m.defaultProviderID {
					providerText = provider.Name
					if providerText == "" {
						providerText = provider.Type
					}
					break
				}
			}
		}

		if hasChanges {
			// Show orange with asterisk when modified
			orangeStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#FFA500"))
			providerText = "* " + providerText
			lines = append(lines, orangeStyle.Render("  "+providerText))
		} else {
			lines = append(lines, m.styles.Normal.Render("  "+providerText))
		}
		lines = append(lines, strings.Repeat("─", min(width, 30)))
		lines = append(lines, "") // spacer
	}

	// Menu title
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
		{"ESC", "Main Menu", PageWelcome},
		{"1", "README.md", PageReadme},
		{"2", "Configure Providers", PageConfigure},
		{"3", "Select Default", PageSelectDefault},
		{"4", "Diagnostics", PageDiagnostics},
	}

	for _, item := range menuItems {
		style := m.styles.Normal
		prefix := "  "

		// Highlight current page
		if item.page == m.page {
			style = m.styles.Selected
			// Use ASCII pointer to avoid ambiguous glyph width
			prefix = "> "
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
		{"s", "Settings", "Configure settings"},
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

	// Apply a max-width container to avoid stretching on very wide terminals
	const contentMaxWidth = 110
	viewW := innerW
	if viewW > contentMaxWidth {
		viewW = contentMaxWidth
	}
	// Horizontal offset to center the container
	offsetX := max(0, (innerW-viewW)/2)

	// Sections
	// Grid split into top/bottom lines
	gtop, gbottom := "", ""
	if g := m.anim.RenderGrid(viewW); g != "" {
		parts := strings.SplitN(g, "\n", 2)
		gtop = parts[0]
		if len(parts) > 1 {
			gbottom = parts[1]
		}
	}
	// Compact hero: scale=1 (no extra vertical margin)
	hero := m.anim.RenderHero(viewW, 1)
	heroLines := 0
	if hero != "" {
		heroLines = len(strings.Split(hero, "\n"))
	}
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
			items[i] = padANSI(style.Render(pointer+p), viewW)
		}
	}

	// Theme status indicator only
	themeLbl := padANSI(m.styles.Help.Render(fmt.Sprintf("anim: %v", m.anim.Enabled)), viewW)

	// Build content lines
	var lines []string
	// Count actual header lines as we build them
	actualHeaderLines := 0

	// Place top grid line above hero (if present)
	if gtop != "" {
		lines = append(lines, gtop)
		actualHeaderLines++
	}
	if hero != "" {
		heroSplit := strings.Split(hero, "\n")
		lines = append(lines, heroSplit...)
		actualHeaderLines += len(heroSplit)
	}
	// Place bottom grid line directly under hero
	if gbottom != "" {
		lines = append(lines, gbottom)
		actualHeaderLines++
	}
	// One spacer line under the animation before content
	lines = append(lines, strings.Repeat(" ", viewW))
	actualHeaderLines++

	// Use a fixed header count to avoid jitter from +/-1 oscillations
	// caused by animation reflows. The actualHeaderLines built above
	// should equal welcomeHeaderLines, but we intentionally lock to a
	// constant for stability.
	headerLines := welcomeHeaderLines

	switch m.page {
	case PageWelcome:
		bodyHeight := max(3, innerH-headerLines-1) // leave line for theme status only

		// Fill body with blank lines; the start menu is rendered as an overlay
		for i := 0; i < bodyHeight; i++ {
			lines = append(lines, "")
		}
		// Status line
		status := "↑/↓ select  •  Enter: open  •  q: quit"
		lines = append(lines, padANSI(m.styles.Help.Render(status), viewW))
	case PageReadme:
		// Render viewport content (README)
		lines = append(lines, strings.Split(m.vp.View(), "\n")...)
		// Status line
		status := "arrows/pgup/pgdn: scroll  •  ESC: back"
		lines = append(lines, padANSI(m.styles.Help.Render(status), viewW))
	case PageConfigure:
		bodyHeight := max(3, innerH-headerLines-1) // leave line for theme status only

		// Calculate menu and content widths (narrower ~23% of inner width)
		menuWidth := 0
		if m.showTOC {
			menuWidth = innerW * 7 / 30
			if menuWidth < 20 {
				menuWidth = 20
			}
			if menuWidth > 45 {
				menuWidth = 45
			}
		}
		contentWidth := innerW - menuWidth
		if menuWidth > 0 {
			contentWidth -= 3 // Space for separator " │ "
		}

		// Build content based on current state
		var providerLines []string

		if m.editingProvider && m.tempProvider != nil {
			// Show provider editing form
			providerLines = append(providerLines, m.styles.Subtitle.Render("Edit Provider: "+m.tempProvider.Type))
			providerLines = append(providerLines, "")

			// Show configurable fields for this provider type
			fields := GetConfigurableFields(m.tempProvider.Type)

			for i, field := range fields {
				var label, value string
				var inputComponent string

				// Create field label and get current value
				switch field {
				case "name":
					label = "Name:"
					value = m.nameInput.Value()
					if m.editingField == field {
						inputComponent = m.nameInput.View()
					}
				case "host":
					label = "Host:"
					value = m.hostInput.Value()
					if m.editingField == field {
						inputComponent = m.hostInput.View()
					}
				case "port":
					label = "Port:"
					value = m.portInput.Value()
					if m.editingField == field {
						inputComponent = m.portInput.View()
					}
				case "api_key":
					label = "API Key:"
					value = strings.Repeat("*", len(m.apiKeyInput.Value()))
					if m.editingField == field {
						inputComponent = m.apiKeyInput.View()
					}
				case "base_url":
					label = "Base URL:"
					value = m.baseURLInput.Value()
					if m.editingField == field {
						inputComponent = m.baseURLInput.View()
					}
				case "org_id":
					label = "Org ID:"
					value = m.orgIDInput.Value()
					if m.editingField == field {
						inputComponent = m.orgIDInput.View()
					}
				case "model":
					label = "Model:"
					value = m.tempProvider.Config.Model
				case "tags":
					label = "Tags:"
					if len(m.selectedTags) > 0 {
						value = strings.Join(m.selectedTags, ", ")
					} else {
						value = "none"
					}
				}

				// Render field
				style := m.styles.Normal
				pointer := "  "
				if i == m.fieldIndex {
					style = m.styles.Selected
					pointer = "> "
				}

				if m.editingField == field && inputComponent != "" {
					// Show active text input
					providerLines = append(providerLines, style.Render(pointer+label))
					providerLines = append(providerLines, "    "+inputComponent)
				} else {
					// Show field with current value
					fieldDisplay := fmt.Sprintf("%s %s", label, value)
					providerLines = append(providerLines, style.Render(pointer+fieldDisplay))
				}
			}

			// Show tags dropdown if active
			if m.showingTags {
				providerLines = append(providerLines, "")
				providerLines = append(providerLines, m.styles.Subtitle.Render("Available Tags:"))
				providerLines = append(providerLines, m.styles.Help.Render("(Enter to toggle, ESC to close)"))
				for i, tag := range m.availableTags {
					style := m.styles.Normal
					pointer := "  "

					// Check if selected
					isSelected := false
					for _, selectedTag := range m.selectedTags {
						if selectedTag == tag {
							isSelected = true
							break
						}
					}

					if i == m.tagDropdownIndex {
						style = m.styles.Selected
						pointer = "> "
					}

					// Add checkmark for selected tags
					displayTag := tag
					if isSelected {
						displayTag = "✓ " + tag
					} else {
						displayTag = "  " + tag
					}

					providerLines = append(providerLines, style.Render(pointer+displayTag))
				}
			}

			// Show connection status if testing or test completed
			if m.isTestingConnection {
				providerLines = append(providerLines, "")
				providerLines = append(providerLines, m.styles.Help.Render("Testing connection..."))
			} else if !m.connectionStatus.Success && m.connectionStatus.Message != "" {
				providerLines = append(providerLines, "")
				statusStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#FF4444"))
				providerLines = append(providerLines, statusStyle.Render("✗ "+m.connectionStatus.Message))
				if m.connectionStatus.Details != "" {
					providerLines = append(providerLines, m.styles.Help.Render("  "+m.connectionStatus.Details))
				}
			} else if m.connectionStatus.Success && m.connectionStatus.Message != "" {
				providerLines = append(providerLines, "")
				statusStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#44FF44"))
				providerLines = append(providerLines, statusStyle.Render("✓ "+m.connectionStatus.Message))
				if m.connectionStatus.Details != "" {
					providerLines = append(providerLines, m.styles.Help.Render("  "+m.connectionStatus.Details))
				}
				if m.connectionStatus.Latency > 0 {
					providerLines = append(providerLines, m.styles.Help.Render(fmt.Sprintf("  Latency: %v", m.connectionStatus.Latency)))
				}
			}

			// Actions for editing mode
			providerLines = append(providerLines, "")
			providerLines = append(providerLines, m.styles.Help.Render("Actions:"))
			providerLines = append(providerLines, m.styles.Help.Render("  [Tab] Next field"))
			providerLines = append(providerLines, m.styles.Help.Render("  [Enter] Edit field / Save field"))
			providerLines = append(providerLines, m.styles.Help.Render("  [S] Save provider"))
			providerLines = append(providerLines, m.styles.Help.Render("  [T] Test connection"))
			providerLines = append(providerLines, m.styles.Help.Render("  [ESC] Cancel"))

		} else {
			// Show providers list and add functionality
			providerLines = append(providerLines, m.styles.Subtitle.Render("Configured Providers"))
			providerLines = append(providerLines, "")

			if len(m.configuredProviders) == 0 {
				providerLines = append(providerLines, m.styles.Help.Render("No providers configured yet"))
				providerLines = append(providerLines, m.styles.Help.Render("Press 'A' to add a provider"))
			} else {
				for i, provider := range m.configuredProviders {
					style := m.styles.Normal
					pointer := "  "

					// Check if this provider has unsaved changes (being edited)
					isUnsaved := m.editingProvider && m.editingProviderIndex == i

					if i == m.selectedProviderIdx {
						style = m.styles.Selected
						pointer = "> "
					}

					// Display provider with tags
					displayName := provider.Name
					if displayName == "" {
						displayName = provider.Type
					}

					// Add unsaved indicator
					if isUnsaved {
						displayName = "* " + displayName
						// Use orange color for unsaved providers
						if i == m.selectedProviderIdx {
							// Keep selection style but make it orange
							orangeStyle := lipgloss.NewStyle().
								Foreground(lipgloss.Color("#FFA500")).
								Background(m.styles.Selected.GetBackground()).
								Bold(true)
							style = orangeStyle
						} else {
							orangeStyle := lipgloss.NewStyle().Foreground(lipgloss.Color("#FFA500"))
							style = orangeStyle
						}
					}

					if len(provider.Tags) > 0 {
						displayName += " (" + strings.Join(provider.Tags, ", ") + ")"
					}

					providerLines = append(providerLines, style.Render(pointer+displayName))
				}
			}

			// Add provider type dropdown section
			providerLines = append(providerLines, "")
			providerLines = append(providerLines, m.styles.Subtitle.Render("Add Provider"))

			if m.addingProvider {
				providerLines = append(providerLines, m.styles.Help.Render("Select provider type:"))
				for i, provType := range m.availableTypes {
					style := m.styles.Normal
					pointer := "  "
					if i == m.typeDropdownIndex {
						style = m.styles.Selected
						pointer = "> "
					}
					providerLines = append(providerLines, style.Render(pointer+provType))
				}
			} else {
				providerLines = append(providerLines, m.styles.Help.Render("Press 'A' to add a new provider"))
			}

			// Add actions hint
			providerLines = append(providerLines, "")
			providerLines = append(providerLines, m.styles.Help.Render("Actions:"))
			providerLines = append(providerLines, m.styles.Help.Render("  [A/a] Add provider"))
			providerLines = append(providerLines, m.styles.Help.Render("  [S] Save all"))
			providerLines = append(providerLines, m.styles.Help.Render("  [D] Delete provider"))
			providerLines = append(providerLines, m.styles.Help.Render("  [Enter] Edit provider"))
		}

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
			for i := 0; i < bodyHeight; i++ {
				menuLine := ""
				contentLine := ""

				if i < len(menuLines) {
					menuLine = menuLines[i]
				}
				if i < len(providerLines) {
					contentLine = providerLines[i]
				}

				// Pad to fixed widths - ensure consistent width
				menuLine = padANSI(menuLine, menuWidth)
				contentLine = padANSI(contentLine, contentWidth)

				// Combine with separator
				line := menuLine + " │ " + contentLine
				lines = append(lines, line)
			}
		} else {
			// No menu, just show provider content
			for _, line := range providerLines {
				lines = append(lines, padANSI(line, viewW))
			}
		}
	case PageSelectDefault:
		bodyHeight := max(3, innerH-headerLines-1) // leave line for theme status only

		// Calculate menu and content widths (narrower ~23% of inner width)
		menuWidth := 0
		if m.showTOC {
			menuWidth = innerW * 7 / 30
			if menuWidth < 20 {
				menuWidth = 20
			}
			if menuWidth > 45 {
				menuWidth = 45
			}
		}
		contentWidth := innerW - menuWidth
		if menuWidth > 0 {
			contentWidth -= 3 // Space for separator " │ "
		}

		// Build default provider selection content
		var defaultLines []string
		defaultLines = append(defaultLines, m.styles.Subtitle.Render("Select Default Provider"))
		defaultLines = append(defaultLines, "")

		if len(m.configuredProviders) == 0 {
			defaultLines = append(defaultLines, m.styles.Help.Render("No providers configured yet"))
			defaultLines = append(defaultLines, m.styles.Help.Render("Go to Configure Providers (2) first"))
		} else {
			defaultLines = append(defaultLines, m.styles.Help.Render("Choose your default provider:"))
			defaultLines = append(defaultLines, "")

			for i, provider := range m.configuredProviders {
				style := m.styles.Normal
				pointer := "  "

				// Check if this is the current default
				isDefault := provider.ID == m.defaultProviderID

				if i == m.selectedProviderIdx {
					style = m.styles.Selected
					pointer = "▸ "
				}

				// Display provider with status
				displayName := provider.Name
				if displayName == "" {
					displayName = provider.Type
				}

				if isDefault {
					displayName = "★ " + displayName + " (current default)"
				}

				if len(provider.Tags) > 0 {
					displayName += " (" + strings.Join(provider.Tags, ", ") + ")"
				}

				defaultLines = append(defaultLines, style.Render(pointer+displayName))
			}
		}

		// Actions
		defaultLines = append(defaultLines, "")
		defaultLines = append(defaultLines, m.styles.Help.Render("Actions:"))
		defaultLines = append(defaultLines, m.styles.Help.Render("  [Enter] Set as default provider"))
		defaultLines = append(defaultLines, m.styles.Help.Render("  [2] Configure Providers"))
		defaultLines = append(defaultLines, m.styles.Help.Render("  [ESC] Back to Welcome"))

		// Ensure content fits in available space
		for len(defaultLines) < bodyHeight {
			defaultLines = append(defaultLines, "")
		}

		// Build the display with menu panel
		if m.showTOC {
			menuLines := strings.Split(m.renderMenu(menuWidth, bodyHeight), "\n")

			// Ensure both have same number of lines
			for len(menuLines) < bodyHeight {
				menuLines = append(menuLines, "")
			}
			for len(defaultLines) < bodyHeight {
				defaultLines = append(defaultLines, "")
			}

			// Combine line by line with proper padding
			for i := 0; i < bodyHeight; i++ {
				menuLine := ""
				contentLine := ""

				if i < len(menuLines) {
					menuLine = menuLines[i]
				}
				if i < len(defaultLines) {
					contentLine = defaultLines[i]
				}

				// Pad to fixed widths - ensure consistent width
				menuLine = padANSI(menuLine, menuWidth)
				contentLine = padANSI(contentLine, contentWidth)

				// Combine with separator
				line := menuLine + " │ " + contentLine
				lines = append(lines, line)
			}
		} else {
			// No menu, just show default provider content
			for _, line := range defaultLines {
				lines = append(lines, padANSI(line, viewW))
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
			lines = append(lines, padANSI(style.Render(pointer+o), viewW))
		}
	case PageDiagnostics:
		lines = append(lines, padANSI(m.styles.Subtitle.Render("Diagnostics"), viewW))
		if m.diag.ConfigPath != "" {
			lines = append(lines, padANSI(m.styles.Normal.Render("config: ")+m.diag.ConfigPath, viewW))
		} else {
			lines = append(lines, padANSI(m.styles.Normal.Render("config: (none)"), viewW))
		}
		if m.diag.ProviderType != "" {
			lines = append(lines, padANSI(m.styles.Normal.Render("provider: ")+m.diag.ProviderType, viewW))
		}
		if m.diag.ProviderModel != "" {
			lines = append(lines, padANSI(m.styles.Normal.Render("model: ")+m.diag.ProviderModel, viewW))
		}
		if len(m.diag.Env) > 0 {
			lines = append(lines, padANSI(m.styles.Subtitle.Render("env"), viewW))
			for k, v := range m.diag.Env {
				lines = append(lines, padANSI(m.styles.Help.Render(k+": ")+v, viewW))
			}
		}
		if len(m.diag.Hints) > 0 {
			lines = append(lines, padANSI(m.styles.Subtitle.Render("hints"), viewW))
			for _, h := range m.diag.Hints {
				lines = append(lines, padANSI(m.styles.Help.Render("- ")+h, viewW))
			}
		}
		if m.lastSaved != "" {
			lines = append(lines, padANSI(m.styles.Help.Render("saved: ")+m.lastSaved, viewW))
		} else {
			lines = append(lines, padANSI(m.styles.Help.Render("press 'e' to export"), viewW))
		}
	case PageModelBrowser:
		header := "Browse models for " + m.providerForModels
		if m.providerForModels == "local" && len(m.modelAllItems) > 0 {
			if m.modelDownloadedOnly {
				header += " (downloaded only)"
			}
		}
		lines = append(lines, padANSI(m.styles.Subtitle.Render(header), viewW))
		if m.modelStatus != "" {
			lines = append(lines, padANSI(m.styles.Help.Render(m.modelStatus), viewW))
		}
		if len(m.modelItems) == 0 && m.modelStatus == "" {
			lines = append(lines, padANSI(m.styles.Help.Render("No models"), viewW))
		}
		for i, it := range m.modelItems {
			style := m.styles.Normal
			pointer := "  "
			if i == m.modelIndex {
				style = m.styles.Selected
				pointer = m.styles.Highlight.Render("› ")
			}
			// Build rich label for local provider entries
			label := it.ID
			name := it.Name
			if name == "" {
				name = it.ID
			}
			status := ""
			if it.Current {
				status = " [CURRENT]"
			} else if it.Downloaded {
				status = " [Downloaded]"
			} else {
				// Highlight recommended models when not downloaded/current
				for _, t := range it.Tags {
					if t == "recommended" {
						status = " [Recommended]"
						break
					}
				}
			}
			if m.providerForModels == "local" {
				// Fitness indicator based on available RAM
				fit := ""
				if m.availableRAMGB > 0 && it.RecommendedRAMGB > 0 {
					if it.RecommendedRAMGB <= m.availableRAMGB*0.7 {
						fit = m.styles.Highlight.Render(" ●") // good
					} else if it.RecommendedRAMGB <= m.availableRAMGB {
						fit = m.styles.Help.Render(" ●") // tight
					} else {
						fit = m.styles.Help.Render(" !") // too big
					}
				}
				if it.Size != "" {
					label = fmt.Sprintf("%s (%s)%s%s", name, it.Size, status, fit)
				} else if it.FileSizeMB > 0 {
					label = fmt.Sprintf("%s  (%d MB)%s%s", name, it.FileSizeMB, status, fit)
				} else {
					label = name + status + fit
				}
			} else {
				// Remote providers
				if it.FileSizeMB > 0 {
					label = fmt.Sprintf("%s  (%d MB)", it.ID, it.FileSizeMB)
				} else {
					label = it.ID
				}
			}
			lines = append(lines, padANSI(style.Render(pointer+label), viewW))
			// Render extra metadata line for local provider
			if m.providerForModels == "local" {
				meta := []string{}
				if it.RecommendedRAMGB > 0 {
					meta = append(meta, fmt.Sprintf("RAM: %.1fGB", it.RecommendedRAMGB))
				}
				if it.ContextWindow > 0 {
					meta = append(meta, fmt.Sprintf("ctx: %d", it.ContextWindow))
				}
				if len(it.Tags) > 0 {
					// Show up to 3 tags
					tcount := 3
					if len(it.Tags) < tcount {
						tcount = len(it.Tags)
					}
					meta = append(meta, "tags: "+strings.Join(it.Tags[:tcount], ", "))
				}
				if len(meta) > 0 {
					lines = append(lines, padANSI(m.styles.Help.Render("    "+strings.Join(meta, "  |  ")), viewW))
				}
			}
		}
	case PageSettings:
		bodyHeight := max(3, innerH-headerLines-1) // leave line for theme status only

		// Calculate menu and content widths (narrower ~23% of inner width)
		menuWidth := 0
		if m.showTOC {
			menuWidth = innerW * 7 / 30
			if menuWidth < 20 {
				menuWidth = 20
			}
			if menuWidth > 45 {
				menuWidth = 45
			}
		}
		contentWidth := innerW - menuWidth
		if menuWidth > 0 {
			contentWidth -= 3 // Space for separator " │ "
		}

		// Build settings content
		var settingsLines []string
		settingsLines = append(settingsLines, m.styles.Subtitle.Render("Settings"))
		settingsLines = append(settingsLines, "")
		settingsLines = append(settingsLines, m.styles.Normal.Render("Work in progress..."))
		settingsLines = append(settingsLines, "")
		settingsLines = append(settingsLines, m.styles.Help.Render("This page will contain:"))
		settingsLines = append(settingsLines, m.styles.Help.Render("• Theme configuration"))
		settingsLines = append(settingsLines, m.styles.Help.Render("• Animation settings"))
		settingsLines = append(settingsLines, m.styles.Help.Render("• Default paths"))
		settingsLines = append(settingsLines, m.styles.Help.Render("• Cache management"))
		settingsLines = append(settingsLines, m.styles.Help.Render("• Advanced options"))

		// Ensure content fits in available space
		for len(settingsLines) < bodyHeight {
			settingsLines = append(settingsLines, "")
		}

		// Build the display with menu panel
		if m.showTOC {
			menuLines := strings.Split(m.renderMenu(menuWidth, bodyHeight), "\n")

			// Ensure both have same number of lines
			for len(menuLines) < bodyHeight {
				menuLines = append(menuLines, "")
			}
			for len(settingsLines) < bodyHeight {
				settingsLines = append(settingsLines, "")
			}

			// Combine line by line with proper padding
			for i := 0; i < bodyHeight; i++ {
				menuLine := ""
				contentLine := ""

				if i < len(menuLines) {
					menuLine = menuLines[i]
				}
				if i < len(settingsLines) {
					contentLine = settingsLines[i]
				}

				// Pad to fixed widths - ensure consistent width
				menuLine = padANSI(menuLine, menuWidth)
				contentLine = padANSI(contentLine, contentWidth)

				// Combine with separator
				line := menuLine + " │ " + contentLine
				lines = append(lines, line)
			}
		} else {
			// No menu, just show settings content
			for _, line := range settingsLines {
				lines = append(lines, padANSI(line, viewW))
			}
		}
	}
	// Removed legend (help) - it's already in Actions section
	lines = append(lines, strings.Repeat(" ", innerW), themeLbl)

	// Fill remaining height so frame renders full-screen (respect container width)
	need := innerH - len(lines)
	for i := 0; i < max(0, need); i++ {
		lines = append(lines, strings.Repeat(" ", viewW))
	}

	// Build header/body and compose using lipgloss v2 layers (centered container)

	header := strings.Join(lines[:headerLines], "\n")
	body := strings.Join(lines[headerLines:], "\n")

	layers := []*lipgloss.Layer{
		lipgloss.NewLayer(body).X(offsetX).Y(headerLines),
		lipgloss.NewLayer(header).X(offsetX).Y(0),
	}
	// Overlay title and subtitle inside hero region, aligned to the left
	if m.headerTitle() != "" {
		overlayLine := m.styles.Title.Render(m.headerTitle())
		overlayY := 0
		if gtop != "" {
			overlayY++
		}
		if heroLines > 0 {
			overlayY += heroLines / 2
		}
		layers = append(layers, lipgloss.NewLayer(overlayLine).X(offsetX).Y(overlayY))
		// subtitle directly under title
		if overlaySubtitle != "" {
			layers = append(layers, lipgloss.NewLayer(overlaySubtitle).X(offsetX).Y(overlayY+1))
		}
	}

	// Add save banner overlay if visible
	if m.showSaveBanner {
		bannerStyle := lipgloss.NewStyle().
			Background(lipgloss.Color("#00ff00")).
			Foreground(lipgloss.Color("#000000")).
			Bold(true).
			Padding(0, 2).
			Margin(0, 0, 1, 0)

		// Handle error vs success styling
		if strings.Contains(m.saveBannerMsg, "❌") {
			bannerStyle = bannerStyle.Background(lipgloss.Color("#ff4444"))
		}

		bannerText := bannerStyle.Render(m.saveBannerMsg)
		// Position banner at top center
		bannerX := max(0, (m.width-lipgloss.Width(bannerText))/2)
		layers = append(layers, lipgloss.NewLayer(bannerText).X(bannerX).Y(2))
	}

	// Overlay start menu for Welcome page (centered on body)
	if m.page == PageWelcome && len(m.startMenuItems) > 0 {
		// Build simple decorated menu block with a gradient header and border
		title := "Main Menu"
		itemLines := make([]string, 0, len(m.startMenuItems)*2)
		maxInner := lipgloss.Width(title)
		for i, it := range m.startMenuItems {
			prefix := "  "
			style := m.styles.Normal
			if i == m.startMenuIndex {
				prefix = "> "
				style = m.styles.Selected
			}
			line := style.Render(prefix + it.Label)
			if lipgloss.Width(line) > maxInner {
				maxInner = lipgloss.Width(line)
			}
			itemLines = append(itemLines, line)
			if it.Help != "" {
				help := m.styles.Help.Render("  - " + it.Help)
				if lipgloss.Width(help) > maxInner {
					maxInner = lipgloss.Width(help)
				}
				itemLines = append(itemLines, help)
			}
		}
		// Padding inside box
		innerPad := 2
		menuInnerW := maxInner
		boxInner := menuInnerW + innerPad*2
		// Build gradient header using ▀ blocks with purple->blue colors
		grad := []string{"#7C3AED", "#8B5CF6", "#3B82F6"}
		var headerGrad strings.Builder
		for i := 0; i < boxInner; i++ {
			// map position to gradient index
			gi := i * (len(grad) - 1) / max(1, boxInner-1)
			st := lipgloss.NewStyle().Foreground(lipgloss.Color(grad[gi]))
			headerGrad.WriteString(st.Render("▀"))
		}
		// Title line centered
		titleLine := padANSI(title, menuInnerW)
		titleLine = strings.Repeat(" ", innerPad) + m.styles.Subtitle.Render(titleLine) + strings.Repeat(" ", innerPad)
		// Build content lines with side borders
		side := lipgloss.NewStyle().Foreground(lipgloss.Color("#334155"))
		sideChar := "┃" // thicker vertical border
		content := make([]string, 0, len(itemLines)+3)
		// top gradient (with side bars to keep width consistent)
		content = append(content, side.Render(sideChar)+headerGrad.String()+side.Render(sideChar))
		// blank spacer under gradient
		content = append(content, side.Render(sideChar)+titleLine+side.Render(sideChar))
		// only one spacer to keep block slightly higher
		// content = append(content, side.Render("|") + strings.Repeat(" ", boxInner) + side.Render("|"))
		for _, ln := range itemLines {
			padded := strings.Repeat(" ", innerPad) + padANSI(ln, menuInnerW) + strings.Repeat(" ", innerPad)
			content = append(content, side.Render(sideChar)+padded+side.Render(sideChar))
		}
		// bottom gradient using ▄ (with side bars)
		var bottomGrad strings.Builder
		for i := 0; i < boxInner; i++ {
			gi := i * (len(grad) - 1) / max(1, boxInner-1)
			st := lipgloss.NewStyle().Foreground(lipgloss.Color(grad[gi]))
			bottomGrad.WriteString(st.Render("▄"))
		}
		// add bottom gradient line
		content = append(content, side.Render(sideChar)+bottomGrad.String()+side.Render(sideChar))

		menuBlock := strings.Join(content, "\n")
		// Center within body
		bodyHeight := max(3, innerH-welcomeHeaderLines-1)
		blockWidth := boxInner + 2 // side bars
		menuX := offsetX + max(0, (viewW-blockWidth)/2)
		// Vertical position: bias further upward (~1/6 of remaining space)
		menuY := welcomeHeaderLines + max(0, (bodyHeight-len(content))/6)
		layers = append(layers, lipgloss.NewLayer(menuBlock).X(menuX).Y(menuY))
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
		return "chi-llm • menu"
	case PageReadme:
		return "chi-llm • README.md"
	case PageConfigure:
		return "chi-llm • configure providers"
	case PageSelectDefault:
		return "chi-llm • select default provider"
	case PageRebuild:
		return "chi-llm • (re)build configuration"
	case PageDiagnostics:
		return "chi-llm • diagnostics"
	case PageModelBrowser:
		return "chi-llm • provider models"
	case PageSettings:
		return "chi-llm • settings"
	default:
		return "chi-llm"
	}
}

func (m Model) subtitle() string {
	switch m.page {
	case PageWelcome:
		return "Main menu"
	case PageReadme:
		return "Readme"
	case PageConfigure:
		return "Manage configured providers"
	case PageSelectDefault:
		return "Choose your main provider"
	case PageRebuild:
		return "Where to write configuration?"
	case PageDiagnostics:
		return "Provider status and environment"
	case PageModelBrowser:
		return "Pick a model for the provider"
	case PageSettings:
		return "Application settings"
	default:
		return ""
	}
}

// Page enumerates app sections
type Page int

const (
	PageWelcome Page = iota
	PageReadme
	PageConfigure
	PageSelectDefault
	PageDiagnostics
	PageRebuild
	PageModelBrowser
	PageSettings
	PageExit
)

// renderMarkdown renders markdown content with glamour
func renderMarkdown(content string, width int) string {
	renderer, err := glamour.NewTermRenderer(
		glamour.WithAutoStyle(),
		glamour.WithWordWrap(width),
	)
	if err != nil {
		// Fallback to plain text if glamour fails
		return content
	}

	rendered, err := renderer.Render(content)
	if err != nil {
		// Fallback to plain text if rendering fails
		return content
	}

	return rendered
}

// figletText renders ASCII art for a label using figlet4go with caching.
// (previous figletText removed; menu now uses a lightweight gradient frame)

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
				// Return raw markdown - will be rendered later with glamour
				return string(b)
			}
		}
		nd := filepath.Dir(dir)
		if nd == dir {
			break
		}
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
	// Fast path for empty strings
	if s == "" {
		return strings.Repeat(" ", width)
	}

	w := lipgloss.Width(s)
	if w >= width {
		return s
	}
	return s + strings.Repeat(" ", width-w)
}

// modelItem is a simple item to render in the model browser list.
type modelItem struct {
	ID               string
	Name             string
	Size             string
	FileSizeMB       int
	ContextWindow    int
	RecommendedRAMGB float64
	Tags             []string
	Downloaded       bool
	Current          bool
}

// modelListMsg carries async discovery results into the update loop.
type modelListMsg struct {
	Items          []modelItem
	Err            string
	AvailableRAMGB float64
}

// fetchModelsCmd asynchronously discovers models for a provider.
func fetchModelsCmd(provider string) tea.Cmd {
	return func() tea.Msg {
		if provider == "local" {
			// Use detailed catalog from chi-llm CLI
			details, err := discovery.CliLocalModelDetails()
			if err != nil {
				// Fallback to simple discovery
				infos, derr := discovery.Discover(provider, "", 0)
				if derr != nil {
					return modelListMsg{Err: derr.Error()}
				}
				items := make([]modelItem, 0, len(infos))
				for _, inf := range infos {
					items = append(items, modelItem{ID: inf.ID, FileSizeMB: int(inf.SizeMB())})
				}
				return modelListMsg{Items: items}
			}
			items := make([]modelItem, 0, len(details))
			for _, d := range details {
				items = append(items, modelItem{
					ID:               d.ID,
					Name:             d.Name,
					Size:             d.Size,
					FileSizeMB:       d.FileSizeMB,
					ContextWindow:    d.ContextWindow,
					RecommendedRAMGB: d.RecommendedRAMGB,
					Tags:             d.Tags,
					Downloaded:       d.Downloaded,
					Current:          d.Current,
				})
			}
			// Fetch available RAM for fitness indicators
			ram, _ := discovery.GetAvailableRAMGB()
			msg := modelListMsg{Items: items}
			msg.AvailableRAMGB = ram
			return msg
		}
		// Network providers discovery (LMStudio/Ollama)
		infos, err := discovery.Discover(provider, "", 0)
		if err != nil {
			return modelListMsg{Err: err.Error()}
		}
		items := make([]modelItem, 0, len(infos))
		for _, inf := range infos {
			items = append(items, modelItem{ID: inf.ID, FileSizeMB: int(inf.SizeMB())})
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
	// Fixed header height for stability
	headerLines := welcomeHeaderLines
	bodyHeight := max(3, innerH-headerLines-1) // reserve line for theme status only

	// Match content width calculation used in View() to prevent width thrash
	const contentMaxWidth = 110
	viewW := innerW
	if viewW > contentMaxWidth {
		viewW = contentMaxWidth
	}
	tocWidth := 0
	if m.showTOC && len(m.tocItems) > 0 {
		tocWidth = viewW * 7 / 30
		if tocWidth < 20 {
			tocWidth = 20
		}
		if tocWidth > 45 {
			tocWidth = 45
		}
	}
	contentWidth := viewW - tocWidth
	if tocWidth > 0 {
		contentWidth -= 3 // Space for separator " │ "
	}

	vpWidth := max(0, contentWidth)
	vpHeight := max(1, bodyHeight)
	if m.vp.Width() != vpWidth {
		m.vp.SetWidth(vpWidth)
	}
	if m.vp.Height() != vpHeight {
		m.vp.SetHeight(vpHeight)
	}
	// Cache TOC width for use in View to keep widths stable across frames
	m.welcomeTOCWidth = tocWidth
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
		if !b.Enabled() {
			continue
		}
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
		part := style.Render("["+keyLabel+"]") + " " + m.styles.Help.Render(h.Desc)
		parts = append(parts, part)
	}
	s := strings.Join(parts, "  ")
	if width > 0 {
		s = padANSI(s, width)
	}
	return s
}

// connectionTestMsg is sent when connection testing completes
type connectionTestMsg struct {
	status ConnectionStatus
}

// testConnectionCmd tests connection to a provider
func testConnectionCmd(config ProviderConfig) tea.Cmd {
	return func() tea.Msg {
		status := TestConnection(config)
		return connectionTestMsg{status: status}
	}
}

// getCurrentProvider returns the currently selected configured provider
func (m *Model) getCurrentProvider() *ConfiguredProvider {
	if len(m.configuredProviders) == 0 || m.selectedProviderIdx >= len(m.configuredProviders) {
		return nil
	}
	return &m.configuredProviders[m.selectedProviderIdx]
}

// updateCurrentProviderFromFields updates the current provider config from input fields
func (m *Model) updateCurrentProviderFromFields() {
	provider := m.getCurrentProvider()
	if provider == nil {
		return
	}

	provider.Config.Host = m.hostInput.Value()
	provider.Config.Port = m.portInput.Value()
	provider.Config.APIKey = m.apiKeyInput.Value()
	provider.Config.BaseURL = m.baseURLInput.Value()
	provider.Config.OrgID = m.orgIDInput.Value()
	provider.Name = m.nameInput.Value()
	provider.Tags = m.selectedTags
}

// populateInputsFromProvider populates input fields with data from a provider
func (m *Model) populateInputsFromProvider(provider *ConfiguredProvider) {
	m.hostInput.SetValue(provider.Config.Host)
	m.portInput.SetValue(provider.Config.Port)
	m.apiKeyInput.SetValue(provider.Config.APIKey)
	m.baseURLInput.SetValue(provider.Config.BaseURL)
	m.orgIDInput.SetValue(provider.Config.OrgID)
	m.nameInput.SetValue(provider.Name)
	m.selectedTags = append([]string{}, provider.Tags...) // Copy slice
}

// showSaveSuccessBanner shows a success banner with auto-hide after 2 seconds
func (m Model) showSaveSuccessBanner(msg string) Model {
	m.showSaveBanner = true
	m.saveBannerMsg = msg
	m.saveBannerAt = time.Now()
	return m
}

// hideSaveBannerAfterDelay returns a command to hide the banner after 2 seconds
func hideSaveBannerAfterDelay() tea.Cmd {
	return tea.Tick(2*time.Second, func(t time.Time) tea.Msg {
		return hideBannerMsg(t)
	})
}
