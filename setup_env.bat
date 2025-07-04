@echo off
REM 检查conda是否安装
where conda >nul 2>nul
if errorlevel 1 (
    echo 请先安装 Anaconda 或 Miniconda 并确保 conda 命令可用。
    pause
    exit /b 1
)

REM 创建环境
echo 正在创建/更新conda环境 ai-kefu ...
conda env update -f environment.yml

REM 激活环境
echo.
echo 环境创建完成。请运行以下命令激活环境：
echo.
echo     conda activate ai-kefu
echo.
pause
