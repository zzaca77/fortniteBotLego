# -*- coding: utf-8 -*-
"""
Este módulo, start.py, é responsável por iniciar uma partida no Fortnite LEGO.
Ele é chamado pelo painel.py após o usuário configurar e iniciar o bot.

Utiliza a função clicar_por_imagem de utils.py, que inclui múltiplas tentativas
e um sistema de backup de coordenadas JSON para maior robustez.

O fluxo principal tenta clicar diretamente no botão 'Jogar' na tela inicial.
Se esse botão não for encontrado (talvez devido a uma tela diferente ou estado do jogo),
O script ativa um fluxo alternativo:
1. Clica no botão 'Selecionar Mundo'.
2. Seleciona o mundo específico (ex: LEGO Fortnite).
3. Clica no botão 'Jogar' dentro da tela de seleção de mundo.

Após o clique bem-sucedido em 'Jogar' (seja no fluxo normal ou alternativo),
O script implementa um tempo de espera crucial de 1 minuto (60 segundos).
Esta pausa garante que o jogo tenha tempo suficiente para carregar a partida completamente
antes que o módulo bot.py seja chamado para iniciar as ações dentro do jogo.
Isso previne que o bot tente interagir com elementos que ainda não apareceram na tela,
melhorando a estabilidade e a confiabilidade do processo.

Este script lê as configurações necessárias (caminhos das imagens e tempo de execução)
Do arquivo config.json, que foi salvo pelo painel.py.
"""

import time
import subprocess
import json
import os
import logging

# Importa a função de clique com múltiplas tentativas e backup JSON
from utils import clicar_por_imagem # Presume-se que utils.py está no mesmo diretório (src)

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Diretório base do script atual (src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (um nível acima de src)
PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT_DIR, 'config', 'config.json')

