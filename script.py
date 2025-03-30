# deixar a tela em 1360 x 768

import time
import subprocess
import sys  # Importando sys
from pynput.keyboard import Key, Listener

script_active = False  

def on_press(key):
    global script_active
    if key == Key.f8:
        if not script_active:
            script_active = True
            print("Iniciando start.py...")
            subprocess.Popen(['python', 'start.py'])

            time.sleep(15)
            print("Iniciando bot.py...")
            subprocess.Popen(['python', 'bot.py'])
        else:
            print("Os scripts já foram iniciados!")

def main():
    print("Pressione F8 para iniciar os scripts.")
    with Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        print("Reiniciado automaticamente pelo resgatar.py...")
        subprocess.Popen(['python', 'start.py'])
        time.sleep(15)
        subprocess.Popen(['python', 'bot.py'])
    else:
        main()
