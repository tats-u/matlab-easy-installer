$ErrorActionPreference = "Stop"
pyinstaller easy_install.py --onefile
if(Test-Path .\easy_install.exe) {
    Remove-Item .\easy_install.exe
}
Move-Item dist\easy_install.exe .
Remove-Item -Recurse build
Remove-Item -Recurse dist
remove-item easy_install.spec
