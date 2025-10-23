-- Pull in the wezterm API
local wezterm = require("wezterm")

-- This will hold the configuration.
local config = wezterm.config_builder()

-- This is where you actually apply your config choices

-- For example, changing the color scheme:
config.color_scheme = "Catppuccin Frappe"

local mux = wezterm.mux

wezterm.on("gui-startup", function()
	local tab, pane, window = mux.spawn_window(cmd or {})
	window:gui_window():maximize()
end)
config.window_decorations = "RESIZE"
config.enable_tab_bar = true
config.hide_tab_bar_if_only_one_tab = true

config.wsl_domains = {
	{
		-- The name of this specific domain.  Must be unique amonst all types
		-- of domain in the configuration file.
		name = "WSL:Ubuntu-24.04",

		default_cwd = "~",
	},
}

-- config.font = wezterm.font("JetBrainsMonoNL Nerd Font Propo", { weight = "Bold" })
-- config.font = wezterm.font("NotoSansM Nerd Font Propo", { weight = "Bold" })
config.font = wezterm.font_with_fallback({
	{ family = "Maple Mono NF", weight = "Bold" },
	{ family = "NotoSansM Nerd Font Propo", weight = "Bold" },
	{ family = "D2CodingLigature Nerd Font Propo", weight = "Bold" },
})
config.font_size = 15.0

config.default_prog = { "wsl.exe", "--cd", "~" }

-- randomly select background images

-- Function to get a random file from the list
local function get_random_file(files)
	if #files == 0 then
		return nil
	end
	local index = math.random(1, #files)
	return files[index]
end

-- Get the list of files and select one randomly

-- C:\Users\dhkim\AppData\Local\Packages\Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy\LocalState\Assets
-- local bg_images_dir_path = wezterm.config_dir
-- .. "/AppData/Local/Packages/Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy/LocalState/Assets"
-- local files = wezterm.read_dir(bg_images_dir_path)
-- local random_file = get_random_file(files)

-- config.background = {
-- 	{
-- 		source = {
-- 			-- File = random_file,
-- 		},
-- 		-- Adjust brightness (lower value makes it dimmer)
-- 		hsb = {
-- 			-- brightness = 0.015, -- Adjust this value to make the background dim
-- 			brightness = 0.0, -- Adjust this value to make the background dim
-- 		},
-- 		-- width = "100%",
-- 		height = "100%",
-- 	},
-- }

-- config.background = {
-- 	-- first layer
-- 	{
-- 		-- Use an image as the background
-- 		-- source = {
-- 		-- File = xdg_config_home .. "/Pictures/arch-catppuccin-blurred.png", -- Provide the path to the image file
-- 		-- File = random_file,
-- 		-- },
--
-- 		repeat_x = "NoRepeat",
-- 		horizontal_align = "Center",
-- 		opacity = 1,
-- 	},
-- 	-- second layer
-- 	{
-- 		source = {
-- 			Color = "rgba(48, 52, 70, 0.95)",
-- 		},
-- 		opacity = 0.95,
-- 		height = "100%",
-- 		width = "100%",
-- 	},
-- }

-- config.window_background_opacity = 0.5
-- config.win32_system_backdrop = "Acrylic"

local launch_menu = {}

table.insert(launch_menu, {
	label = "PowerShell",
	args = { "powershell.exe", "-NoLogo" },
})
table.insert(launch_menu, {
	label = "Pwsh",
	args = { "pwsh-preview.exe", "-NoLogo" },
})
table.insert(launch_menu, {
	label = "Nushell",
	args = { "nu.exe" },
})

config.launch_menu = launch_menu

config.window_padding = {
	left = 10,
	right = 0,
	top = 0,
	bottom = 0,
}

-- and finally, return the configuration to wezterm
return config