def carregar_configuracoes_start():
    """Carrega as configurações do config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            logging.info(f"Configurações carregadas com sucesso para start.py de {CONFIG_FILE}")
            return config
    except FileNotFoundError:
        logging.error(f"Erro: Arquivo de configuração {CONFIG_FILE} não encontrado.")
        return None
    except json.JSONDecodeError:
        logging.error(f"Erro: Falha ao decodificar o arquivo JSON: {CONFIG_FILE}")
        return None
    except Exception as e:
        logging.error(f"Erro inesperado ao carregar configurações: {e}")
        return None

def _get_absolute_image_path(relative_path_from_config):
    """Converte um caminho relativo do config.json para um caminho absoluto."""
    if not relative_path_from_config:
        return None
    if os.path.isabs(relative_path_from_config):
        return relative_path_from_config # Já é absoluto
    # Caminhos no config.json são relativos ao PROJECT_ROOT_DIR
    abs_path = os.path.join(PROJECT_ROOT_DIR, relative_path_from_config)
    return os.path.normpath(abs_path)

def iniciar_partida(config):
    """
    Tenta iniciar a partida usando o fluxo alternativo de 'Selecionar Mundo',
    utilizando clicar_por_imagem com muitas tentativas e backup JSON.

    Args:
        config (dict): Dicionário contendo os caminhos das imagens e outras configs.

    Returns:
        bool: True se a partida foi iniciada com sucesso, False caso contrário.
    """
    caminhos_rel = config.get('caminhos_imagens', {})
    
    img_selecionar_mundo_1_rel = caminhos_rel.get('selecionar_mundo_1')
    img_selecionar_mundo_2_rel = caminhos_rel.get('selecionar_mundo_2')
    img_jogar_selecao_rel = caminhos_rel.get('jogar_selecao')

    img_selecionar_mundo_1 = _get_absolute_image_path(img_selecionar_mundo_1_rel)
    img_selecionar_mundo_2 = _get_absolute_image_path(img_selecionar_mundo_2_rel)
    img_jogar_selecao = _get_absolute_image_path(img_jogar_selecao_rel)

    TENTATIVAS_ALTAS = 500
    INTERVALO_TENTATIVAS = 1
    CONFIANCA_IMAGEM = 0.8

    required_images_info = {
        "Selecionar Mundo 1": img_selecionar_mundo_1,
        "Selecionar Mundo 2 (LEGO)": img_selecionar_mundo_2,
        "Jogar (Seleção)": img_jogar_selecao
    }

    for name, path in required_images_info.items():
        if not path:
            logging.error(f"Caminho para imagem '{name}' não configurado ou inválido no config.json.")
            return False
        if not os.path.exists(path):
            logging.error(f"Imagem '{name}' não encontrada no caminho: {path} (Relativo original: {caminhos_rel.get(name.lower().replace(' ', '_').replace('(', '').replace(')', ''))}). Verifique o config.json e a existência do arquivo.")
            return False
        logging.info(f"Caminho absoluto para '{name}': {path}")

    logging.info("Fluxo Secundário: Sempre indo para a seleção de mundo.")
    time.sleep(2)

    logging.info(f"Tentando clicar em 'Selecionar Mundo 1' ({os.path.basename(img_selecionar_mundo_1)})...")
    if clicar_por_imagem(img_selecionar_mundo_1, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
        time.sleep(2)
        logging.info(f"Fluxo Secundário: Selecionar o mundo (LEGO Fortnite) ({os.path.basename(img_selecionar_mundo_2)})...")
        if clicar_por_imagem(img_selecionar_mundo_2, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
            time.sleep(4)
            logging.info(f"Fluxo Secundário: Clicar em 'Jogar' na seleção de mundo ({os.path.basename(img_jogar_selecao)})...")
            time.sleep(2)
            if clicar_por_imagem(img_jogar_selecao, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
                logging.info("Fluxo Secundário concluído. Botão 'Jogar' (Seleção) clicado.")
                return True
            else:
                logging.error(f"Falha ao clicar no botão 'Jogar' (Seleção) ({os.path.basename(img_jogar_selecao)}). Tentativas esgotadas.")
                return False
        else:
            logging.error(f"Falha ao selecionar o mundo (LEGO Fortnite) ({os.path.basename(img_selecionar_mundo_2)}). Tentativas esgotadas.")
            return False
    else:
        logging.error(f"Falha ao clicar em 'Selecionar Mundo 1' ({os.path.basename(img_selecionar_mundo_1)}). Tentativas esgotadas.")
        return False

if __name__ == '__main__':
    logging.info("--- Iniciando start.py (versão com caminhos corrigidos) ---")
    # Adiciona o diretório raiz do projeto ao sys.path para garantir que 'utils' seja encontrado
    # Isso é útil se start.py for executado de um diretório diferente de 'src' em alguns cenários de teste,
    # embora o subprocess.Popen no painel defina cwd='src'.
    import sys
    if PROJECT_ROOT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_ROOT_DIR) # Garante que src.utils possa ser importado se necessário
    if BASE_DIR not in sys.path: # src
        sys.path.insert(0, BASE_DIR)

    configuracoes = carregar_configuracoes_start()

    if configuracoes:
        if iniciar_partida(configuracoes):
            logging.info("Partida iniciada. Aguardando 60 segundos para o carregamento...")
            time.sleep(60)
            logging.info("Tempo de espera concluído. Chamando bot.py...")
            try:
                script_bot_path = os.path.join(BASE_DIR, 'bot.py')
                logging.info(f"Tentando chamar bot.py a partir do caminho: {script_bot_path}")
                if not os.path.exists(script_bot_path):
                    logging.error(f"Arquivo 'bot.py' não encontrado em {BASE_DIR}.")
                else:
                    # O bot.py também lerá as configs de config.json e deverá usar _get_absolute_image_path ou similar
                    # Se bot.py também usa imagens do config.json, ele precisará de lógica similar para caminhos.
                    # O cwd para bot.py será o mesmo que start.py (BASE_DIR, ou seja, 'src')
                    python_executable = 'python3' if os.name != 'nt' else 'python'
                    subprocess.Popen([python_executable, script_bot_path], cwd=BASE_DIR)
                    logging.info("Processo bot.py iniciado.")
            except Exception as e:
                logging.exception("Falha ao iniciar bot.py")
        else:
            logging.error("Não foi possível iniciar a partida após tentar o fluxo alternativo.")
    else:
        logging.error("Não foi possível carregar as configurações. Encerrando start.py.")

    logging.info("--- Encerrando start.py ---")

