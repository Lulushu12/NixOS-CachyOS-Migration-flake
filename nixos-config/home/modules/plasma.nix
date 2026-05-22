{ ... }:

# Declarative KDE Plasma configuration via plasma-manager.
# plasma-manager is injected as a sharedModule in flake.nix.
#
# To fill in each TODO section, share the relevant config file:
#   cat ~/.config/kdeglobals
#   cat ~/.config/plasmarc
#   cat ~/.config/plasma-org.kde.plasma.desktop-appletsrc
#   cat ~/.config/kwinrc
#   cat ~/.config/kglobalshortcutsrc
#   cat ~/.config/kscreenlockerrc
#   cat ~/.config/powerdevilrc

{
  programs.plasma = {

    # ── Kvantum theme selection ────────────────────────────────────────────
    # Active theme: Edna (files live in dotfiles/themes/kvantum/ — see desktop.nix)
    configFile."Kvantum/kvantum.kvconfig"."General"."theme" = "Edna";

    # ── Workspace appearance ───────────────────────────────────────────────
    # workspace = {
    #   colorScheme = "";   # TODO: check [General] ColorScheme in kdeglobals
    #   iconTheme   = "";   # TODO: check [Icons] Theme in kdeglobals
    #   lookAndFeel = "";   # TODO: check [KDE] LookAndFeelPackage in kdeglobals
    #   cursor = {
    #     theme = "";       # TODO: check [Mouse] cursorTheme in kcminputrc
    #     size  = 24;
    #   };
    #   wallpaper = "";     # TODO: absolute path or nix store path
    # };

    # ── Panels & widgets ──────────────────────────────────────────────────
    # TODO: share ~/.config/plasma-org.kde.plasma.desktop-appletsrc
    # Example structure once you have the file:
    # panels = [
    #   {
    #     location = "bottom";
    #     height   = 44;
    #     widgets  = [ "org.kde.plasma.kickoff" "org.kde.plasma.taskmanager" ... ];
    #   }
    # ];

    # ── Global keyboard shortcuts ─────────────────────────────────────────
    # TODO: share ~/.config/kglobalshortcutsrc
    # shortcuts = {
    #   "kwin"."Switch to Desktop 1" = "Meta+1";
    #   ...
    # };

    # ── KWin (compositor / window manager) ───────────────────────────────
    # TODO: share ~/.config/kwinrc
    # kwin = {
    #   effects.blur.enable          = true;
    #   effects.desktopSwitching.animation = "slide";
    #   virtualDesktops.number       = 4;
    #   virtualDesktops.rows         = 1;
    # };

    # ── Screen locker ─────────────────────────────────────────────────────
    # TODO: share ~/.config/kscreenlockerrc
    # configFile."kscreenlockerrc"."Daemon"."Autolock"   = true;
    # configFile."kscreenlockerrc"."Daemon"."Timeout"    = 5;

    # ── Power management ──────────────────────────────────────────────────
    # TODO: share ~/.config/powerdevilrc
    # configFile."powerdevilrc"."AC"."idleTime" = 600000;

    # ── Session restore ───────────────────────────────────────────────────
    # Disable session restore to prevent KDE from drifting the plasma config
    # back between home-manager activations.
    # configFile."ksmserverrc"."General"."loginMode" = "emptySession";

    # ── Arbitrary KDE config files ────────────────────────────────────────
    # Use this escape hatch for any KDE app setting not covered above.
    # Format: configFile."<filename>"."<group>"."<key>" = value;
    # Example (Dolphin):
    # configFile."dolphinrc"."General"."RememberOpenedTabs" = false;
  };
}
