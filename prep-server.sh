#!/bin/bash


# Credits: lazy-electrons (rajeshvs)
# Summary: This script installs the NVIDIA CUDA Toolkit, NVIDIA Driver, NVIDIA Container Toolkit, Docker, the Hugging Face Hub Python Client, and NVTOP on Ubuntu 22.04.x and related systems.

# Setup the Script Variables
echo "Setting up the Script Variables..."
set -o nounset
disable_apparmor=true
disable_firewall=true
enable_rootless_docker=false
enable_system_startup_for_rootless_docker=false



# Setup the Log File
echo "Setting up the Log File..."
mkdir -p $HOME/logs
log_file=$HOME/logs/private-ai-quick-setup.log
exec > >(tee -i $log_file) 2>&1

# Start the Private AI Quick Pre-Setup
echo "Starting the Private AI Quick Pre-Setup..."

# Set Permissions for Accessible Private AI Setup Files
echo "Setting Permissions for Accessible Private AI Setup Files..."
script_directory="$(cd "$(dirname "${bash_source[0]}")" && pwd)"
private_ai_files=("prep-server.sh")
for private_ai_file in "${private_ai_files[@]}"; do
    target_file="$script_directory/$private_ai_file"
    [ -e "$target_file" ] && chmod a+x "$target_file"
done

# Disable AppArmor
if [ "$disable_apparmor" = "true" ]; then
    echo "Disabling AppArmor..."
    sudo systemctl stop apparmor
    sudo systemctl disable apparmor
fi

# Disable Firewall
if [ "$disable_firewall" = "true" ]; then
    echo "Disabling the Firewall..."
    sudo systemctl stop ufw
    sudo systemctl disable ufw
fi



# Uninstall Previous Docker Installations
echo "Uninstalling Previous Docker Installations..."
sudo snap remove docker --purge

# Install UIDMap (Prerequisite for Docker Rootless Mode)
if [ "$enable_rootless_docker" = "true" ]; then
    echo "Installing UIDMap (Prerequisite for Docker Rootless Mode)..."
    sudo apt-get install -y uidmap
fi

# Install Docker
echo "Installing Docker..."
sudo apt  install docker.io -y

sudo apt  install docker-compose -y

# Add the user named $(whoami) to the Docker Group
if [ ! "$enable_rootless_docker" = "true" ]; then
    echo "Adding the user named $(whoami) to the Docker Group..."
    sudo usermod -aG docker $(whoami)
fi

# Setup Docker in Rootless Mode
if [ "$enable_rootless_docker" = "true" ]; then
    echo "Setting up Docker in Rootless Mode..."
    /usr/bin/dockerd-rootless-setuptool.sh install
fi

# Install the NVIDIA Container Toolkit
echo "Installing the NVIDIA Container Toolkit..."
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor --yes -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
    && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configure Docker to Use the NVIDIA Container Runtime
echo "Configuring Docker to Use the NVIDIA Container Runtime..."
sudo nvidia-ctk runtime configure --runtime=docker

# Ensure Any Previous NVIDIA Container Runtime Installations Are Set to Support Cgroups
echo "Ensuring Any Previous NVIDIA Container Runtime Installations Are Set to Support Cgroups..."
sudo nvidia-ctk config --set nvidia-container-cli.no-cgroups=false --in-place

# Restart Docker to Apply NVIDIA Container Runtime Configuration
echo "Restarting Docker to Apply NVIDIA Container Runtime Configuration..."
sudo systemctl restart docker

# Configure the NVIDIA Container Runtime for Docker to Run in Rootless Mode
if [ "$enable_rootless_docker" = "true" ]; then
    echo "Configuring the NVIDIA Container Runtime for Docker to Run in Rootless Mode..."
    nvidia-ctk runtime configure --runtime=docker --config=$HOME/.config/docker/daemon.json
    systemctl --user restart docker
    sudo nvidia-ctk config --set nvidia-container-cli.no-cgroups --in-place
fi

# Enable System Startup for Rootless Docker
if [ "$enable_rootless_docker" = "true" ]; then
    if [ "$enable_system_startup_for_rootless_docker" = "true" ]; then
        echo "Enabling System Startup for Rootless Docker..."
        systemctl --user enable docker
        sudo loginctl enable-linger $(whoami)
    fi
fi

# Install NVTOP
echo "Installing NVTOP..."
sudo add-apt-repository ppa:quentiumyt/nvtop -y
sudo apt install nvtop -y

# apt install python3.10-venv -y 
# python3 -m venv .venv
# source .venv/bin/activate

echo "Installing Python 3 pip..."
sudo apt-get install -y python3-pip

sudo pip3 install "docker<7.0.0" 
# Install Hugging Face Hub
echo "Installing Hugging Face Hub..."
sudo pip3 install huggingface_hub[hf_xet]

# Install Hugging Face HF-Transfer
echo "Installing Hugging Face HF-Transfer..."
sudo pip3 install hf_transfer

# Update PATH with Potential 'huggingface-cli' Directory
echo "Updating PATH with Potential 'huggingface-cli' Directory..."
PATH=$PATH:$HOME/.local/bin

# Add Hugging Face HF-Transfer Environment Variable to .bashrc
echo "Adding Hugging Face HF-Transfer Environment Variable to .bashrc..."
sudo cat << EOF >> ~/.bashrc

# Hugging Face HF-Transfer Enablement
export HF_HUB_ENABLE_HF_TRANSFER=1

EOF
source ~/.bashrc
