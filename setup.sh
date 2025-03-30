#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "  ____  _            _   _       ____                  "
echo " / ___|| |_ ___  ___| |_| |     / ___|  ___ __ _ _ __ "
echo " \___ \| __/ _ \/ __| __| |____\___ \ / __/ _\` | '_ \\"
echo "  ___) | ||  __/ (__| |_| |_____|__) | (_| (_| | | | |"
echo " |____/ \__\___|\___|\__|_|    |____/ \___\__,_|_| |_|"
echo -e "${NC}"
echo -e "${CYAN}StealthScan Pro - Military Grade Port Scanner${NC}"
echo -e "${YELLOW}Installation Script${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}[!] Warning: Running as root is not recommended.${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${NC}"
        exit 1
    fi
fi

# Check Python version
echo -e "${BLUE}[*] Checking Python version...${NC}"
python_version=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
required_version="3.6"

if [[ $(echo "$python_version >= $required_version" | bc -l) -eq 1 ]]; then
    echo -e "${GREEN}[✓] Python $python_version detected (>= $required_version required)${NC}"
else
    echo -e "${RED}[X] Python 3.6+ is required but found $python_version${NC}"
    exit 1
fi

# Check for Tkinter
echo -e "${BLUE}[*] Checking for Tkinter...${NC}"
if python3 -c "import tkinter" &> /dev/null; then
    echo -e "${GREEN}[✓] Tkinter is installed${NC}"
else
    echo -e "${YELLOW}[!] Tkinter not found. Installing...${NC}"
    
    # Detect OS and install Tkinter
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        case $ID in
            debian|ubuntu|linuxmint)
                sudo apt-get update
                sudo apt-get install -y python3-tk
                ;;
            fedora|centos|rhel)
                sudo yum install -y python3-tkinter
                ;;
            arch|manjaro)
                sudo pacman -Syu --noconfirm tk
                ;;
            *)
                echo -e "${RED}[X] Unsupported Linux distribution. Please install Tkinter manually.${NC}"
                exit 1
                ;;
        esac
        
        # Verify installation
        if python3 -c "import tkinter" &> /dev/null; then
            echo -e "${GREEN}[✓] Tkinter successfully installed${NC}"
        else
            echo -e "${RED}[X] Failed to install Tkinter${NC}"
            exit 1
        fi
    else
        echo -e "${RED}[X] Could not detect OS. Please install Tkinter manually.${NC}"
        exit 1
    fi
fi

# Check other dependencies
echo -e "${BLUE}[*] Verifying Python dependencies...${NC}"
dependencies=("socket" "concurrent.futures" "json" "threading" "re" "struct")
missing_deps=0

for dep in "${dependencies[@]}"; do
    if python3 -c "import $dep" &> /dev/null; then
        echo -e "${GREEN}[✓] $dep module available${NC}"
    else
        echo -e "${RED}[X] $dep module missing${NC}"
        ((missing_deps++))
    fi
done

if [[ $missing_deps -gt 0 ]]; then
    echo -e "${RED}[X] $missing_deps critical dependencies missing${NC}"
    exit 1
fi

# Create virtual environment (optional but recommended)
echo -e "${BLUE}[*] Creating virtual environment...${NC}"
if python3 -m venv stealthscan-venv &> /dev/null; then
    echo -e "${GREEN}[✓] Virtual environment created${NC}"
    echo -e "${YELLOW}[!] Activate with: source stealthscan-venv/bin/activate${NC}"
else
    echo -e "${YELLOW}[!] Failed to create virtual environment (continuing anyway)${NC}"
fi

# Final message
echo -e "${PURPLE}"
echo "StealthScan Pro is ready to use!"
echo -e "${NC}"
echo -e "Run the scanner with: ${CYAN}python3 scan.py${NC}"
echo -e "For GUI mode: ${CYAN}python3 scan.py --gui${NC}"
echo -e "For command line mode: ${CYAN}python3 scan.py --target <IP> --ports <RANGE>${NC}"
echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
