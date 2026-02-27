#!/bin/bash
# VFS Appointment Bot - Setup & Run Script
# ==========================================

set -e

echo "=== VFS Appointment Bot Setup ==="

# Install Python dependencies
echo "[1/3] Installing Python dependencies..."
pip install -r requirements.txt 2>&1 | tail -3

# Install Playwright browser + system deps
echo "[2/3] Installing Chromium browser for Playwright..."
sudo playwright install-deps chromium 2>&1 | tail -3
playwright install chromium 2>&1 | tail -3

echo "[3/3] Setup complete!"
echo ""
echo "=== Run the bot ==="
echo ""
echo "# For Portugal (from Morocco):"
echo 'python -m vfs_appointment_bot.main -sc MA -dc PT -ap "visa_center=<center>,visa_category=<category>,visa_sub_category=<sub_category>"'
echo ""
echo "# For Spain (from Morocco):"
echo 'python -m vfs_appointment_bot.main -sc MA -dc ES -ap "visa_center=<center>,visa_category=<category>,visa_sub_category=<sub_category>"'
echo ""
echo "Replace <center>, <category>, <sub_category> with actual values from the VFS website."
echo "Example: visa_center=Casablanca,visa_category=National Visa,visa_sub_category=Study"
