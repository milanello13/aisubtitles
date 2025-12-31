#!/bin/sh

# =================================================================================================
# Command: wget https://raw.githubusercontent.com/milanello13/aisubtitles/main/installer.sh -O - | /bin/sh #
# =================================================================================================
# Configuration
#########################################
plugin="aisubtitles"
git_url="https://github.com/milanello13/aisubtitles/raw/main/aisubtitles/"

version=$(wget $git_url/version -qO- | awk 'NR==1')
plugin_path="/usr/lib/enigma2/python/Plugins/Extensions/AISubtitles"
package="enigma2-plugin-extensions-$plugin"
targz_file="$plugin.tar.gz"
url="$git_url/$targz_file"
temp_dir="/tmp"

# Determine package manager
#########################################
if command -v dpkg &> /dev/null; then
package_manager="apt"
status_file="/var/lib/dpkg/status"
uninstall_command="apt-get purge --auto-remove -y"
else
package_manager="opkg"
status_file="/var/lib/opkg/status"
uninstall_command="opkg remove --force-depends"
fi

#check and_remove package old version
#########################################
check_and_remove_package() {
if [ -d $plugin_path ]; then
echo "> removing package old version please wait..."
sleep 3 
rm -rf $plugin_path > /dev/null 2>&1
rm -rf /etc/enigma2/aisubtitles > /dev/null 2>&1

if grep -q "$package" "$status_file"; then
echo "> Removing existing $package package, please wait..."
$uninstall_command $package > /dev/null 2>&1
fi
echo "*******************************************"
echo "*             Removed Finished            *"
echo "*           Created By ammarbary          *"
echo "*******************************************"
sleep 3
exit 1
else
echo " " 
fi  }
check_and_remove_package

#check & install dependencies
#########################################
check_and_install_dependencies() {
# Determine package manager
if command -v dpkg &> /dev/null; then
    install_command="apt-get install"
else
    install_command="opkg install"
fi
#check python version
python=$(python -c"from sys import version_info; print(version_info[0])")
sleep 1;
case $python in
3)
$install_command python3-pillow python3-requests> /dev/null 2>&1
;;
*)
echo "> your image python version: $python is not supported"
sleep 3
exit 1
;;
esac
}
check_and_install_dependencies

#download & install package
#########################################
download_and_install_package() {
echo "> Downloading $plugin-$version package  please wait ..."
sleep 3
wget --show-progress -qO $temp_dir/$targz_file --no-check-certificate $url
tar -xzf $temp_dir/$targz_file -C / > /dev/null 2>&1
extract=$?
rm -rf $temp_dir/$targz_file >/dev/null 2>&1

if [ $extract -eq 0 ]; then
  echo "> $plugin-$version package installed successfully"
  sleep 3
  echo ""
else
  echo "> $plugin-$version package download failed"
  sleep 3
fi  }
download_and_install_package

# Remove unnecessary files and folders
#########################################
print_message() {
echo "> [$(date +'%Y-%m-%d')] $1"
}
cleanup() {
[ -d "/CONTROL" ] && rm -rf /CONTROL >/dev/null 2>&1
rm -rf /control /postinst /preinst /prerm /postrm /tmp/*.ipk /tmp/*.tar.gz >/dev/null 2>&1
print_message "> Uploaded By ammarbary "
}
cleanup
