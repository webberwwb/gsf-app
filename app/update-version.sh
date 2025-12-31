#!/bin/bash
# Script to update Service Worker version before deployment
# This ensures users get the latest version of your app

set -e  # Exit on error

# Get current date and time for version
VERSION=$(date +"%Y.%m.%d.%H%M")

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 Updating Service Worker version"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📅 New version: $VERSION"
echo ""

# Update version in sw.js
if [ -f "public/sw.js" ]; then
  sed -i '' "s/const VERSION = '[^']*'/const VERSION = '$VERSION'/" public/sw.js
  echo "✅ Service Worker version updated in public/sw.js"
else
  echo "❌ Error: public/sw.js not found"
  exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Building application..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Build the application
npm run build

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Build complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Deployment Info:"
echo "   • Service Worker version: $VERSION"
echo "   • Build output: dist/"
echo "   • Old caches will be automatically cleared"
echo ""
echo "🚀 Next steps:"
echo "   1. Deploy the dist/ folder to your server"
echo "   2. Users will see update banner within 2-5 minutes"
echo "   3. They click 'Update' to get the new version"
echo ""
echo "💡 Pro tip: Test in incognito mode first!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
