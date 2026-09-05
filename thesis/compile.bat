@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo Kompilacja Pracy Magisterskiej LaTeX: ADK
echo =======================================================

cd /d "%~dp0"

where tectonic >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Znaleziono kompilator Tectonic. Rozpoczynanie kompilacji...
    tectonic main.tex
    if %errorlevel% equ 0 (
        echo [SUKCES] Pomyslnie wygenerowano plik main.pdf!
    ) else (
        echo [BLAD] Kompilacja Tectonic zakonczona niepowodzeniem.
    )
    goto end
)

where latexmk >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Znaleziono latexmk. Rozpoczynanie pelnego cyklu...
    latexmk -pdf -interaction=nonstopmode main.tex
    if %errorlevel% equ 0 (
        echo [SUKCES] Pomyslnie wygenerowano plik main.pdf!
    )
    goto end
)

where pdflatex >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Znaleziono pdflatex. Uruchamianie procedury (pdflatex + biber)...
    pdflatex -interaction=nonstopmode main.tex
    biber main
    pdflatex -interaction=nonstopmode main.tex
    pdflatex -interaction=nonstopmode main.tex
    echo [SUKCES] Procedura zakonczona.
    goto end
)

echo [OSTRZEZENIE] Nie wykryto lokalnego kompilatora LaTeX (Tectonic / latexmk / pdflatex).
echo.
echo Mozesz skompilowac prace na dwa sposoby:
echo 1. W VS Code wciskajac Ctrl+Alt+B (jesli uzywasz LaTeX Workshop)
echo 2. Instalujac lekki (30 MB) kompilator Tectonic wpisujac w terminalu:
echo    winget install Tectonic.Tectonic
echo.
pause

:end
endlocal

