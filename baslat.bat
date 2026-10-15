@echo off
cd /d "%~dp0"

python main.py
if errorlevel 1 (
    echo.
    echo [BILGI] Uygulama baslatilamadi. Bagimliliklar kontrol ediliyor...
    python -m pip install -r requirements.txt
    echo Uygulama yeniden baslatiliyor...
    python main.py
    if errorlevel 1 (
        echo.
        echo [HATA] Bir sorun olustu.
        pause
    )
)
