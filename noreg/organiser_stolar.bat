@echo off
chcp 65001 >nul
title Organiser stolar - noreg
cd /d "%~dp0"

:loop
echo.
echo  ======================================
echo  Organiserer stolar med 3D-modellar
echo  ======================================
echo.

set /a count=0

for %%G in (*.glb) do call :moveglb "%%G"

if %count%==0 (
    echo   Ingen nye GLB-filer.
) else (
    echo   Flytta %count% filer.
)

echo.
echo  Trykk ENTER for aa koyre igjen...
pause >nul
cls
goto loop

:moveglb
set "glbfile=%~1"
set "glbname=%~n1"
for /f "tokens=1 delims=_" %%I in ("%glbname%") do set "objid=%%I"
if not exist "%objid%\" mkdir "%objid%"
echo   + %objid%\%~nx1
move "%glbfile%" "%objid%\" >nul 2>nul
set /a count+=1
for %%J in (%objid%_*.jpg) do call :movejpg "%%J"
goto :eof

:movejpg
echo     %~nx1
move "%~1" "%objid%\" >nul 2>nul
set /a count+=1
goto :eof
