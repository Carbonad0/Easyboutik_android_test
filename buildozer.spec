[app]
# EasyBoutik Android v3.4
# Build depuis ce dossier avec : buildozer -v android debug

title = EASYBOUTIK
package.name = easyboutik
package.domain = org.easyboutik
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,txt,pdf
version = 3.4.0
requirements = python3,kivy,kivymd,plyer,reportlab,pyjnius
orientation = portrait
fullscreen = 0

# Sélection d'images sur Android 13+.
android.permissions = READ_MEDIA_IMAGES
android.api = 35
android.minapi = 23
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
