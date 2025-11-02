#!/bin/bash
set -e  # Exit on error

echo "🔄 Starting build process..."

# Update package list
apt-get update

# Install system dependencies
apt-get install -y \
    wget \
    unzip \
    curl \
    gnupg \
    xvfb \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2

# Install Chrome
echo "📥 Installing Google Chrome..."
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Install ChromeDriver
echo "📥 Installing ChromeDriver..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}')
echo "Chrome version: $CHROME_VERSION"

# Dapatkan major version untuk ChromeDriver
MAJOR_VERSION=$(echo $CHROME_VERSION | cut -d'.' -f1)
CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$MAJOR_VERSION")
echo "ChromeDriver version: $CHROMEDRIVER_VERSION"

wget -q "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip -q chromedriver_linux64.zip
chmod +x chromedriver
mv chromedriver /usr/local/bin/
rm chromedriver_linux64.zip

# Verifikasi instalasi
echo "✅ Chrome version: $(google-chrome --version)"
echo "✅ ChromeDriver version: $(chromedriver --version)"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎉 Build completed successfully!"
