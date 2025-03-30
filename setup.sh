#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Improved Banner
echo -e "${PURPLE}"
echo " _   _ _   _ ____   ____    _    _   _ _   _ _____ ____  "
echo "| | | | \ | / ___| / ___|  / \  | \ | | \ | | ____|  _ \ "
echo "| | | |  \| \___ \| |     / _ \ |  \| |  \| |  _| | |_) |"
echo "| |_| | |\  |___) | |___ / ___ \| |\  | |\  | |___|  _ < "
echo " \___/|_| \_|____/ \____/_/   \_\_| \_|_| \_|_____|_| \_\"
echo -e "${NC}"
echo -e "${CYAN}UNSCANNER - High-Grade Port Scanner${NC}"
echo -e "${YELLOW}Installation Script${NC}"
echo ""


# Function to compare versions
version_compare() {
    local req_ver="$1"
    local cur_ver="$2"
    
    # Split version numbers into arrays
    IFS='.' read -ra req_parts <<< "$req_ver"
    IFS='.' read -ra cur_parts <<< "$cur_ver"
    
    # Compare each part
    for i in "${!req_parts[@]}"; do
        if [[ -z "${cur_parts[i]}" ]]; then
            return 0
        elif ((10#${cur_parts[i]} > 10#${req_parts[i]})); then
            return 0
        elif ((10#${cur_parts[i]} < 10#${req_parts[i]})); then
            return 1
        fi
    done
    return 0
}

# Check Python version (without bc)
echo -e "${BLUE}[*] Checking Python version...${NC}"
python_version=$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))' 2>/dev/null || echo "0.0")
required_version="3.6"

if version_compare "$required_version" "$python_version"; then
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
    
    # Detect package manager
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-tk
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-tkinter
    elif command -v pacman &> /dev/null; then
        sudo pacman -Syu --noconfirm tk
    else
        echo -e "${RED}[X] Could not detect package manager. Please install Tkinter manually:"
        echo -e "Debian/Ubuntu: sudo apt-get install python3-tk"
        echo -e "RHEL/CentOS: sudo yum install python3-tkinter"
        echo -e "Arch: sudo pacman -S tk${NC}"
        exit 1
    fi
    
    # Verify installation
    if python3 -c "import tkinter" &> /dev/null; then
        echo -e "${GREEN}[✓] Tkinter successfully installed${NC}"
    else
        echo -e "${RED}[X] Failed to install Tkinter${NC}"
        exit 1
    fi
fi

# Check other dependencies
echo -e "${BLUE}[*] Verifying Python dependencies...${NC}"
dependencies=("socket" "concurrent.futures" "json" "threading" "re" "struct")
all_ok=true

for dep in "${dependencies[@]}"; do
    if python3 -c "import $dep" &> /dev/null; then
        echo -e "${GREEN}[✓] $dep module available${NC}"
    else
        echo -e "${RED}[X] $dep module missing${NC}"
        all_ok=false
    fi
done

if ! $all_ok; then
    echo -e "${RED}[X] Some critical dependencies are missing${NC}"
    exit 1
fi

# Final message
echo -e "${PURPLE}"
echo "Unscanner is ready to use!"
echo -e "${NC}"
echo -e "Run the scanner with: ${CYAN}python3 scan-gui.py${NC}"
echo -e "For command line mode: ${CYAN}python3 scan-gui.py --target <IP> --ports <RANGE>${NC}"
echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
