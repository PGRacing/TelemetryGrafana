#!/bin/bash
# Author           : Malwina Kozak
# Created On       : 06.01.2024
# Last Modified By : Malwina Kozak
# Last Modified On : 16.01.2024
# Version          : 1.12
#
# DESCRIPTION 
# The script will connect to your FTP server and backups
# two files: sql.tar.gz and www.tar.gz. You need to prepare these two
# files on your remote server, in case of question please contact
# hosting provider and check manual.
#
# LICENSE 
# This program is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version. This program is
# distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details. You should have received a copy of the
# GNU General Public License along with this program.  If not, see
# <http://www.gnu.org/licenses/>.
#
# Variables for frequent use
# param_given variable is used to start text menu with options when
# paramaters are not given. If parameters are given, there is no need
# to display menu.
param_given=false
login=""
password=""
server=""
# Current directory is set as current folder if user will not specify
# other location
catalog=$PWD
help="BraveBackup script – help
The purpose of the script is to download backup files from your
server. In most cases hosting providers will have only one backup
server, and in case of losing this machine you will loose all your
work. I recommend to perform this backup weekly. 

What you need to know:
1. Please prepare the backup files on your servers, on most cases
 there will be two two files: one for WWW files, second for SQL
 (database).
2. Files should be compressed and you should have two files:
- www.tar.gz – all your files (in most cases whole /public_html folder)
- sql.tar.gz – your database
3. The files should be placed in dedicated folder on your server and
 this folder should be accessible by specified FTP user 
4. Depending on your website, the files could have more than 1GB –
 please check available space on your disk before performing the backup.
5. After downloading you can delete files from your server to save
 diskspace.
For detailed syntax please check man ./BraveBackup.1
In case of question, please contact me."

copyright="╔╗ ┬─┐┌─┐┬  ┬┌─┐╔╗ ┌─┐┌─┐┬┌─┬ ┬┌─┐
╠╩╗├┬┘├─┤└┐┌┘├┤ ╠╩╗├─┤│  ├┴┐│ │├─┘
╚═╝┴└─┴ ┴ └┘ └─┘╚═╝┴ ┴└─┘┴ ┴└─┘┴  1.12

The script will backup your website to your local computer.
Please prepare on your server two files, please check help:
  1) www.tar.gz – all your files (in most cases /public_html folder)
  2) sql.tar.gz – your database.
  "
# Function to display version
version() {
    clear
    echo "Version 1.12, Malwina Kozak"
}

# The function to handle displaying the menu
menu () {
# Clear the screen to display the logo and menu properly
# Print Welcome Screen
# Define default values
login="LOGIN"
password="PASSWORD"
server="SERVER"
catalog=$PWD
while true
do
  clear
  echo "$copyright"
  echo "Please choose"
  echo "[0]. General help - please read carefully!" 
  echo "[1]. Check the free space on your disk"
  echo "[2]. Specify folder to download: $catalog"
  echo "[3]. Specify FTP username: $login" 
  echo "[4]. Specify FTP password: $password"
  echo "[5]. Specify FTP server: $server"
  echo "[6]. Perform backup!"
  echo "[7]. Extract downloaded files"    
  echo "[8]. Quit"
  echo ""
  echo "What is your choice? "

 # Start the main program 
 read choice
      if [ $choice -eq 8 ]
  then
      clear 
      echo "$copyright"
      echo "Thank you for using BraveBackup!"
      break
  elif [ $choice -eq 0 ]
  then
    clear
      echo "$help"
      read -p "Press ENTER to continue" nopurpose
  elif [ $choice -eq 1 ]
  then
  echo "Available disk space on your local machine"
  df -H
    read -p "Press ENTER to continue" nopurpose
  elif [ $choice -eq 2 ]
  then
    echo "Default catalog is:" $PWD  
    read -p "Please enter the name of the catalog: " catalog
  elif [ $choice -eq 3 ]
  then
      echo "Current login: " $login
      read -p "Please specify the FTP username on your server: " login
  elif [ $choice -eq 4 ]
  then
      echo "Current password: " $password
      read -p "Please specify the FTP password on your server: " password    
  elif [ $choice -eq 5 ]
  then
      echo "Current FTP server: " $server
      read -p "Please specify the FTP server: " server    
  elif [ $choice -eq 6 ]
  then
    # Clear screen
    clear 
    echo "$copyright"
    # Transfer input to server data
    www_file="ftp://${server}/www.tar.gz"
    sql_file="ftp://${server}/sql.tar.gz"
    # Print all the details about the connection
    echo "FTP login: $login"
    echo "FTP password: $password"
    echo "Full WWW backup filepath: $www_file"
    echo "Full SQL backup filepath: $sql_file"
    read -p "Press ENTER to continue" nopurpose    

    echo "Downloading your backup..."
    # Download files using wget, -P is local path
    wget -P $catalog --user=$login --password=$password $www_file
    wget -P $catalog --user=$login --password=$password $sql_file   
    read -p "Press ENTER to continue" nopurpose    

  elif [ $choice -eq 7 ]
  then
    clear
    echo "$copyright"
    # tar parameters to extract the archive
    # x extract, 
    # v Verbose/show output 
    # f specify the File
    tar -xvf ${catalog}/www.tar.gz -C $catalog
    tar -xvf ${catalog}/sql.tar.gz -C $catalog
    echo "Extracting completed. Enjoy your files!"
    read -p "Press ENTER to continue" nopurpose
  else
    echo "Please choose number from 0 to 8"
    read -p "Press ENTER to continue" nopurpose
  fi
done
}

# Loop over all the getops options
# exit 0 - finished succesfully
# exit 1 - finished with errors
# for getops for v (version) and h (help) no need to give an argument, 
# so ":" is not needed for these two
while getopts "l:p:s:c:vh" opt; do
  case ${opt} in
    l)
      login=$OPTARG
      param_given=true
      ;; 
    p)
      password=$OPTARG
      param_given=true
      ;;
    s)
      server=$OPTARG
      param_given=true
      ;;
    c)
      catalog=$OPTARG 
      param_given=true  
      ;;
    v)
      version
      param_given=true
      exit 0  
      ;;
    h)
      echo $help
      param_given=true
      exit 0
      ;;
 # Handling other options
    \?)
      echo "Not known options: -$OPTARG" >&2
      exit 1
      ;;
     # No parameter
    :)
      echo "Option -$OPTARG needs an argument." >&2
      exit 1
      ;;
  esac
done

# If no parameters - show text menu
if ! $param_given ; then
# Start menu function  
menu
exit 0
fi

# If parameters are given start to download
# Show full path to download with the parameters
  echo "Downloading your backup..."
  echo login: $login
  echo password: $password 
  echo server: $server 
  echo local catalog: $catalog
# Convert to full path
  www_file="ftp://${server}/www.tar.gz"
  sql_file="ftp://${server}/sql.tar.gz"

  #Download files using wget, -P is local path
  wget -P $catalog --user=$login --password=$password $www_file
  wget -P $catalog --user=$login --password=$password $sql_file
  read -p "Press ENTER to continue" nopurpose
  exit 0


