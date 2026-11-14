#!/usr/bin/env bash
# ==============================================================================
# ISL Fingerspelling Dataset Setup & Ingestion Pipeline
# Organizes the Prathum Arikeri ISL Character Dataset into data/raw/fingerspelling/
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${ROOT_DIR}/data/raw/fingerspelling"

echo "=========================================================="
echo "🔤 ISL Fingerspelling Dataset Setup Pipeline"
echo "=========================================================="

mkdir -p "${TARGET_DIR}"

# Check if dataset is already extracted
EXISTING_COUNT=$(find "${TARGET_DIR}" -type f -name "*.jpg" 2>/dev/null | wc -l || echo 0)

if [ "${EXISTING_COUNT}" -ge 40000 ]; then
  echo "✅ Dataset already organized in ${TARGET_DIR} (${EXISTING_COUNT} images found)."
else
  # Check common download locations
  ARCHIVE_PATH="${1:-}"

  if [ -z "${ARCHIVE_PATH}" ]; then
    if [ -f "${HOME}/Downloads/archive.zip" ]; then
      ARCHIVE_PATH="${HOME}/Downloads/archive.zip"
    elif [ -f "${ROOT_DIR}/data/raw/archive.zip" ]; then
      ARCHIVE_PATH="${ROOT_DIR}/data/raw/archive.zip"
    fi
  fi

  if [ -n "${ARCHIVE_PATH}" ] && [ -f "${ARCHIVE_PATH}" ]; then
    echo "📦 Extracting archive from: ${ARCHIVE_PATH}..."
    unzip -q -o "${ARCHIVE_PATH}" -d "${TARGET_DIR}"

    # Flatten if nested under Indian/
    if [ -d "${TARGET_DIR}/Indian" ]; then
      echo "📂 Flattening nested Indian/ subdirectories..."
      mv "${TARGET_DIR}/Indian"/* "${TARGET_DIR}/"
      rmdir "${TARGET_DIR}/Indian"
    fi
    echo "✅ Extraction complete!"
  else
    echo "⚠️  archive.zip not found automatically."
    echo "Please download the dataset from Kaggle:"
    echo "   URL: https://www.kaggle.com/datasets/prathumarikeri/indian-sign-language-isl"
    echo "Or run with archive path: bash scripts/setup_fingerspelling_dataset.sh /path/to/archive.zip"
    exit 1
  fi
fi

# Generate dataset manifest
echo "📊 Generating dataset manifest..."
python3 "${ROOT_DIR}/ml/manifest_fingerspelling.py"

echo "=========================================================="
echo "🎉 Dataset Pipeline Ready in data/raw/fingerspelling/!"
echo "=========================================================="
