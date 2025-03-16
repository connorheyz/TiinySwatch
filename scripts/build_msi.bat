@echo off
echo Building TiinySwatch MSI installer...
python ../setup.py bdist_msi
echo Done! Check the dist directory for your MSI installer. 