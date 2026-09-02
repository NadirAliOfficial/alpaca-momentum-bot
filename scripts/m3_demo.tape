Output "m3-demo.mp4"

Set Shell "zsh"
Set FontSize 15
Set Width 1280
Set Height 820
Set Theme "Dracula"
Set TypingSpeed 30ms
Set Padding 20

Hide
Type "cd ~/code/alpaca-momentum-bot && source .venv/bin/activate && export PYTHONUNBUFFERED=1 && clear"
Enter
Sleep 1s
Show

Type "python -m scripts.m3_demo"
Enter
Sleep 12s

Type "pytest -p no:warnings --no-header -rN"
Enter
Sleep 10s

Type "exit"
Enter
Sleep 1s
