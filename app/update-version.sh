#!/bin/bash
# Script to update Service Worker version before deployment

# Get current date and time for version
VERSION=$(date +"%Y.%m.%d.%H%M")

echo "Updating Service Worker version to: $VERSION"

# Update version in sw.js
sed -i '' "s/const VERSION = '[^']*'/const VERSION = '$VERSION'/" public/sw.js

echo "✅ Service Worker version updated"
echo "📦 Building application..."

# Build the application
npm run build

echo "✅ Build complete!"
echo ""
echo "🚀 Now you can deploy the dist/ folder"
echo "   Service Worker version: $VERSION"


