<div align="center">

# 🔧 Morphe Non-Root Builds

**Pre-built Morphe APKs for non-root Android devices.** 

Forked from [RookieEnough/Morphe-AutoBuilds](https://github.com/RookieEnough/Morphe-AutoBuilds).

[![Daily Build](https://img.shields.io/github/actions/workflow/status/godwyn20/Morphe-AutoBuilds/patch.yml?label=Daily%20Build\&style=for-the-badge)](https://github.com/godwyn20/Morphe-AutoBuilds/actions/workflows/patch.yml)

[![Latest Release](https://img.shields.io/github/v/release/godwyn20/Morphe-AutoBuilds?style=for-the-badge\&label=Latest%20Release)](https://github.com/godwyn20/Morphe-AutoBuilds/releases/latest)

</div>

---

## 📥 Download

👉 **[Download the Latest Release](https://github.com/godwyn20/Morphe-AutoBuilds/releases/latest)**

Choose the APK for the app you want to install.

Most modern Android phones use **arm64-v8a**.

> The builds in this repository are automatically generated from the configured app versions and Morphe patches.

---

## 📱 Available Apps

| App               | Architecture |
| :---------------- | :----------: |
| 1.1.1.1           |  `arm64-v8a` |
| Adobe Acrobat     |  `arm64-v8a` |
| Brave             |  `arm64-v8a` |
| CamScanner        |  `arm64-v8a` |
| CapCut            |  `arm64-v8a` |
| Microsoft Excel   |  `arm64-v8a` |
| Gboard            |  `arm64-v8a` |
| Google Photos     |  `arm64-v8a` |
| Hidden Settings   |  `universal` |
| Hill Climb Racing |  `arm64-v8a` |
| Jetpack Joyride   |  `arm64-v8a` |
| Microsoft Edge    |  `arm64-v8a` |
| Proton VPN        |  `arm64-v8a` |
| SD Maid SE        |  `arm64-v8a` |
| Speedtest         |  `arm64-v8a` |
| Strava            |  `arm64-v8a` |
| TikTok            |  `universal` |
| Traffic Rider     |  `arm64-v8a` |
| Vivaldi           |  `arm64-v8a` |
| Windy             |  `arm64-v8a` |
| Microsoft Word    |  `arm64-v8a` |
| YouTube           |  `universal` |
| YouTube Music     |  `arm64-v8a` |

---

## 📲 How to Install

### 1. Download your app

Go to the **[Latest Release](https://github.com/godwyn20/Morphe-AutoBuilds/releases/latest)** and download the APK for the app you want.

### 2. Allow APK installation

If Android asks for permission, allow the browser or file manager you used to download the APK to **install unknown apps**.

You only need to do this once.

### 3. Install the APK

Open the downloaded APK and install it.

If you already have the same patched app installed, Android should normally allow you to install the newer build over it.

> If Android says the app cannot be installed because of a signature or package conflict, you may need to uninstall the existing version first. **Uninstalling an app can remove its local data.**

### 4. Open the app

After installation, open the app and complete its normal setup.

---

## ▶️ YouTube, YouTube Music & Google Photos

These apps require **MicroG-RE** for sign-in and Google services.

### First-time installation

1. Download **[MicroG-RE](https://github.com/MorpheApp/MicroG-RE/releases/latest)**.
2. Install MicroG-RE.
3. Download the patched YouTube, YouTube Music, or Google Photos APK from the **[Latest Release](https://github.com/godwyn20/Morphe-AutoBuilds/releases/latest)**.
4. Install the patched app.
5. Open the app and sign in when prompted.

> You only need to install MicroG-RE once. The same MicroG-RE installation can be used by supported patched Google apps.

<details>
<summary>⚙️ Optional: PotHelper</summary>

**PotHelper** is an optional component for **YouTube and YouTube Music** configurations that use the external PoToken provider.

You do **not** need to install it for every YouTube or YouTube Music installation.

If your configuration specifically requires it:

👉 [**Download PotHelper**](https://github.com/MorpheApp/PotHelper/releases/latest)

PotHelper is an experimental/optional component and may not work in every situation or on every device.

</details>

---

## 🔄 Updates

Builds are automatically checked and generated on a regular schedule.

When a newer compatible app version and patch combination is available, a new build can be published to the **Latest Release**.

### Updating an installed app

1. Download the newer APK from the **[Latest Release](https://github.com/godwyn20/Morphe-AutoBuilds/releases/latest)**.
2. Install it over your existing patched version.
3. Open the updated app.

You normally do **not** need to uninstall the old version first.

> If Android refuses the update because the package or signature is different, you may need to uninstall the previous installation. This can remove local app data.

---

## 🧩 Patch Sources

The APKs in this repository use Morphe patches from several community-maintained sources.

| Author        | Patch Repository                                                                  |
| :------------ | :-------------------------------------------------------------------------------- |
| MorpheApp     | [morphe-patches](https://github.com/MorpheApp/morphe-patches)                     |
| kveld9        | [kveld-morphe-patches](https://github.com/kveld9/kveld-morphe-patches)            |
| jasonwu1994   | [Gboard-patches](https://github.com/jasonwu1994/Gboard-patches)                   |
| quantavil     | [edge-morphe-patches](https://github.com/quantavil/edge-morphe-patches)           |
| hoo-dles      | [morphe-patches](https://github.com/hoo-dles/morphe-patches)                      |
| byehi98       | [okish-morphe-patches](https://github.com/byehi98/okish-morphe-patches)           |
| arandomhooman | [hoomans-morphe-patches](https://github.com/arandomhooman/hoomans-morphe-patches) |
| rushiranpise  | [morphe-patches](https://github.com/rushiranpise/morphe-patches)                  |
| kiraio-moe    | [Lain-Patches](https://github.com/kiraio-moe/Lain-Patches)                        |
| riky-dev      | [morphe-patches](https://github.com/riky-dev/morphe-patches)                      |
| RookieEnough  | [De-Vanced](https://github.com/RookieEnough/De-Vanced)                            |

> Patch repositories are maintained independently from this project. Their supported apps and versions can change over time.

---

## ⚠️ Disclaimer

This project is not affiliated with Morphe or the developers of the listed applications.

Use these builds at your own discretion. Apps and patches may change or stop working at any time.
