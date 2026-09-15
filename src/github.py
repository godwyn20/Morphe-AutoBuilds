import os
import re
import logging
from src import session


def _get_headers():
    headers = {}
    if "GITHUB_TOKEN" in os.environ:
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    return headers


def _find_release_for_version(repo: str, version: str):
    """
    Find the GitHub release corresponding to a specific version.
    This is primarily used for apps whose release assets do not contain
    the version in their filename, such as Brave's BraveMono assets.
    """
    if not version:
        return None

    response = session.get(
        f"https://api.github.com/repos/{repo}/releases",
        headers=_get_headers(),
        params={"per_page": 100},
    )

    if response.status_code != 200:
        response.raise_for_status()

    releases = response.json()
    normalized_version = version.lstrip("v")

    for release in releases:
        if release.get("prerelease"):
            continue

        tag_name = str(release.get("tag_name", "")).lstrip("v")
        release_name = str(release.get("name", "")).lstrip("v")

        if tag_name == normalized_version or release_name == normalized_version:
            return release

        for value in (tag_name, release_name):
            if re.search(
                rf"(?<![\d.]){re.escape(normalized_version)}"
                rf"(?![\d.])",
                value,
            ):
                return release

    return None


def get_latest_version(app_name: str, config: dict) -> str | None:
    repo = config.get("repo")
    tag = config.get("tag")

    if not repo or not tag:
        logging.error(f"Missing 'repo' or 'tag' in github config for {app_name}")
        return None

    if tag == "latest":
        url = f"https://api.github.com/repos/{repo}/releases/latest"
    else:
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"

    try:
        response = session.get(url, headers=_get_headers())

        if response.status_code == 200:
            data = response.json()

            versions = []

            for asset in data.get("assets", []):
                name = asset.get("name", "")

                m = re.search(r"-([\d\.]+)-", name)

                if m:
                    versions.append(m.group(1).strip("."))
                else:
                    m = re.search(r"([\d\.]+)", name)

                    if m:
                        versions.append(m.group(1).strip("."))

            if versions:
                versions.sort(
                    key=lambda x: [
                        int(p) for p in x.split(".") if p.isdigit()
                    ]
                )

                logging.info(
                    f"Latest version found on GitHub for {app_name}: "
                    f"{versions[-1]}"
                )

                return versions[-1]

        elif response.status_code == 404:
            logging.debug(f"GitHub release not found for {url}")
        else:
            response.raise_for_status()

    except Exception as e:
        logging.error(
            f"Failed to fetch GitHub release for {app_name}: {e}"
        )

    return None


def get_download_link(
    version: str,
    app_name: str,
    config: dict,
) -> str | None:
    repo = config.get("repo")
    tag = config.get("tag")

    if not repo or not tag:
        return None

    try:
        # If an asset pattern is configured, locate the release by the
        # requested app version first. This is required for assets such
        # as BraveMonoarm64.apk whose filename does not contain the version.
        if config.get("asset_pattern") and version:
            data = _find_release_for_version(repo, version)

            if not data:
                logging.warning(
                    f"Could not find GitHub release for {app_name} "
                    f"version {version}; will not use an unrelated release."
                )
                return None
        else:
            if tag == "latest":
                url = f"https://api.github.com/repos/{repo}/releases/latest"
            else:
                url = (
                    f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
                )

            response = session.get(
                url,
                headers=_get_headers(),
            )

            if response.status_code != 200:
                response.raise_for_status()

            data = response.json()

        if config.get("asset_pattern"):
            pattern = config["asset_pattern"].lower()

            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()

                if (
                    pattern in name
                    and name.endswith(
                        (".apk", ".apkm", ".xapk")
                    )
                ):
                    logging.info(
                        f"Found GitHub asset for {app_name} "
                        f"{version}: {asset.get('name')}"
                    )
                    return asset.get("browser_download_url")

            logging.warning(
                f"No GitHub asset matching '{config['asset_pattern']}' "
                f"found for {app_name} version {version}"
            )

            return None

        # Normal GitHub asset matching when no explicit pattern is used.
        arch = config.get("arch", "arm64-v8a").lower()

        for asset in data.get("assets", []):
            name = asset.get("name", "").lower()

            if (
                version.lower() in name
                and name.endswith(
                    (".apk", ".apkm", ".xapk")
                )
            ):
                if arch in ("all", "both") or arch in name:
                    logging.info(
                        f"Found GitHub download link for "
                        f"{app_name} {version}"
                    )
                    return asset.get("browser_download_url")

        # Fallback: version match without architecture requirement.
        for asset in data.get("assets", []):
            name = asset.get("name", "").lower()

            if (
                version.lower() in name
                and name.endswith(
                    (".apk", ".apkm", ".xapk")
                )
            ):
                logging.info(
                    f"Fallback arch: Found GitHub download link for "
                    f"{app_name} {version}"
                )
                return asset.get("browser_download_url")

    except Exception as e:
        logging.error(
            f"Failed to get GitHub download link for "
            f"{app_name}: {e}"
        )

    return None