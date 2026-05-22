{ pkgs, ... }:

{
  # ── Kitty  (Tokyo Night colour scheme) ────────────────────────────────────

  programs.kitty = {
    enable = true;
    font   = { name = "JetBrainsMono Nerd Font"; size = 13; };
    settings = {
      background           = "#1a1b26";
      foreground           = "#c0caf5";
      selection_background = "#283457";
      selection_foreground = "#c0caf5";
      cursor               = "#c0caf5";
      cursor_text_color    = "#1a1b26";
      url_color            = "#73daca";

      color0  = "#15161e";  color8  = "#414868";
      color1  = "#f7768e";  color9  = "#f7768e";
      color2  = "#9ece6a";  color10 = "#9ece6a";
      color3  = "#e0af68";  color11 = "#e0af68";
      color4  = "#7aa2f7";  color12 = "#7aa2f7";
      color5  = "#bb9af7";  color13 = "#bb9af7";
      color6  = "#7dcfff";  color14 = "#7dcfff";
      color7  = "#a9b1d6";  color15 = "#c0caf5";

      background_opacity    = "0.95";
      window_padding_width  = 8;
      scrollback_lines      = 10000;
      enable_audio_bell     = false;
      copy_on_select        = "clipboard";
      strip_trailing_spaces = "smart";

      hide_window_decorations = "yes";
      tab_bar_style           = "powerline";
      tab_bar_min_tabs        = 2;
    };
  };

  # ── Alacritty ─────────────────────────────────────────────────────────────
  # programs.alacritty = {
  #   enable = true;
  #   # TODO: share ~/.config/alacritty/alacritty.toml to fill this in
  # };
}
