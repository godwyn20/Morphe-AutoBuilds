import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from sys import exit
from os import getenv

from src import (
    r2,
    utils,
    release,
    downloader,
)


def _should_retry_with_older_version(output: str | None) -> bool:
    """Detect common patterns that indicate the chosen app version is not
    actually compatible with the selected patches."""
    if not output:
        return False

    t = output.lower()

    return (
        "failed to match the fingerprint" in t
        or "patch.patchexception" in t
        or ("fingerprint" in t and "failed" in t)
        or "patching aborted" in t
    )


def run_build(
    app_name: str,
    source: str,
    arch: str = "universal",
) -> str | None:
    """Build APK for a specific architecture."""

    # ---------------------------------------------------------
    # DOWNLOAD PATCH RESOURCES
    # ---------------------------------------------------------

    download_files, name, patch_repo = (
        downloader.download_required(source)
    )

    logging.info(
        f"📦 Downloaded {len(download_files)} files for {source}:"
    )

    for file in download_files:
        logging.info(
            f"  - {file.name} ({file.stat().st_size} bytes)"
        )

    if patch_repo:
        logging.info(
            f"🎯 Patch repository: {patch_repo}"
        )

    # ---------------------------------------------------------
    # DETECT PATCH SOURCE TYPE
    # ---------------------------------------------------------

    is_morphe = False
    is_revanced = False

    for file in download_files:
        if "morphe-cli" in file.name.lower():
            is_morphe = True
            break

        elif "revanced-cli" in file.name.lower():
            is_revanced = True
            break

    # If CLI name did not identify the source, inspect patch files.
    if not is_morphe and not is_revanced:
        for file in download_files:
            if file.suffix.lower() == ".mpp":
                is_morphe = True
                break

            elif (
                file.suffix.lower() in [".rvp", ".jar"]
                and "patches" in file.name.lower()
            ):
                is_revanced = True
                break

    # Final fallback based on source name.
    if not is_morphe and not is_revanced:
        is_morphe = (
            "morphe" in source.lower()
            or "custom" in source.lower()
        )
        is_revanced = not is_morphe

    logging.info(
        f"🔍 Detected: "
        f"{'Morphe' if is_morphe else 'ReVanced'} source type"
    )

    # ---------------------------------------------------------
    # FIND CLI AND PATCH FILE
    # ---------------------------------------------------------

    if is_morphe:
        cli = utils.find_file(
            download_files,
            contains="morphe-cli",
            suffix=".jar",
            exclude=["dev"],
        )

        if not cli:
            cli = utils.find_file(
                download_files,
                contains="morphe",
                suffix=".jar",
            )

        if not cli:
            cli = utils.find_file(
                download_files,
                suffix=".jar",
            )

        patches = utils.find_file(
            download_files,
            contains="patches",
            suffix=".mpp",
        )

        if not patches:
            patches = utils.find_file(
                download_files,
                suffix=".mpp",
            )

    else:
        cli = utils.find_file(
            download_files,
            contains="revanced-cli",
            suffix=".jar",
        )

        patches = utils.find_file(
            download_files,
            contains="patches",
            suffix=".rvp",
        )

        if not patches:
            patches = utils.find_file(
                download_files,
                contains="patches",
                suffix=".jar",
            )

    # ---------------------------------------------------------
    # VALIDATE PATCH TOOLS
    # ---------------------------------------------------------

    if not cli:
        logging.error(
            f"❌ CLI not found for source: {source}"
        )
        logging.error(
            f"Available files: {[f.name for f in download_files]}"
        )
        return None

    if not patches:
        logging.error(
            f"❌ Patches not found for source: {source}"
        )
        logging.error(
            f"Available files: {[f.name for f in download_files]}"
        )
        return None

    logging.info(
        f"✅ Using CLI: {cli.name}"
    )

    logging.info(
        f"✅ Using patches: {patches.name}"
    )

    # ---------------------------------------------------------
    # DOWNLOAD SOURCE PRIORITY
    # ---------------------------------------------------------
    #
    # If an explicit GitHub app config exists, try GitHub first.
    #
    # This is especially important for Brave because its config
    # specifies:
    #
    #   repo: brave/brave-browser
    #   asset_pattern: bravemonoarm64
    #
    # Other apps retain the normal fallback order.
    # ---------------------------------------------------------

    download_methods = []

    github_config = (
        Path("apps")
        / "github"
        / f"{app_name}.json"
    )

    if github_config.exists():
        logging.info(
            f"⭐ Explicit GitHub app config found for "
            f"{app_name}; trying GitHub first."
        )

        download_methods.append(
            downloader.download_github
        )

    download_methods.extend(
        [
            downloader.download_apkmirror,
            downloader.download_aptoide,
            downloader.download_uptodown,
            downloader.download_apkpure,
            downloader.download_apkcombo,
        ]
    )

    # ---------------------------------------------------------
    # DOWNLOAD APP APK
    # ---------------------------------------------------------

    input_apk = None
    version = None
    candidates: list[str] = []
    used_method = None

    for method in download_methods:
        input_apk, version, candidates = method(
            app_name,
            str(cli),
            str(patches),
            arch,
            patch_repo=patch_repo,
        )

        if input_apk:
            used_method = method
            break

    if (
        input_apk is None
        or not used_method
        or not version
    ):
        logging.error(
            f"❌ Failed to download APK for {app_name}"
        )
        logging.error(
            "All download sources failed. Skipping this app."
        )
        return None

    # ---------------------------------------------------------
    # VERSION RETRY LIST
    # ---------------------------------------------------------

    versions_to_try: list[str] = [version]

    if candidates and version in candidates:
        versions_to_try += [
            v
            for v in candidates
            if v != version
        ]

    # ---------------------------------------------------------
    # PATCH OPTIONS
    # ---------------------------------------------------------

    exclude_patches = []
    include_patches = []
    option_args = []

    patches_path = (
        Path("patches")
        / f"{app_name}-{source}.txt"
    )

    if patches_path.exists():
        with patches_path.open(
            "r",
            encoding="utf-8",
        ) as patches_file:

            for line in patches_file:
                line = line.strip()

                if not line:
                    continue

                if line.startswith("-"):
                    exclude_patches.extend(
                        [
                            "-d",
                            line[1:].strip(),
                        ]
                    )

                elif line.startswith("+"):
                    include_patches.extend(
                        [
                            "-e",
                            line[1:].strip(),
                        ]
                    )

                elif line.startswith("="):
                    option_args.append(
                        f"-O{line[1:].strip()}"
                    )

    # ---------------------------------------------------------
    # TRY PATCHING
    # ---------------------------------------------------------

    for attempt_idx, ver in enumerate(
        versions_to_try
    ):

        if attempt_idx > 0:
            logging.warning(
                f"Retrying {app_name}/{source}/{arch} "
                f"with older version {ver} due to "
                f"patch failure..."
            )

            try:
                input_apk.unlink(
                    missing_ok=True
                )
            except Exception:
                pass

            input_apk, version, _ = used_method(
                app_name,
                str(cli),
                str(patches),
                arch,
                override_version=ver,
                patch_repo=patch_repo,
            )

            if input_apk is None:
                continue

            version = ver

        # -----------------------------------------------------
        # NORMALIZE / MERGE INPUT
        # -----------------------------------------------------

        if input_apk.suffix.lower() != ".apk":

            is_bundle = False

            try:
                import zipfile

                if zipfile.is_zipfile(input_apk):
                    with zipfile.ZipFile(
                        input_apk,
                        "r",
                    ) as z:
                        namelist = z.namelist()

                        has_split_apks = any(
                            n.endswith(".apk")
                            for n in namelist
                        )

                        is_bundle = (
                            has_split_apks
                            or input_apk.suffix.lower()
                            in [
                                ".apkm",
                                ".xapk",
                                ".apks",
                                ".zip",
                            ]
                        )

            except Exception as e:
                logging.debug(
                    f"Zip inspection failed for "
                    f"{input_apk}: {e}"
                )

            target_apk = input_apk.with_name(
                f"{input_apk.stem}.apk"
            )

            if is_bundle:
                logging.info(
                    f"Input file is a bundle "
                    f"({input_apk.name}), "
                    f"using APKEditor to merge"
                )

                apk_editor = (
                    downloader.download_apkeditor()
                )

                merged_apk = (
                    input_apk.with_suffix(".apk")
                )

                merged_apk.unlink(
                    missing_ok=True
                )

                try:
                    utils.run_process(
                        [
                            "java",
                            "-jar",
                            str(apk_editor),
                            "m",
                            "-f",
                            "-i",
                            str(input_apk),
                            "-o",
                            str(merged_apk),
                        ],
                        silent=True,
                        check=True,
                    )

                    input_apk.unlink(
                        missing_ok=True
                    )

                    input_apk = merged_apk

                except Exception as e:
                    logging.warning(
                        f"APKEditor merge failed "
                        f"({e}); checking if file can "
                        f"be used as standalone APK"
                    )

                    if input_apk.exists():
                        target_apk.unlink(
                            missing_ok=True
                        )

                        os.replace(
                            input_apk,
                            target_apk,
                        )

                        input_apk = target_apk

            else:
                logging.info(
                    f"Normalizing standalone APK "
                    f"filename to {target_apk.name}"
                )

                if input_apk != target_apk:
                    target_apk.unlink(
                        missing_ok=True
                    )

                    os.replace(
                        input_apk,
                        target_apk,
                    )

                    input_apk = target_apk

            if not input_apk.exists():
                logging.error(
                    "Processed APK file not found"
                )
                raise RuntimeError(
                    "Processed APK file not found"
                )

            # Remove APKMirror-style build numbers such as:
            #   app(1575420).apk
            #   app-1575420_name.apk
            clean_name = re.sub(
                r"\(\d+\)",
                "",
                input_apk.name,
            )

            clean_name = re.sub(
                r"-\d{6,}_",
                "_",
                clean_name,
            )

            if clean_name != input_apk.name:
                clean_apk = (
                    input_apk.with_name(clean_name)
                )

                clean_apk.unlink(
                    missing_ok=True
                )

                os.replace(
                    input_apk,
                    clean_apk,
                )

                input_apk = clean_apk

            logging.info(
                f"Normalized APK file: {input_apk}"
            )

        # -----------------------------------------------------
        # ARCHITECTURE PROCESSING
        # -----------------------------------------------------

        if arch != "universal":
            logging.info(
                f"Processing APK for "
                f"{arch} architecture..."
            )

            if arch == "arm64-v8a":
                utils.strip_zip_entries(
                    input_apk,
                    [
                        "lib/x86/*",
                        "lib/x86_64/*",
                        "lib/armeabi-v7a/*",
                    ],
                )

            elif arch == "armeabi-v7a":
                utils.strip_zip_entries(
                    input_apk,
                    [
                        "lib/x86/*",
                        "lib/x86_64/*",
                        "lib/arm64-v8a/*",
                    ],
                )

        else:
            utils.strip_zip_entries(
                input_apk,
                [
                    "lib/x86/*",
                    "lib/x86_64/*",
                ],
            )

        # -----------------------------------------------------
        # APK INTEGRITY
        # -----------------------------------------------------

        logging.info(
            "Checking APK integrity..."
        )

        if not utils.check_apk_integrity(
            input_apk
        ):
            logging.warning(
                "APK integrity check failed; "
                "attempting repair with zip -FF "
                "if available"
            )

            if shutil.which("zip"):
                fixed_apk = Path(
                    f"{app_name}-fixed-v{version}.apk"
                )

                subprocess.run(
                    [
                        "zip",
                        "-FF",
                        str(input_apk),
                        "--out",
                        str(fixed_apk),
                    ],
                    check=False,
                    capture_output=True,
                )

                if (
                    fixed_apk.exists()
                    and fixed_apk.stat().st_size > 0
                ):
                    input_apk.unlink(
                        missing_ok=True
                    )

                    fixed_apk.rename(
                        input_apk
                    )

                    logging.info(
                        "APK fixed successfully"
                    )

                else:
                    logging.warning(
                        "Repair produced no usable "
                        "file; keeping original APK"
                    )

            else:
                logging.warning(
                    "zip command not available "
                    "for repair; proceeding with "
                    "current APK"
                )

        else:
            logging.info(
                "APK integrity OK; no repair needed"
            )

        # -----------------------------------------------------
        # PATCH
        # -----------------------------------------------------

        output_apk = Path(
            f"{app_name}-{arch}-patch-v{version}.apk"
        )

        try:
            if is_morphe:
                logging.info(
                    "🔧 Using Morphe patching system..."
                )

                morphe_cmd = [
                    "java",
                    "-jar",
                    str(cli),
                    "patch",
                    "--patches",
                    str(patches),
                    "--out",
                    str(output_apk),
                    str(input_apk),
                    *exclude_patches,
                    *option_args,
                    *include_patches,
                ]

                utils.run_process(
                    morphe_cmd,
                    capture=True,
                    stream=True,
                )

            else:
                logging.info(
                    "🔧 Using ReVanced patching system..."
                )

                cli_name = (
                    Path(cli)
                    .name
                    .lower()
                )

                is_revanced_v6_or_newer = (
                    "revanced-cli-6" in cli_name
                    or "revanced-cli-7" in cli_name
                    or "revanced-cli-8" in cli_name
                )

                if is_revanced_v6_or_newer:
                    utils.run_process(
                        [
                            "java",
                            "-jar",
                            str(cli),
                            "patch",
                            "-p",
                            str(patches),
                            "-b",
                            "--out",
                            str(output_apk),
                            str(input_apk),
                            *exclude_patches,
                            *option_args,
                            *include_patches,
                        ],
                        capture=True,
                        stream=True,
                    )

                else:
                    utils.run_process(
                        [
                            "java",
                            "-jar",
                            str(cli),
                            "patch",
                            "--patches",
                            str(patches),
                            "--out",
                            str(output_apk),
                            str(input_apk),
                            *exclude_patches,
                            *option_args,
                            *include_patches,
                        ],
                        capture=True,
                        stream=True,
                    )

        except subprocess.CalledProcessError as e:
            input_apk.unlink(
                missing_ok=True
            )

            output_apk.unlink(
                missing_ok=True
            )

            if (
                attempt_idx
                < len(versions_to_try) - 1
                and _should_retry_with_older_version(
                    getattr(e, "output", None)
                )
            ):
                continue

            raise

        # -----------------------------------------------------
        # PATCH SUCCESS
        # -----------------------------------------------------

        input_apk.unlink(
            missing_ok=True
        )

        signed_apk = Path(
            f"{app_name}-{arch}-{name}-v{version}.apk"
        )

        apksigner = utils.find_apksigner()

        if not apksigner:
            raise RuntimeError(
                "apksigner not found"
            )

        try:
            utils.run_process(
                [
                    str(apksigner),
                    "sign",
                    "--verbose",
                    "--ks",
                    "keystore/public.jks",
                    "--ks-pass",
                    "pass:public",
                    "--key-pass",
                    "pass:public",
                    "--ks-key-alias",
                    "public",
                    "--in",
                    str(output_apk),
                    "--out",
                    str(signed_apk),
                ],
                capture=True,
                stream=True,
            )

        except Exception as e:
            logging.warning(
                f"Standard signing failed: {e}"
            )

            logging.info(
                "Trying alternative signing method..."
            )

            utils.run_process(
                [
                    str(apksigner),
                    "sign",
                    "--verbose",
                    "--min-sdk-version",
                    "21",
                    "--ks",
                    "keystore/public.jks",
                    "--ks-pass",
                    "pass:public",
                    "--key-pass",
                    "pass:public",
                    "--ks-key-alias",
                    "public",
                    "--in",
                    str(output_apk),
                    "--out",
                    str(signed_apk),
                ],
                capture=True,
                stream=True,
            )

        output_apk.unlink(
            missing_ok=True
        )

        print(
            f"✅ APK built: {signed_apk.name}"
        )

        return str(signed_apk)

    return None


