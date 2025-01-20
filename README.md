# Building From Source

The following runs the program using python:
```
pip install -r requirements.txt
python main.py
```

The following builds the program to your local machine:
```
pip install pyinstaller
pip install -r requirements.txt
```
```
pyinstaller TiinySwatch.spec
```
or
```
pyinstaller -n "TiinySwatch" main.py <options>
```

# Pre-Built Windows Binary

The file `TiinySwatch.exe` was pre-built for Windows 11 x86-64. Simply click to run it.