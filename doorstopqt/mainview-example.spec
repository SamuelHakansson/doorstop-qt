# -*- mode: python ; coding: utf-8 -*-
# Create a copy of this file named mainview.spec and change the paths.
# Run this script by: pyinstaller mainview.spec (or mainview-example.spec).

block_cipher = None


a = Analysis(['mainview.py'],
             pathex=['path\\to\\project\\doorstop-qt\\doorstopqt'],
             binaries=[],
             datas=[
             ('C:\\Users\\USERNAME\\AppData\\Local\\Programs\\Python\\Python37-32\\Lib\\site-packages\\doorstop', 'doorstop'),
             ('C:\\Users\USERNAME\\AppData\\Local\\Programs\\Python\\Python37-32\\Lib\\site-packages\\mdx_include', 'mdx_include')
             ],
             hiddenimports=['mdx_outline'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='doorstop-qt',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon='C:\\Users\\USERNAME\\doorstop-fork\\doorstop-qt\\doorstopqt\\doorstop-logo\\ds-logo-new.ico')
