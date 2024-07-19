-- wezterm.lua
local wezterm = require("wezterm")

local mux = wezterm.mux

wezterm.on("gui-startup", function()
  local tab, pane, window = mux.spawn_window(cmd or {})
  window:gui_window():maximize()
end)


return {

	enable_tab_bar = false,
	-- Set the default program to launch WSL
	default_prog = { "wsl.exe", "--cd", "~" },
	-- freetype_load_target = "HorizontalLcd",
	-- freetype_render_target = "HorizontalLcd",
	-- freetype_interpreter_version = 40,

	-- Optional: Set WSL distribution if you have multiple distributions
	-- default_prog = { 'wsl.exe', '--distribution', 'Ubuntu' },

	-- Customize the appearance if desired
	-- font = wezterm.font_with_fallback({
	-- 	"JetBrainsMono Nerd Font Mono",
	-- 	"FiraCode Nerd Font",
	-- 	"Noto Color Emoji",
	-- }),
	font = wezterm.font( "JetBrainsMono Nerd Font Mono", {weight = "Bold"} ),
	font_size = 12.0,

	-- Other configurations as needed
	color_scheme = "catppuccin-macchiato",
	window_background_opacity = 0.90,
}
