-- Pull in the wezterm API
local wezterm = require("wezterm")

-- This will hold the configuration.
local config = wezterm.config_builder()

-- This is where you actually apply your config choices

-- For example, changing the color scheme:
config.color_scheme = "catppuccin-macchiato"

local mux = wezterm.mux

wezterm.on("gui-startup", function()
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)

config.wsl_domains = {
	{
		-- The name of this specific domain.  Must be unique amonst all types
		-- of domain in the configuration file.
		name = "WSL:Ubuntu-22.04",

		default_cwd = "~",
	},
}

config.font = wezterm.font("JetBrainsMono Nerd Font Propo", {weight = "Bold"})
config.font_size = 15.0

config.enable_tab_bar = false

config.default_prog = { "wsl.exe", "--cd", "~" }

config.background = {
    {
      source = {
        File = wezterm.config_dir .. '/yosemite.jpg'
      },
      -- Adjust brightness (lower value makes it dimmer)
      hsb = {
        brightness = 0.03, -- Adjust this value to make the background dim
      },
    },
}

local launch_menu = {}

table.insert(launch_menu, {
  label = 'PowerShell',
  args = { 'powershell.exe', '-NoLogo' },
})
table.insert(launch_menu, {
  label = 'Pwsh',
  args = { 'pwsh-preview.exe', '-NoLogo' },
})

config.launch_menu = launch_menu

-- and finally, return the configuration to wezterm
return config
