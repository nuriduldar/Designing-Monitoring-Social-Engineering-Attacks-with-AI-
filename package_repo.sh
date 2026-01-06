#!/bin/bash

# Package the repository into a zip file, excluding sensitive files
# Usage: ./package_repo.sh

set -e

PROJECT_NAME="social-engineering-ai"
ZIP_NAME="${PROJECT_NAME}.zip"
TEMP_DIR=$(mktemp -d)

echo "Packaging ${PROJECT_NAME}..."

# Copy all files except those in .gitignore
rsync -av --exclude-from=.gitignore \
  --exclude='.git' \
  --exclude='*.zip' \
  --exclude='.env' \
  --exclude='models/' \
  --exclude='*.pyc' \
  --exclude='__pycache__/' \
  . "${TEMP_DIR}/${PROJECT_NAME}/"

# Create zip
cd "${TEMP_DIR}"
zip -r "${ZIP_NAME}" "${PROJECT_NAME}/" > /dev/null

# Move to original directory
mv "${ZIP_NAME}" "${OLDPWD}/"

# Cleanup
rm -rf "${TEMP_DIR}"

echo "Created: ${ZIP_NAME}"
echo "Excluded: .env, models/, *.pyc, __pycache__/"

