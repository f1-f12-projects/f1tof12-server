#!/bin/bash
set -e

echo "🚀 F1toF12 Deployment Script"
echo "============================"
echo ""
echo "Select deployment type:"
echo "1) Dev (localDev → dev)"
echo "2) Prod (dev → main)"
read -p "Enter choice [1-2]: " choice

case $choice in
    1)
        echo "\n📦 Dev Deployment: localDev → dev"
        CURRENT_BRANCH=$(git branch --show-current)
        if [ "$CURRENT_BRANCH" != "localDev" ]; then
            echo "❌ Error: Must be on 'localDev' branch. Currently on '$CURRENT_BRANCH'"
            exit 1
        fi
        
        if ! git diff-index --quiet HEAD --; then
            echo "❌ Error: Uncommitted changes detected. Commit or stash them first."
            exit 1
        fi
        
        echo "📥 Fetching latest changes..."
        git fetch origin
        
        echo "🔄 Updating localDev branch..."
        git pull origin localDev
        
        echo "🔀 Switching to dev branch..."
        git checkout dev
        
        echo "🔄 Updating dev branch..."
        git pull origin dev
        
        echo "🔗 Merging localDev into dev..."
        if git merge localDev --no-edit; then
            echo "✅ Merge successful"
        else
            echo "❌ Merge failed. Resolve conflicts and try again."
            git checkout localDev
            exit 1
        fi
        
        echo "📤 Pushing to dev (triggers dev deployment)..."
        if git push origin dev; then
            echo "✅ Successfully pushed to dev"
            echo "🎯 GitHub Actions will deploy to Dev Lambda"
        else
            echo "❌ Push failed"
            git checkout localDev
            exit 1
        fi
        
        echo "🔙 Returning to localDev branch..."
        git checkout localDev
        ;;
    
    2)
        echo "\n🚀 Production Deployment: dev → main"
        CURRENT_BRANCH=$(git branch --show-current)
        if [ "$CURRENT_BRANCH" != "dev" ]; then
            echo "❌ Error: Must be on 'dev' branch. Currently on '$CURRENT_BRANCH'"
            exit 1
        fi
        
        if ! git diff-index --quiet HEAD --; then
            echo "❌ Error: Uncommitted changes detected. Commit or stash them first."
            exit 1
        fi
        
        echo "📥 Fetching latest changes..."
        git fetch origin
        
        echo "🔄 Updating dev branch..."
        git pull origin dev
        
        echo "🔀 Switching to main branch..."
        git checkout main
        
        echo "🔄 Updating main branch..."
        git pull origin main
        
        echo "🔗 Merging dev into main..."
        if git merge dev --no-edit; then
            echo "✅ Merge successful"
        else
            echo "❌ Merge failed. Resolve conflicts and try again."
            git checkout dev
            exit 1
        fi
        
        echo "📤 Pushing to main (triggers production deployment)..."
        if git push origin main; then
            echo "✅ Successfully pushed to main"
            echo "🎯 GitHub Actions will deploy to Production Lambda"
        else
            echo "❌ Push failed"
            git checkout dev
            exit 1
        fi
        
        echo "🔙 Returning to dev branch..."
        git checkout dev
        ;;
    
    *)
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac

echo ""
echo "✨ Deployment initiated successfully!"
echo "⏳ Check GitHub Actions for deployment status"
echo "📊 Monitor: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
