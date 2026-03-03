@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" amd64
set CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.1
echo Building custom_rasterizer...
cd /d C:\Users\Shadow\Desktop\stolar-db\Hunyuan3D-2\hy3dgen\texgen\custom_rasterizer
C:\Users\Shadow\Desktop\stolar-db\Hunyuan3D-2\venv\Scripts\python.exe setup.py install
if errorlevel 1 (
    echo FAILED: custom_rasterizer
    exit /b 1
)
echo Building differentiable_renderer...
cd /d C:\Users\Shadow\Desktop\stolar-db\Hunyuan3D-2\hy3dgen\texgen\differentiable_renderer
C:\Users\Shadow\Desktop\stolar-db\Hunyuan3D-2\venv\Scripts\python.exe setup.py install
if errorlevel 1 (
    echo FAILED: differentiable_renderer
    exit /b 1
)
echo ALL DONE
