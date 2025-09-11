@echo off
cd /d %~dp0
call .venv\Scripts\activate
python main.py
python kpi.py > logs\kpi_%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%.log 2>&1
