@echo off
echo Activating cellpose environment and launching app...
call "%USERPROFILE%\miniconda3\Scripts\activate.bat" cellpose_env
streamlit run app_keyence_10x.py
pause
