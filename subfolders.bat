@echo off
set "output_file=subfolders.csv"
echo Subfolder Name > %output_file%
for /d %%i in (*) do echo %%i >> %output_file%
echo 子資料夾名稱已儲存至 %output_file%