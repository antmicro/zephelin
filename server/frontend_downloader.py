# Copyright (c) 2026 Analog Devices, Inc.
# Copyright (c) 2026 Antmicro <www.antmicro.com>
#
# SPDX-License-Identifier: Apache-2.0

"""
Provides functions for downloading the Zephelin Trace Viewer frontend from GitHub Pages.
"""

import io
import logging
import tempfile
import zipfile
from pathlib import Path

import requests

logger = logging.getLogger("Frontend Downloader")

GITHUB_PAGES_BRANCH = "gh-pages"
GITHUB_ZIP_URL = f"https://github.com/antmicro/zephelin-trace-viewer/archive/refs/heads/{GITHUB_PAGES_BRANCH}.zip"


def download_frontend() -> Path:
    """
    Downloads the Zephelin Trace Viewer frontend from GitHub Pages.

    The frontend is fetched as a single zip archive of the gh-pages branch,
    which is far more efficient than the previous approach of making dozens of
    individual API requests.

    Returns
    -------
    Path
        Path to the downloaded frontend directory.

    Raises
    ------
    RuntimeError
        If download or extraction fails.
    """
    output_dir = Path(tempfile.mkdtemp(prefix="zephelin-frontend-"))
    logger.info(f"Created temporary directory for frontend: {output_dir}")

    logger.info(f"Downloading frontend archive from {GITHUB_ZIP_URL}")

    try:
        response = requests.get(GITHUB_ZIP_URL, timeout=60)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            zip_file.extractall(output_dir)

        extracted_root = next(output_dir.iterdir())
        logger.info(f"Frontend downloaded and extracted to {extracted_root}")
        return extracted_root

    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download frontend: {e}") from e
    except (zipfile.BadZipFile, OSError) as e:
        raise RuntimeError(f"Failed to extract frontend archive: {e}") from e
