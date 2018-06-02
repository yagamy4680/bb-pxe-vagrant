# -*- mode: ruby -*-
# vi: set ft=ruby :

# Get the available physical CPU cores on host system, inspired by
# https://coderwall.com/p/ghbzhw
#
HW_CPUS = RbConfig::CONFIG['host_os'] =~ /darwin/ ?
    %x( sysctl -n hw.physicalcpu_max ) :
    %x( nproc )

# The guest system only uses half of physical CPU cores of host system.
VBOX_CPU = (HW_CPUS.to_i).to_s

# VBOX Name
VBOX_NAME = File.basename(Dir.getwd)

# Make sure `vagrant-shell-commander` plugin is installed,
# in order to execute some bash commands after the
# virtual machine is booted.
#
unless Vagrant.has_plugin?("vagrant-shell-commander")
  raise "vagrant-shell-commander is not installed!!"
end

# Hostname for guest system
VBOX_HOSTNAME = "#{VBOX_NAME}"

# Project Root
#
#PROJECT_ROOTDIR = File.expand_path(".")
#PROJECT_EXTERNAL_DIR = "#{PROJECT_ROOTDIR}/externals"

Vagrant.configure(2) do |config|

  # Use docker as base-image
  #
  # config.vm.box = "comiq/dockerbox"
  # config.vm.box = "ubuntu/xenial64"
  # config.vm.box = "generic/ubuntu1704"
  config.vm.box = "geerlingguy/ubuntu1604"
  config.vm.hostname = VBOX_HOSTNAME

  # BASH script to be executed after share-folder is mounted.
  # config.sh.after_share_folders = "sudo /vagrant/init $(uname -s)"

  config.vm.provider "virtualbox" do |vb|
    # Display the VirtualBox GUI when booting the machine
    vb.gui = false

    vb.customize [
      "modifyvm", :id,
      "--cpus", VBOX_CPU,
      "--memory", "1024",
      "--paravirtprovider", "kvm", # for linux guest
      "--usb", "on",
      "--usbehci", "on"
    ]

    # ICS Advent, USB 2.0 10/100M Ethernet Adaptor
    #
    vb.customize ["usbfilter", "add", "0",
        "--target", :id,
        "--name", "USB 2.0 10/100M Ethernet Adaptor",
        "--vendorid", "0FE6",
        "--productid", "9700"
    ]

    # Realtek USB 10/100 LAN
    #
    vb.customize ["usbfilter", "add", "1",
        "--target", :id,
        "--name", "USB 10/100 LAN",
        "--vendorid", "0BDA",
        "--productid", "8152"
    ]

    # DM9621A USB To FastEther
    #
    vb.customize ["usbfilter", "add", "1",
        "--target", :id,
        "--name", "DM9621A USB To FastEther",
        "--vendorid", "0A46",
        "--productid", "1269"
    ]

    # FTDI TTL232R-3V3
    #
    vb.customize ["usbfilter", "add", "2",
        "--target", :id,
        "--name", "TTL232R-3V3",
        "--vendorid", "0403",
        "--productid", "6001",
        "--manufacturer", "FTDI"
    ]

    # Realtek 802.11n WLAN Adapter
    #
    vb.customize ["usbfilter", "add", "3",
        "--target", :id,
        "--name", "802.11n WLAN Adapter",
        "--vendorid", "7392",
        "--productid", "7811",
        "--manufacturer", "Realtek"
    ]
  end
end
