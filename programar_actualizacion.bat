@echo off
echo ========================================
echo ACTUALIZACION AUTOMATICA PREMIER LEAGUE
echo ========================================
cd /d C:\Users\DIEGO Y JOSIE\Desktop\PREMIER_PREDICTOR
call venv\Scripts\activate
python actualizar_datos.py
python predictor_cli.py
echo.
echo Actualizacion completada en %date% %time%
echo ========================================
pause