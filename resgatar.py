import pyautogui
import time
import subprocess
import sys
import os

def resgatar():
    """Executa a sequência de resgate no jogo."""
    print("Executando resgate...")
    time.sleep(29 / 1000.0)  # Pequeno delay
    pyautogui.moveTo(1073, 837)
    time.sleep(19 / 1000.0)

    # Clica no botão
    pyautogui.mouseDown()
    time.sleep(82 / 1000.0)  
    pyautogui.mouseUp()
    time.sleep(98 / 1000.0)

    # Movimento de mouse final
    pyautogui.moveTo(1073, 837)
    time.sleep(672 / 1000.0)
    print("Resgate concluído!")

if __name__ == "__main__":
    resgatar()

    # Aguarda 60 segundos antes de reiniciar o script principal
    print("Aguardando 60 segundos para reiniciar o jogo...")
    time.sleep(60)

    # Obtém o caminho completo do script.py
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "script.py")

    print("Reiniciando o ciclo automaticamente...")
    subprocess.Popen(['python', script_path, "auto"])
