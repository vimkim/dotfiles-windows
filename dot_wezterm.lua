local wezterm = require("wezterm")
local mux = wezterm.mux
local config = wezterm.config_builder()

config.color_scheme = "Catppuccin Frappe"
config.window_decorations = "RESIZE"
config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true

wezterm.on("gui-startup", function(cmd)
	local _, _, window = mux.spawn_window(cmd or {})
	window:gui_window():maximize()
end)

config.wsl_domains = {
	{
		name = "WSL:Ubuntu",
		distribution = "Ubuntu",
		default_cwd = "~",
	},
}

config.default_prog = { "wsl.exe", "--distribution", "Ubuntu", "--cd", "~" }

config.font = wezterm.font_with_fallback({
	{ family = "Maple Mono NF", weight = "Bold" },
	{ family = "NotoSansM Nerd Font Propo", weight = "Bold" },
	{ family = "D2CodingLigature Nerd Font Propo", weight = "Bold" },
})
config.font_size = 12.0
config.line_height = 0.9

config.window_background_opacity = 0.5
config.win32_system_backdrop = "Acrylic"

config.launch_menu = {
	{
		label = "Ubuntu",
		args = { "wsl.exe", "--distribution", "Ubuntu", "--cd", "~" },
	},
	{
		label = "PowerShell",
		args = { "pwsh.exe", "-NoLogo" },
	},
	{
		label = "Windows PowerShell",
		args = { "powershell.exe", "-NoLogo" },
	},
	{
		label = "Windows Nushell",
		args = { "nu.exe" },
	},
}

config.window_padding = {
	left = 10,
	right = 0,
	top = 0,
	bottom = 0,
}

return config
