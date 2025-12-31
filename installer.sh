#!/bin/sh

# =================================================================================================
# Command: wget https://raw.githubusercontent.com/milanello13/aisubtitles/main/installer.sh -O - | /bin/sh #
# =================================================================================================
# Configuration
#########################################

plugin="aisubtitles"
git_url="https://github.com/milanello13/aisubtitles/raw/main/aisubtitles"
plugin_path="/usr/lib/enigma2/python/Plugins/Extensions/AISubtitles"
targz_file="$plugin.tar.gz"
url="$git_url/$targz_file"
temp_dir="/tmp"

# remove old version
if [ -d "$plugin_path" ]; then
    echo "> Removing old version..."
    rm -rf "$plugin_path"
    rm -rf /etc/enigma2/aisubtitles
fi

# check python3
if ! command -v python3 >/dev/null 2>&1; then
    echo "> Python3 not found"
    exit 1
fi

# install dependencies
if command -v opkg >/dev/null 2>&1; then
    opkg update
    opkg install python3-pillow python3-requests python3-certifi
else
    apt-get update
    apt-get install -y python3-pillow python3-requests python3-certifi
fi

# download
echo "> Downloading plugin..."
wget -O "$temp_dir/$targz_file" --no-check-certificate "$url" || exit 1

# extract
tar -xzf "$temp_dir/$targz_file" -C / || exit 1
rm -f "$temp_dir/$targz_file"

echo "> AISubtitles installed successfully"
