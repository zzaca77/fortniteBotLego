import pyautogui
import time
import random
import subprocess
from pynput.keyboard import Controller, Key

keyboard = Controller()

# Variáveis globais para controlar o estado do bot
bot_active = True  # O bot começa ativado automaticamente

def move_randomly():
    """Movimenta o personagem em direções aleatórias com tempos variáveis."""
    movements = ['w', 'a', 's', 'd']
    key = random.choice(movements)
    
    press_time = random.uniform(0.5, 3)  # Tempo aleatório segurando a tecla
    keyboard.press(key)
    time.sleep(press_time)
    keyboard.release(key)
    
    # Pequena pausa aleatória para parecer mais natural
    if random.random() < 0.3:
        time.sleep(random.uniform(0.2, 1))

def jump():
    """Simula um pulo de forma aleatória."""
    if random.random() < 0.4:  # 40% de chance de pular
        keyboard.press(Key.space)
        time.sleep(random.uniform(0.1, 0.3))
        keyboard.release(Key.space)

def look_around():
    """Move a câmera de forma aleatória."""
    if random.random() < 0.7:  # 70% de chance de olhar ao redor
        x_move = random.randint(-80, 80)
        y_move = random.randint(-80, 80)
        pyautogui.moveRel(x_move, y_move, duration=random.uniform(0.1, 0.5))

def simulate_human_behavior():
    """Simula pequenas pausas e variações de comportamento."""
    if random.random() < 0.2:  # 20% de chance de dar uma pausa rápida
        time.sleep(random.uniform(2, 5))

def execute_sair_script():
    """Executa o script sair.py quando o tempo de 1 hora se esgota."""
    print("Tempo de 1 hora atingido, executando sair.py...")
    subprocess.run(['python', 'sair.py'])  # Executa o script sair.py
    print("sair.py executado com sucesso!")

def main():
    """Função principal para rodar o bot."""
    start_time = time.time()  # Marca o tempo de início do bot
    print("Bot iniciado... Vai rodar por 1 hora e depois executará sair.py.")

    while True:
        # Se o bot estiver ativo
        if bot_active:
            # Realiza as ações do bot
            move_randomly()
            jump()
            look_around()
            simulate_human_behavior()

            # Tempo aleatório antes da próxima ação para evitar padrões
            time.sleep(random.uniform(1, 4))

        # Verifica se o tempo de 1 hora passou
        elapsed_time = time.time() - start_time
        if elapsed_time >= 3600:  # 1 hora = 3600 segundos
            execute_sair_script()  # Executa sair.py
            break  # Sai do loop e termina o bot

if __name__ == "__main__":
    main()