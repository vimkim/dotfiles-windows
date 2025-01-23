-- Pull in the wezterm API
local wezterm = require("wezterm")

-- This will hold the configuration.
local config = wezterm.config_builder()

-- This is where you actually apply your config choices

-- For example, changing the color scheme:
config.color_scheme = "Catppuccin Mocha"

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

-- config.font = wezterm.font("JetBrainsMonoNL Nerd Font Propo", { weight = "Bold" })
config.font = wezterm.font("NotoSansM Nerd Font Propo", { weight = "Bold" })
config.font_size = 15.0

config.enable_tab_bar = false

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
local bg_images_dir_path = wezterm.config_dir
	.. "/AppData/Local/Packages/Microsoft.Windows.ContentDeliveryManager_cw5n1h2txyewy/LocalState/Assets"
local files = wezterm.read_dir(bg_images_dir_path)
local random_file = get_random_file(files)

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
--
local launch_menu = {}

table.insert(launch_menu, {
	label = "PowerShell",
	args = { "powershell.exe", "-NoLogo" },
})
table.insert(launch_menu, {
	label = "Pwsh",
	args = { "pwsh-preview.exe", "-NoLogo" },
})

config.launch_menu = launch_menu

-- and finally, return the configuration to wezterm
return config
