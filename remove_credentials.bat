@echo off
echo Removing credentials files from Git history...

git filter-branch --force --index-filter "git rm --cached --ignore-unmatch deploy/firebase-credentials.json spinthewheel-e14a6-firebase-adminsdk-fbsvc-f1be0ee9e1.json" --prune-empty --tag-name-filter cat -- --all

echo Done.
echo Now run: git push --force 