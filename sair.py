import time
import pyautogui
import pygetwindow as gw
import subprocess  # Para executar o script resgatar.py

# Função para focar a janela do Fortnite
def focus_fortnite():
    try:
        window = gw.getWindowsWithTitle('Fortnite')[0]  # Procura pela janela do Fortnite
        if window:
            window.activate()  # Ativa a janela
            print("Fortnite focado com sucesso!")
            time.sleep(1)  # Espera 1 segundo para garantir que a janela foi ativada
    except IndexError:
        print("Não foi possível encontrar a janela do Fortnite!")

# Função para simular as ações
def execute_sair():
    print("Iniciando ação de sair...")

    # Pressiona a tecla Escape
    pyautogui.keyDown('esc')
    time.sleep(0.044)  # Atraso para simular o tempo de pressão
    pyautogui.keyUp('esc')
    
    # Movimentos e cliques do mouse
    time.sleep(0.036)  # Atraso para garantir que o jogo registre a ação
    pyautogui.moveTo(1354, 765)  # Move o mouse para a posição especificada
    time.sleep(0.481)
    
    # Clique do mouse
    pyautogui.mouseDown(x=1354, y=884)  # Pressiona o botão esquerdo
    pyautogui.moveTo(1354, 884)  # Move o mouse (no caso, mantém a posição)
    pyautogui.mouseUp(x=1354, y=884)  # Solta o botão esquerdo
    
    # Outro movimento do mouse
    pyautogui.moveTo(1489, 874)
    time.sleep(0.013)  # Breve atraso
    pyautogui.mouseDown(x=1489, y=874)  # Pressiona o botão esquerdo
    pyautogui.moveTo(1489, 874)  # Move o mouse
    pyautogui.mouseUp(x=1489, y=874)  # Solta o botão esquerdo
    time.sleep(0.062)  # Atraso para registrar a ação

    # Realiza o último clique
    pyautogui.moveTo(1441, 885)
    pyautogui.mouseDown(x=1441, y=885)
    time.sleep(0.086)  # Atraso para pressionar o botão
    pyautogui.mouseUp(x=1441, y=885)  # Solta o botão do mouse
    print("Ação de sair completada!")

def execute_resgatar_script():
    """Executa o script resgatar.py após 60 segundos do término do script principal."""
    print("Aguardando 60 segundos antes de executar resgatar.py...")
    time.sleep(60)
    print("Iniciando resgatar.py...")
    subprocess.run(['python', 'resgatar.py'])
    print("resgatar.py executado com sucesso!")

def main():
    time.sleep(15)  # Espera 15 segundos
    focus_fortnite()  # Foca a janela do Fortnite
    execute_sair()  # Executa as ações de sair

    # Após a finalização do script, aguarda 60 segundos e executa resgatar.py
    execute_resgatar_script()

if __name__ == "__main__":
    main()