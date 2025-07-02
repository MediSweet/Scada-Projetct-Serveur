
@echo off
:Titre
echo Execution du programme...
start "" "C:\Users\Administrateur\PycharmProjects\PythonProject\dist\main.exe"
timeout /t 3600 /nobreak >nul
taskkill /im main.exe /f
goto Titre