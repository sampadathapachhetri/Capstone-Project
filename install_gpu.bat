@echo off
echo Installing GPU version...
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu132
echo Done!
pause