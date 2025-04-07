from cx_Freeze import setup, Executable

company_name = "Tiiny"
product_name = "TiinySwatch"

bdist_msi_options = {
    "summary_data": {
        "author": "Connor Hayes",
        "comments": "Tiiny Swatch",
        "keywords": "PySide6",
    },
    # Icon for the installer
    "install_icon": "assets\\icons\\TiinySwatch.ico",
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
          "src/app.py",
          shortcut_name="Tiiny Swatch",
          shortcut_dir=["DesktopFolder", "StartMenuFolder"],
          base="Win32GUI",
          icon="assets/icons/TiinySwatch.ico"
      )
      ]
      )
