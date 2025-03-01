from cx_Freeze import setup, Executable
import sys
import os

company_name = "Tiiny"
product_name = "TiinySwatch"

bdist_msi_options = {
    "summary_data": {
        "author": "Connor Hayes",
        "comments": "Tiiny Swatch",
        "keywords": "PySide6",
    },
    # Icon for the installer
    "install_icon": "TiinySwatch.ico",
    "initial_target_dir": rf"C:\\Program Files\\{company_name}\\{product_name}",
    "all_users": True
}


setup(name="TiinySwatch",
      version="1.0",
      description="A one stop shop quick use color utility.",
      options={
          "bdist_msi": bdist_msi_options,
      },
      executables=[Executable(
          "app.py",
          shortcut_name="Tiiny Swatch",
          shortcut_dir="DesktopFolder",
          base="Win32GUI",
          icon="TiinySwatch.ico"
      )
      ]
      )
