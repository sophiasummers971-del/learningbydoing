#!/bin/bash

set -e

clear

RED='\e[1;31m'
GREEN='\e[1;32m'
YELLOW='\e[1;33m'
BLUE='\e[1;34m'
CYAN='\e[1;36m'
WHITE='\e[1;37m'
ORANGE='\e[1;93m'
NC='\e[0m'

if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root"
   exit 1
fi

COLOR_NUM=$((RANDOM % 7))
# Assign a color variable based on the random number
case $COLOR_NUM in
    0) COLOR=$RED;;
    1) COLOR=$GREEN;;
    2) COLOR=$YELLOW;;
    3) COLOR=$BLUE;;
    4) COLOR=$CYAN;;
    5) COLOR=$ORANGE;;
    *) COLOR=$WHITE;;
esac

echo -e "${COLOR}"
echo ""
echo "   ▄█    █▄       ▄████████  ▄████████    ▄█   ▄█▄  ▄█  ███▄▄▄▄      ▄██████▄           ███      ▄██████▄   ▄██████▄   ▄█       ";
echo "  ███    ███     ███    ███ ███    ███   ███ ▄███▀ ███  ███▀▀▀██▄   ███    ███      ▀█████████▄ ███    ███ ███    ███ ███       ";
echo "  ███    ███     ███    ███ ███    █▀    ███▐██▀   ███▌ ███   ███   ███    █▀          ▀███▀▀██ ███    ███ ███    ███ ███       ";
echo " ▄███▄▄▄▄███▄▄   ███    ███ ███         ▄█████▀    ███▌ ███   ███  ▄███                 ███   ▀ ███    ███ ███    ███ ███       ";
echo "▀▀███▀▀▀▀███▀  ▀███████████ ███        ▀▀█████▄    ███▌ ███   ███ ▀▀███ ████▄           ███     ███    ███ ███    ███ ███       ";
echo "  ███    ███     ███    ███ ███    █▄    ███▐██▄   ███  ███   ███   ███    ███          ███     ███    ███ ███    ███ ███       ";
echo "  ███    ███     ███    ███ ███    ███   ███ ▀███▄ ███  ███   ███   ███    ███          ███     ███    ███ ███    ███ ███▌    ▄ ";
echo "  ███    █▀      ███    █▀  ████████▀    ███   ▀█▀ █▀    ▀█   █▀    ████████▀          ▄████▀    ▀██████▀   ▀██████▀  █████▄▄██ ";
echo "                                         ▀                                                                            ▀         ";

echo -e "${BLUE}                                    https://github.com/Z4nzu/hackingtool ${NC}"
echo -e "${RED}                                     [!] This Tool Must Run As ROOT [!]${NC}\n"
echo -e "${CYAN}              Select Best Option : \n"
echo -e "${WHITE}              [1] Kali Linux / Parrot-Os (apt)"
echo -e "${WHITE}              [2] Arch Linux (pacman)" # added arch linux support because of feature request #231
echo -e "${WHITE}              [0] Exit "

echo -e "${COLOR}┌──($USER㉿$HOST)-[$(pwd)]"
choice=$1
if [[ ! $choice =~ ^[1-2]+$ ]]; then
    read -p "└─$>>" choice
fi

# Define installation directories
install_dir="/usr/share/hackingtool"
bin_dir="/usr/bin"

