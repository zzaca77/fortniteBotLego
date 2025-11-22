# -*- coding: utf-8 -*-
import pyautogui
import time
import random
import subprocess
import os
import json
import logging
import sys

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Diretório base e arquivo de configuração
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), 'config', 'config.json')
PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)

# Desativar o fail-safe do PyAutoGUI (NÃO RECOMENDADO, USAR COM CAUTELA)
pyautogui.FAILSAFE = False

def carregar_configuracoes_bot():
    """Carrega as configurações do config.json, especificamente o tempo de execução."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            tempo_segundos = config.get('tempo_execucao_segundos')
            if tempo_segundos is None or not isinstance(tempo_segundos, int) or tempo_segundos <= 0:
                logging.error("Tempo de execução inválido ou não encontrado em config.json. Usando padrão de 300s (5 min).")
                return 300
            logging.info(f"Configurações carregadas para bot.py. Tempo de execução: {tempo_segundos}s")
            return tempo_segundos
    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de configuração {CONFIG_FILE} não encontrado. Usando padrão de 300s.")
        return 300
    except json.JSONDecodeError:
        logging.error(f"Erro: Falha ao decodificar {CONFIG_FILE}. Usando padrão de 300s.")
        return 300
    except Exception as e:
        logging.error(f"Erro inesperado ao carregar config: {e}. Usando padrão de 300s.")
        return 300

def get_screen_dimensions():
    """Obtém as dimensões da tela."""
    return pyautogui.size()

def safe_move(x, y, duration=0.2):
    """Move o mouse para dentro da zona segura da tela."""
    screen_width, screen_height = get_screen_dimensions()
    SAFE_MARGIN = 50
    safe_x_min, safe_x_max = SAFE_MARGIN, screen_width - SAFE_MARGIN
    safe_y_min, safe_y_max = SAFE_MARGIN, screen_height - SAFE_MARGIN

    target_x = max(safe_x_min, min(safe_x_max, x))
    target_y = max(safe_y_min, min(safe_y_max, y))
    pyautogui.moveTo(target_x, target_y, duration=duration)

def realizar_acoes_aleatorias(duracao_total_segundos):
    """
    Executa ações aleatórias aprimoradas, incluindo combinações de teclas e sequências,
    pelo tempo especificado.
    """
    tempo_inicio = time.time()
    tempo_fim = tempo_inicio + duracao_total_segundos

    logging.info(f"Iniciando ciclo de ações aleatórias por {duracao_total_segundos} segundos.")

    acoes_possiveis = [
        ('mover_curto', 12), ('mover_longo', 6), ('correr_curto', 10), ('correr_longo', 5),
        ('pular', 7), ('agachar_toggle', 5), ('agachar_hold', 3), ('interagir', 4),
        ('recarregar', 3), ('mover_camera_suave', 18), ('mover_camera_rapido', 7),
        ('pausa_curta', 12), ('pausa_media', 8),
        ('seq_mover_olhar', 9), ('seq_correr_parar_olhar', 8)
    ]
    nomes_acoes = [a[0] for a in acoes_possiveis]
    pesos_acoes = [a[1] for a in acoes_possiveis]

    while time.time() < tempo_fim:
        tempo_restante = tempo_fim - time.time()
        if tempo_restante <= 0:
            break

        acao_escolhida = random.choices(nomes_acoes, weights=pesos_acoes, k=1)[0]
        logging.debug(f"Tempo restante: {tempo_restante:.2f}s. Próxima ação: {acao_escolhida}")

        try:
            duracao_acao = 0

            if acao_escolhida == 'mover_curto':
                tecla = random.choice(['w', 'a', 's', 'd'])
                duracao_press = random.uniform(0.2, 0.8)
                pyautogui.keyDown(tecla)
                time.sleep(max(0, min(duracao_press, tempo_restante)))
                pyautogui.keyUp(tecla)
                duracao_acao = duracao_press
            elif acao_escolhida == 'mover_longo':
                tecla = random.choice(['w', 'a', 's', 'd'])
                duracao_press = random.uniform(1.0, 2.5)
                pyautogui.keyDown(tecla)
                time.sleep(max(0, min(duracao_press, tempo_restante)))
                pyautogui.keyUp(tecla)
                duracao_acao = duracao_press
            elif acao_escolhida == 'pular':
                pyautogui.press('space')
                duracao_acao = random.uniform(0.4, 1.0)
                time.sleep(max(0, min(duracao_acao, tempo_restante)))
            elif acao_escolhida == 'agachar_toggle':
                pyautogui.press('ctrl')
                duracao_acao = random.uniform(0.6, 1.5)
                time.sleep(max(0, min(duracao_acao, tempo_restante)))
                if random.random() < 0.7:
                    pyautogui.press('ctrl')
                    duracao_acao += 0.2
            elif acao_escolhida == 'agachar_hold':
                duracao_hold = random.uniform(0.8, 2.0)
                pyautogui.keyDown('ctrl')
                time.sleep(max(0, min(duracao_hold, tempo_restante)))
                pyautogui.keyUp('ctrl')
                duracao_acao = duracao_hold
            elif acao_escolhida == 'interagir':
                pyautogui.press('e')
                duracao_acao = random.uniform(0.5, 1.0)
                time.sleep(max(0, min(duracao_acao, tempo_restante)))
            elif acao_escolhida == 'recarregar':
                pyautogui.press('r')
                duracao_acao = random.uniform(1.0, 2.0)
                time.sleep(max(0, min(duracao_acao, tempo_restante)))
            elif acao_escolhida == 'mover_camera_suave':
                move_x = random.randint(-80, 80)
                move_y = random.randint(-40, 40)
                duracao_mov = random.uniform(0.2, 0.6)
                current_x, current_y = pyautogui.position()
                safe_move(current_x + move_x, current_y + move_y, duration=duracao_mov)
                duracao_acao = duracao_mov
            elif acao_escolhida == 'mover_camera_rapido':
                move_x = random.randint(-200, 200)
                move_y = random.randint(-100, 100)
                duracao_mov = random.uniform(0.1, 0.25)
                current_x, current_y = pyautogui.position()
                safe_move(current_x + move_x, current_y + move_y, duration=duracao_mov)
                duracao_acao = duracao_mov
            elif acao_escolhida == 'pausa_curta':
                duracao_pausa = random.uniform(0.3, 1.0)
                time.sleep(max(0, min(duracao_pausa, tempo_restante)))
                duracao_acao = duracao_pausa
            elif acao_escolhida == 'pausa_media':
                duracao_pausa = random.uniform(1.0, 2.0)
                time.sleep(max(0, min(duracao_pausa, tempo_restante)))
                duracao_acao = duracao_pausa
            elif acao_escolhida == 'correr_curto':
                tecla = random.choice(['w', 'a', 's', 'd'])
                duracao_press = random.uniform(0.5, 1.5)
                pyautogui.keyDown('shift')
                pyautogui.keyDown(tecla)
                time.sleep(max(0, min(duracao_press, tempo_restante)))
                pyautogui.keyUp(tecla)
                pyautogui.keyUp('shift')
                duracao_acao = duracao_press
            elif acao_escolhida == 'correr_longo':
                tecla = 'w'
                duracao_press = random.uniform(1.5, 3.5)
                pyautogui.keyDown('shift')
                pyautogui.keyDown(tecla)
                time.sleep(max(0, min(duracao_press, tempo_restante)))
                pyautogui.keyUp(tecla)
                pyautogui.keyUp('shift')
                duracao_acao = duracao_press
            elif acao_escolhida == 'seq_mover_olhar':
                tecla_mov = random.choice(['w', 'a', 's', 'd'])
                dur_mov = random.uniform(0.5, 1.5)
                pyautogui.keyDown(tecla_mov)
                time.sleep(max(0, min(dur_mov, tempo_restante)))
                pyautogui.keyUp(tecla_mov)
                duracao_acao += dur_mov
                tempo_restante_seq = tempo_restante - dur_mov
                if tempo_restante_seq <= 0: continue
                dur_pausa1 = random.uniform(0.2, 0.5)
                time.sleep(max(0, min(dur_pausa1, tempo_restante_seq)))
                duracao_acao += dur_pausa1
                tempo_restante_seq -= dur_pausa1
                if tempo_restante_seq <= 0: continue
                move_x1 = random.randint(-150, -50) if random.random() < 0.5 else random.randint(50, 150)
                move_y1 = random.randint(-30, 30)
                dur_cam1 = random.uniform(0.2, 0.4)
                current_x, current_y = pyautogui.position()
                safe_move(current_x + move_x1, current_y + move_y1, duration=dur_cam1)
                duracao_acao += dur_cam1
                tempo_restante_seq -= dur_cam1
                if tempo_restante_seq <= 0: continue
                dur_pausa2 = random.uniform(0.3, 0.6)
                time.sleep(max(0, min(dur_pausa2, tempo_restante_seq)))
                duracao_acao += dur_pausa2
                tempo_restante_seq -= dur_pausa2
                if tempo_restante_seq <= 0: continue
                move_x2 = -move_x1 + random.randint(-30, 30)
                move_y2 = random.randint(-30, 30)
                dur_cam2 = random.uniform(0.2, 0.4)
                current_x, current_y = pyautogui.position()
                safe_move(current_x + move_x2, current_y + move_y2, duration=dur_cam2)
                duracao_acao += dur_cam2
            elif acao_escolhida == 'seq_correr_parar_olhar':
                dur_corrida = random.uniform(1.5, 3.0)
                pyautogui.keyDown('shift')
                pyautogui.keyDown('w')
                time.sleep(max(0, min(dur_corrida, tempo_restante)))
                pyautogui.keyUp('w')
                pyautogui.keyUp('shift')
                duracao_acao += dur_corrida
                tempo_restante_seq = tempo_restante - dur_corrida
                if tempo_restante_seq <= 0: continue
                dur_pausa1 = random.uniform(0.1, 0.3)
                time.sleep(max(0, min(dur_pausa1, tempo_restante_seq)))
                duracao_acao += dur_pausa1
                tempo_restante_seq -= dur_pausa1
                if tempo_restante_seq <= 0: continue
                move_x1 = random.randint(-200, 200)
                move_y1 = random.randint(-50, 50)
                dur_cam1 = random.uniform(0.1, 0.3)
                current_x, current_y = pyautogui.position()
                safe_move(current_x + move_x1, current_y + move_y1, duration=dur_cam1)
                duracao_acao += dur_cam1
                tempo_restante_seq -= dur_cam1
                if tempo_restante_seq <= 0: continue
                dur_pausa2 = random.uniform(0.5, 1.0)
                time.sleep(max(0, min(dur_pausa2, tempo_restante_seq)))
                duracao_acao += dur_pausa2

            if duracao_acao < 1.0:
                pausa_entre_acoes = random.uniform(0.1, 0.4)
            elif duracao_acao < 2.5:
                pausa_entre_acoes = random.uniform(0.2, 0.6)
            else:
                pausa_entre_acoes = random.uniform(0.3, 0.8)
            
            tempo_restante_final = tempo_fim - time.time()
            time.sleep(max(0, min(pausa_entre_acoes, tempo_restante_final)))

        except Exception as e:
            logging.error(f"Erro durante a execução da ação {acao_escolhida}: {e}")
            tempo_restante_ex = tempo_fim - time.time()
            time.sleep(max(0, min(0.5, tempo_restante_ex)))

    logging.info("Tempo de execução do bot concluído.")

def chamar_script_sair():
    """Chama o script sair.py para iniciar o processo de saída da partida."""
    try:
        script_sair_path = os.path.join(BASE_DIR, 'sair.py') 
        if not os.path.exists(script_sair_path):
            logging.error(f"Arquivo 'sair.py' não encontrado em {BASE_DIR}.")
            return False

        logging.info(f"Chamando o script {script_sair_path}...")
        python_executable = 'python3' if os.name != 'nt' else 'python'
        subprocess.Popen([python_executable, script_sair_path], cwd=BASE_DIR)
        logging.info("Processo sair.py iniciado.")
        return True
    except Exception as e:
        logging.exception("Falha ao iniciar sair.py")
        return False

if __name__ == '__main__':
    logging.info("--- Iniciando bot.py ---")
    
    # Adiciona os diretórios ao path para garantir que os imports funcionem
    if PROJECT_ROOT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_ROOT_DIR)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)

    # PASSO 1: Pausa inicial para garantir que a transição para o jogo seja concluída.
    # O usuário deve garantir que a janela do jogo está em foco.
    logging.info("Pausa de 2 segundos para garantir que o jogo esteja em foco. Clique na janela do Fortnite se necessário.")
    time.sleep(2)

    # PASSO 2: Carregar configurações e executar o bot.
    logging.info("Carregando configurações do bot...")
    tempo_total = carregar_configuracoes_bot()

    if tempo_total > 0:
        realizar_acoes_aleatorias(tempo_total)
        logging.info("Ações aleatórias concluídas. Preparando para sair da partida...")
        chamar_script_sair()
    else:
        logging.error("Tempo de execução inválido ou não carregado. Encerrando bot.py sem ações.")

    logging.info("--- Encerrando bot.py ---")
