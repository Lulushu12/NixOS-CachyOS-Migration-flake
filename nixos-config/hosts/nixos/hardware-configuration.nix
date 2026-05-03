{ config, lib, pkgs, modulesPath, ... }:

{
  imports =
    [ (modulesPath + "/installer/scan/not-detected.nix")
    ];

  boot.initrd.availableKernelModules = [ "nvme" "xhci_pci" "ahci" "usb_storage" "usbhid" "sd_mod" ];
  boot.initrd.kernelModules = [ ];
  boot.kernelModules = [ "kvm-amd" ];
  boot.extraModulePackages = [ ];

  fileSystems."/" = {
    device = "/dev/disk/by-uuid/3b325acc-6046-4f45-ab99-97eb9e5385ce";
    fsType = "ext4";
  };

  fileSystems."/boot" = {
    device = "/dev/disk/by-uuid/AD86-B6E7";
    fsType = "vfat";
    options = [ "fmask=0077" "dmask=0077" ];
  };

  # /home partition — uncomment the correct one once confirmed:
  #   nvme0n1p2  ext4   UUID 9f89bcd3-935e-4db7-979f-25d8a67126b3
  #   nvme1n1p1  btrfs  UUID 4c84f5c3-7504-4709-9ee1-e2e366e38f88
  #   sda1       ext4   UUID 7fbdcc9d-3097-41e2-87b3-347ca9025691
  # fileSystems."/home" = {
  #   device = "/dev/disk/by-uuid/REPLACE-ME";
  #   fsType = "ext4";
  # };

  swapDevices =
    [ { device = "/dev/disk/by-uuid/1995d5af-8005-46de-a02f-cdaf4cd5bda5"; }
    ];

  nixpkgs.hostPlatform = lib.mkDefault "x86_64-linux";
  hardware.cpu.amd.updateMicrocode = lib.mkDefault config.hardware.enableRedistributableFirmware;
}
