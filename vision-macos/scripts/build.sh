#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="$ROOT/build/Cat Vision.app"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$ROOT/vendor/uvc-util/LICENSE" "$APP/Contents/Resources/uvc-util-LICENSE.txt"
clang -w -mmacosx-version-min=14.0 -o "$APP/Contents/MacOS/uvc-util" -framework IOKit -framework Foundation "$ROOT/vendor/uvc-util/uvc-util.m" "$ROOT/vendor/uvc-util/UVCController.m" "$ROOT/vendor/uvc-util/UVCType.m" "$ROOT/vendor/uvc-util/UVCValue.m"
clang -w -mmacosx-version-min=14.0 -I "$ROOT/vendor/uvc-util" -o "$APP/Contents/MacOS/c922-led" -framework IOKit -framework Foundation "$ROOT/Sources/C922LED.m" "$ROOT/vendor/uvc-util/UVCController.m" "$ROOT/vendor/uvc-util/UVCType.m" "$ROOT/vendor/uvc-util/UVCValue.m"
ARCH="$(uname -m)"
swiftc -target "$ARCH-apple-macosx14.0" -sdk "$(xcrun --show-sdk-path)" -swift-version 5 -O -parse-as-library "$ROOT/Sources/Geometry.swift" "$ROOT/Sources/CameraModel.swift" "$ROOT/Sources/App.swift" -o "$APP/Contents/MacOS/CatVision" -framework SwiftUI -framework AppKit -framework AVFoundation -framework Vision -framework CoreImage
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>CFBundleName</key><string>Cat Vision</string>
<key>CFBundleDisplayName</key><string>Cat Vision</string>
<key>CFBundleIdentifier</key><string>world.livinginacat.vision</string>
<key>CFBundleExecutable</key><string>CatVision</string>
<key>CFBundlePackageType</key><string>APPL</string>
<key>CFBundleShortVersionString</key><string>0.1.0</string>
<key>NSCameraUsageDescription</key><string>Cat Vision usa la cámara para detectar la pantalla del teléfono y mostrar un cursor virtual.</string>
<key>LSMinimumSystemVersion</key><string>14.0</string>
<key>NSHighResolutionCapable</key><true/>
</dict></plist>
PLIST
codesign --force --sign - "$APP" >/dev/null
printf 'App lista: %s\n' "$APP"
