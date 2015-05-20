#!/bin/bash

# Enables all the repositories that are required for IPA installation

sudo dnf copr enable mkosek/freeipa-master -y
sudo dnf copr enable edewata/pki-fedora -y
sudo dnf copr enable mkosek/freeipa -y

# Update to pull new packages from these repos
sudo dnf update -y