# Check if the user chose a valid option and perform the installation steps
if [[ $choice =~ ^[1-2]+$ ]]; then
    echo -e "${YELLOW}[*] Checking Internet Connection ..${NC}"
    echo "";
    if curl -s -m 10 https://www.google.com > /dev/null || curl -s -m 10 https://www.github.com > /dev/null; then
        echo -e "${GREEN}[✔] Internet connection is OK [✔]${NC}"
        echo "";
        echo -e "${YELLOW}[*] Updating package list ..."
        # Perform installation steps based on the user's choice
        if [[ $choice == 1 ]]; then
            sudo apt update -y && sudo apt upgrade -y
            sudo apt-get install -y git python3-pip figlet boxes php curl xdotool wget -y ;
        elif [[ $choice == 2 ]]; then
            sudo pacman -Syu --noconfirm
            sudo pacman -S --noconfirm git python-pip figlet curl wget php xdotool
            echo "Python 3.3+ comes with a module called venv."   # v0 feature preserved
            # Build boxes from AUR
            if [ -z "$SUDO_USER" ]; then
                echo -e "${RED}[!] For Arch Linux installation, this script must be run with sudo.${NC}"
                exit 1
            fi
            build_dir=$(mktemp -d)
            chown "$SUDO_USER:$SUDO_USER" "$build_dir"
            trap 'rm -rf "$build_dir"' EXIT
            sudo -u "$SUDO_USER" git clone https://aur.archlinux.org/boxes.git "$build_dir/boxes"
            pushd "$build_dir/boxes" > /dev/null
            sudo -u "$SUDO_USER" makepkg -s --noconfirm
            sudo pacman -U --noconfirm *.pkg.tar.*
            popd > /dev/null
        fi
        echo "";
        echo -e "${YELLOW}[*] Checking directories...${NC}"
        if [[ -d "$install_dir" ]]; then
            echo -e -n "${RED}[!] The directory $install_dir already exists. Do you want to replace it? [y/n]: ${NC}"
            read input
            if [[ $input == "y" ]] || [[ $input == "Y" ]]; then
                echo -e "${YELLOW}[*]Removing existing module.. ${NC}"
                sudo rm -rf "$install_dir"
            else
                echo -e "${RED}[✘]Installation Not Required[✘] ${NC}"
                exit 0
            fi
        fi
        echo "";
        echo -e "${YELLOW}[✔] Downloading hackingtool...${NC}"
        if sudo git clone https://github.com/Z4nzu/hackingtool.git $install_dir; then
            # Install virtual environment
            echo -e "${YELLOW}[*] Installing Virtual Environment...${NC}"
            if [[ $choice == 1 ]]; then
              sudo apt install python3-venv -y
            fi
            echo "";
            # Create a virtual environment for the tool
            echo -e "${YELLOW}[*] Creating virtual environment..."
            sudo python3 -m venv $install_dir/venv
            source $install_dir/venv/bin/activate
            # Install requirements
            echo -e "${GREEN}[✔] Virtual Environment successfully [✔]${NC}";
            echo "";
            echo -e "${YELLOW}[*] Installing requirements...${NC}"
            pip3 install -r $install_dir/requirements.txt
            if [[ $choice == 1 ]]; then
                # Debian/Ubuntu installation
                pip3 install -r $install_dir/requirements.txt
                sudo apt install figlet -y
                sudo apt install boxes -y
            
            elif [[ $choice == 2 ]]; then
                # Arch Linux installation
                pip3 install -r $install_dir/requirements.txt
                sudo pacman -S figlet --noconfirm
            
                # Install boxes from AUR
                sudo -u $SUDO_USER git clone https://aur.archlinux.org/boxes.git && cd boxes
                sudo -u $SUDO_USER makepkg -si
            fi

            # Create a shell script to launch the tool
            echo -e "${YELLOW}[*] Creating a shell script to launch the tool..."
            echo '#!/bin/bash' > $install_dir/hackingtool.sh
            echo "source $install_dir/venv/bin/activate" >> $install_dir/hackingtool.sh
            echo "python3 $install_dir/hackingtool.py \$@" >> $install_dir/hackingtool.sh
            chmod +x $install_dir/hackingtool.sh
            sudo mv $install_dir/hackingtool.sh $bin_dir/hackingtool
            echo -e "${GREEN}[✔] Script created successfully [✔]"
        else
            echo -e "${RED}[✘] Failed to download Hackingtool [✘]"
            exit 1
        fi

    else
       echo -e "${RED}[✘] Internet connection is not available [✘]${NC}"
       exit 1
    fi

    if [ -d $install_dir ]; then
        echo "";
        echo -e "${GREEN}[✔] Successfully Installed [✔]";
        echo "";
        echo "";
        echo -e  "${ORANGE}[+]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++[+]"
        echo     "[+]                                                             [+]"
        echo -e  "${ORANGE}[+]     ✔✔✔ Now Just Type In Terminal (hackingtool) ✔✔✔      [+]"
        echo     "[+]                                                             [+]"
        echo -e  "${ORANGE}[+]+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++[+]"
    else
        echo -e "${RED}[✘] Installation Failed !!! [✘]";
        exit 1
    fi

elif [[ $choice == 0 ]]; then
    echo -e "${RED}[✘] Exiting tool [✘]"
    exit 1
else
    echo -e "${RED}[!] Select Valid Option [!]"
fi
