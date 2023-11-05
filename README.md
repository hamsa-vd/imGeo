# imGeo

- This is a desktop application built with tkinter
- You can provide your image and have your own date and geo imprinted on it

## Command to build the exe for windows

```console
python -m nuitka --standalone --disable-console --windows-icon-from-ico="C:\Users\Hamsa\Documents\coding\imGeo\assets\imGeo.ico" --include-module=babel.numbers  --enable-plugin=tk-inter imGeo.py
```
