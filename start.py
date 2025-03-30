import time
import pyautogui

def executar_comandos():
    # Delay inicial
    time.sleep(0.537)  # 537ms
    
    # Mover o mouse para a posição (439, 742)
    pyautogui.moveTo(439, 742)
    
    # Garantir que o mouse chegou à posição antes de clicar
    time.sleep(0.092)  # 92ms para o tempo de espera após o movimento
    
    # Pressionar o botão esquerdo do mouse
    pyautogui.mouseDown()
    time.sleep(0.092)  # 92ms de clique
    
    # Soltar o botão esquerdo do mouse
    pyautogui.mouseUp()
    time.sleep(1.290)  # 1290ms de espera após o clique
    
    # Delay extra
    time.sleep(0.257)  # 257ms
    
    # Mover o mouse para a mesma posição novamente (simulação)
    pyautogui.moveTo(439, 742)

# Executar a função
executar_comandos()
