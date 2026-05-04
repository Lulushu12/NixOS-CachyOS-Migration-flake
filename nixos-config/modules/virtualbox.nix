# VirtualBox guest additions.
#
# What this enables:
#   - Automatic screen resolution adjustment when you resize the VM window
#   - Shared clipboard between host and VM (set in VirtualBox: Devices → Clipboard)
#   - Drag-and-drop between host and VM
#   - Shared folders (mount with: `sudo mount -t vboxsf <sharename> /mnt/share`)
#     Members of the `vboxsf` group can access shared folders without sudo.
#
# The guest additions version is kept in sync with your VirtualBox installation
# automatically by NixOS — no manual updates needed.

{ pkgs, ... }:

{
  # VirtualBox Guest Additions require a kernel they can compile against.
  # linuxPackages_latest (6.15+) is not yet supported by vbox-guest 7.1.x;
  # pin to the 6.6 LTS kernel which is fully compatible.
  boot.kernelPackages = pkgs.linuxPackages_6_6;

  virtualisation.virtualbox.guest = {
    enable       = true;
    dragAndDrop  = true;
  };
}