def main():
    app_name = getenv("APP_NAME")
    source = getenv("SOURCE")

    if not app_name or not source:
        logging.error(
            "APP_NAME and SOURCE environment "
            "variables must be set"
        )
        exit(1)

    # ---------------------------------------------------------
    # READ ARCH CONFIG
    # ---------------------------------------------------------

    arch_config_path = Path(
        "arch-config.json"
    )

    if arch_config_path.exists():
        with arch_config_path.open(
            encoding="utf-8"
        ) as f:
            arch_config = json.load(f)

        # The workflow provides ARCH.
        # If ARCH is absent, fall back to arch-config.json.
        arches = [
            (getenv("ARCH") or "universal").strip()
        ]

        if not getenv("ARCH"):
            for config in arch_config:
                if (
                    config["app_name"] == app_name
                    and config["source"] == source
                ):
                    arches = config["arches"]
                    break

        # -----------------------------------------------------
        # BUILD EACH ARCHITECTURE
        # -----------------------------------------------------

        built_apks = []

        for arch in arches:
            logging.info(
                f"🔨 Building {app_name} "
                f"for {arch} architecture..."
            )

            apk_path = run_build(
                app_name,
                source,
                arch,
            )

            if apk_path:
                built_apks.append(
                    apk_path
                )

                print(
                    f"✅ Built {arch} version: "
                    f"{Path(apk_path).name}"
                )

        # -----------------------------------------------------
        # SUMMARY
        # -----------------------------------------------------

        print(
            f"\n🎯 Built {len(built_apks)} APK(s) "
            f"for {app_name}:"
        )

        for apk in built_apks:
            print(
                f"  📱 {Path(apk).name}"
            )

    else:
        logging.warning(
            "arch-config.json not found, "
            "building universal only"
        )

        apk_path = run_build(
            app_name,
            source,
            "universal",
        )

        if apk_path:
            print(
                f"🎯 Final APK path: {apk_path}"
            )


if __name__ == "__main__":
    main()