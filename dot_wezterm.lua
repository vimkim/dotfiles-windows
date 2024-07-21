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

config.font = wezterm.font("JetBrainsMono Nerd Font Mono")
config.font_size = 12.0

config.enable_tab_bar = false

config.window_background_opacity = 0.90
config.default_prog = { "wsl.exe", "--cd", "~" }

-- and finally, return the configuration to wezterm
return config
