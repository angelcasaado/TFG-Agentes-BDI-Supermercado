@echo off
REM — Sitúate en la carpeta que contiene “codigo_modulado”
cd /d "C:\Users\acasa\Desktop\TFG"

REM — Lanza main.py como módulo del paquete
python -m src.main

REM — Mantén la ventana abierta para ver logs o errores
pause