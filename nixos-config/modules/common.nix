# Common system settings: locale, timezone, fonts, and audio.
# These apply to all users and are independent of the desktop choice.

{ pkgs, ... }:

{
  # ── Timezone & locale ────────────────────────────────────────────────────────
  time.timeZone = "Europe/Bucharest";

  i18n.defaultLocale = "en_US.UTF-8";

  # Romanian formats for dates, numbers, currency — keeps the UI in English
  # while respecting local conventions. Remove if you prefer everything in en_US.
  i18n.extraLocaleSettings = {
    LC_ADDRESS        = "ro_RO.UTF-8";
    LC_IDENTIFICATION = "ro_RO.UTF-8";
    LC_MEASUREMENT    = "ro_RO.UTF-8";
    LC_MONETARY       = "ro_RO.UTF-8";
    LC_NAME           = "ro_RO.UTF-8";
    LC_NUMERIC        = "ro_RO.UTF-8";
    LC_PAPER          = "ro_RO.UTF-8";
    LC_TELEPHONE      = "ro_RO.UTF-8";
    LC_TIME           = "ro_RO.UTF-8";
  };

  # Keyboard layout for the virtual console (TTY, before the GUI loads).
  console.keyMap = "us";

  # ── Fonts ────────────────────────────────────────────────────────────────────
  # NixOS ships with no fonts by default — everything here is intentional.
  fonts = {
    enableDefaultPackages = true;

    packages = with pkgs; [
      # ── Unicode / language coverage ────────────────────────────────────────
      noto-fonts              # Broad Latin/Greek/Cyrillic/etc. coverage
      noto-fonts-cjk-sans     # Chinese, Japanese, Korean (sans-serif)
      noto-fonts-cjk-serif    # Chinese, Japanese, Korean (serif)
      noto-fonts-color-emoji  # Colour emoji (renders in browsers, terminal, apps)

      # ── Modern UI fonts ────────────────────────────────────────────────────
      inter                   # Clean, widely used sans-serif UI font
      roboto                  # Google's UI font — common on Android / web

      # ── Microsoft core fonts (needed for .docx / .xlsx compatibility) ──────
      # Requires allowUnfree = true (set in hosts/nixos/default.nix).
      # Provides: Arial, Times New Roman, Courier New, Verdana, Georgia, etc.
      corefonts

      # ── Nerd Fonts: patched fonts with developer icons ─────────────────────
      # Used by Kitty, terminal prompts, file managers, etc.
      # Individual packages required since nixpkgs 25.05 (nerdfonts.override removed).
      nerd-fonts.jetbrains-mono
      nerd-fonts.fira-code
      nerd-fonts.ubuntu-mono
      nerd-fonts.hack

      # ── Additional fonts (migrated from CachyOS) ───────────────────────────
      cantarell-fonts   # GNOME default sans-serif (used by some GTK apps)
      liberation_ttf    # Metric-compatible replacements for Arial/Times/Courier
      dejavu_fonts      # Extended Unicode coverage family
      font-awesome      # Icon font (web apps, some status bars)
      fira              # Fira Sans + Fira Mono (Mozilla's UI font)
      hack-font         # Monospace font for source code
    ];

    fontconfig.defaultFonts = {
      serif      = [ "Noto Serif" ];
      sansSerif  = [ "Inter" "Noto Sans" ];
      monospace  = [ "JetBrainsMono Nerd Font" "FiraCode Nerd Font" ];
      emoji      = [ "Noto Color Emoji" ];
    };
  };

  # ── Audio: PipeWire + JACK ────────────────────────────────────────────────────
  # PipeWire is the modern Linux audio server. It replaces both PulseAudio and
  # JACK, and transparently supports both APIs so all apps work out of the box.
  #
  # With jack.enable = true, pro audio apps (DAWs, audio editors) can connect
  # directly for low-latency operation. PipeWire acts as a JACK server.
  #
  # For the lowest latency (DAW work), consider also setting:
  #   services.pipewire.extraConfig.pipewire."92-low-latency" = {
  #     context.properties."default.clock.rate" = 48000;
  #     context.properties."default.clock.quantum" = 64;
  #   };
  services.pipewire = {
    enable            = true;
    alsa.enable       = true;
    alsa.support32Bit = true;   # 32-bit ALSA — needed for some games and old apps
    pulse.enable      = true;   # PulseAudio compatibility (most apps use this)
    jack.enable       = true;   # JACK compatibility for pro audio (DAWs, etc.)
  };

  # WirePlumber is the default session manager for PipeWire (routes streams
  # between sources and sinks). It replaces the older pipewire-media-session.
  services.pipewire.wireplumber.enable = true;

  # PulseAudio must be disabled — PipeWire's pulse layer replaces it.
  services.pulseaudio.enable = false;

  # RTKit grants PipeWire real-time scheduling priority.
  # This reduces audio glitches under load (gaming, heavy CPU tasks, etc.).
  security.rtkit.enable = true;

  # PAM limits for the audio group — needed for reliable low-latency audio.
  # Pro audio apps need to lock memory and run at real-time priority.
  security.pam.loginLimits = [
    { domain = "@audio"; item = "memlock"; type = "-";    value = "unlimited"; }
    { domain = "@audio"; item = "rtprio";  type = "-";    value = "99"; }
    { domain = "@audio"; item = "nofile";  type = "soft"; value = "524288"; }
    { domain = "@audio"; item = "nofile";  type = "hard"; value = "524288"; }
  ];

  # ── Optional: Printing ───────────────────────────────────────────────────────
  # Uncomment to enable CUPS printing.
  # services.printing.enable = true;

  # ── CPU microcode ────────────────────────────────────────────────────────────
  # Loads AMD microcode updates early in boot — improves stability and security.
  hardware.cpu.amd.updateMicrocode = true;

  # ── Firmware updates ─────────────────────────────────────────────────────────
  # Enables fwupd — updates motherboard, SSD, and peripheral firmware via KDE
  # Discover or `fwupdmgr update` in the terminal.
  services.fwupd.enable = true;

  # ── Bluetooth ────────────────────────────────────────────────────────────────
  # KDE's Bluedevil provides the GUI — no need for blueman.
  hardware.bluetooth.enable      = true;
  hardware.bluetooth.powerOnBoot = true;

  # ── Tailscale (mesh VPN) ─────────────────────────────────────────────────────
  # After enabling, run `sudo tailscale up` to authenticate.
  services.tailscale.enable = true;

  # ── Power profiles ───────────────────────────────────────────────────────────
  # Exposes balanced / performance / power-saver profiles in KDE's battery applet.
  services.power-profiles-daemon.enable = true;

  # ── Jellyfin (self-hosted media server) ──────────────────────────────────────
  # Web UI available at http://localhost:8096 after first boot.
  # openFirewall = true lets other devices on the LAN reach it.
  services.jellyfin = {
    enable      = true;
    openFirewall = true;
  };

  # ── Optional: Printing ───────────────────────────────────────────────────────
  # Uncomment to enable CUPS printing.
  # services.printing.enable = true;
}
