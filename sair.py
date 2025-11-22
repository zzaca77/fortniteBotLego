# -*- coding: utf-8 -*-
import pyautogui
import time
import subprocess
import os
import json
import logging
from utils import clicar_por_imagem  # Importa a função de clique

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Diretório base do script atual (src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (um nível acima de src)
PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT_DIR, 'config', 'config.json')

# Tempo de espera em segundos entre as ações críticas (ajustável)
TEMPO_ESPERA_ACOES = 15  # 60 segundos = 1 minuto, conforme instrução

def carregar_configuracoes_sair():
    """Carrega os caminhos das imagens necessárias do config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            caminhos_rel = config.get('caminhos_imagens', {})
            logging.info(f"Configurações carregadas com sucesso para sair.py de {CONFIG_FILE}")
            
            # Converte para caminhos absolutos
            caminhos_abs = {}
            for key, rel_path in caminhos_rel.items():
                caminhos_abs[key] = _get_absolute_image_path(rel_path)

            necessarias = ['sair_menu', 'voltar_lobby', 'confirmar_sim']
            faltando = []
            for img_key in necessarias:
                abs_path = caminhos_abs.get(img_key)
                if not abs_path:
                    faltando.append(f"{img_key} (não configurado ou caminho relativo inválido: {caminhos_rel.get(img_key)})")
                elif not os.path.exists(abs_path):
                    faltando.append(f"{img_key} (arquivo não encontrado em: {abs_path}, relativo original: {caminhos_rel.get(img_key)})")
            
            if faltando:
                logging.warning(f"Imagens necessárias para sair.py não encontradas ou inválidas: {', '.join(faltando)}")
            return caminhos_abs # Retorna caminhos absolutos
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

def executar_saida(caminhos_imagens_abs):
    """
    Executa a sequência de ações para sair da partida.

    Args:
        caminhos_imagens_abs (dict): Dicionário com os caminhos ABSOLUTOS das imagens.

    Returns:
        bool: True se o processo de saída foi iniciado com sucesso, False caso contrário.
    """
    img_sair_menu = caminhos_imagens_abs.get('sair_menu')
    img_voltar_lobby = caminhos_imagens_abs.get('voltar_lobby')
    img_confirmar_sim = caminhos_imagens_abs.get('confirmar_sim')

    if not all([img_sair_menu, img_voltar_lobby, img_confirmar_sim]):
        logging.error("Faltam caminhos de imagem essenciais (absolutos) para o processo de saída. Verifique logs anteriores de carregamento.")
        return False
    
    # Log para verificar os caminhos que serão usados
    logging.info(f"Usando imagem para Sair Menu: {img_sair_menu}")
    logging.info(f"Usando imagem para Voltar ao Lobby: {img_voltar_lobby}")
    logging.info(f"Usando imagem para Confirmar Sim: {img_confirmar_sim}")

    try:
        time.sleep(2)
        logging.info("Pressionando ESC para abrir o menu...")
        pyautogui.keyDown('esc')
        time.sleep(0.05) # Pequeno ajuste no tempo de pressionamento
        pyautogui.keyUp('esc')
        logging.info("Aguardando 3 segundos após pressionar ESC...")
        time.sleep(3)

        logging.info(f"Tentando clicar em 'Sair' (imagem: {os.path.basename(img_sair_menu if img_sair_menu else 'N/A')})...")
        if clicar_por_imagem(img_sair_menu, tentativas=3, confianca=0.8):
            logging.info(f"Botão 'Sair' clicado. Aguardando {TEMPO_ESPERA_ACOES} segundos...")
            time.sleep(TEMPO_ESPERA_ACOES)

            logging.info(f"Tentando clicar em 'Voltar ao Lobby' (imagem: {os.path.basename(img_voltar_lobby if img_voltar_lobby else 'N/A')})...")
            if clicar_por_imagem(img_voltar_lobby, tentativas=3, confianca=0.8):
                logging.info(f"Botão 'Voltar ao Lobby' clicado. Aguardando {TEMPO_ESPERA_ACOES} segundos...")
                time.sleep(TEMPO_ESPERA_ACOES)

                logging.info(f"Tentando clicar em 'Sim' para confirmação (imagem: {os.path.basename(img_confirmar_sim if img_confirmar_sim else 'N/A')})...")
                clicou_sim = clicar_por_imagem(img_confirmar_sim, tentativas=2, confianca=0.8, usar_backup=False)
                if clicou_sim:
                    logging.info("Botão 'Sim' de confirmação clicado.")
                    logging.info(f"Aguardando {TEMPO_ESPERA_ACOES // 2} segundos extras...")
                    time.sleep(TEMPO_ESPERA_ACOES // 2)
                else:
                    logging.info("Botão 'Sim' não encontrado ou não foi necessário.")

                logging.info("Processo de saída iniciado com sucesso.")
                return True
            else:
                logging.error(f"Falha ao clicar em 'Voltar ao Lobby' ({os.path.basename(img_voltar_lobby if img_voltar_lobby else 'N/A')}).")
                return False
        else:
            logging.error(f"Falha ao clicar em 'Sair' no menu ({os.path.basename(img_sair_menu if img_sair_menu else 'N/A')}).")
            return False
    except Exception as e:
        logging.exception("Erro inesperado durante o processo de saída.")
        return False

def chamar_script_retorno_lobby():
    """Chama o script retorno_lobby.py para finalizar o ciclo."""
    try:
        script_retorno_path = os.path.join(BASE_DIR, 'retorno_lobby.py')
        if not os.path.exists(script_retorno_path):
            logging.error(f"Arquivo 'retorno_lobby.py' não encontrado em {BASE_DIR}.")
            return False

        logging.info(f"Chamando o script {script_retorno_path}...")
        python_executable = 'python3' if os.name != 'nt' else 'python'
        subprocess.Popen([python_executable, script_retorno_path], cwd=BASE_DIR)
        logging.info("Processo retorno_lobby.py iniciado.")
        return True
    except Exception as e:
        logging.exception("Falha ao iniciar retorno_lobby.py")
        return False

if __name__ == '__main__':
    logging.info("--- Iniciando sair.py (versão com caminhos corrigidos) ---")
    # Adiciona o diretório raiz do projeto ao sys.path para garantir que 'utils' seja encontrado
    import sys
    if PROJECT_ROOT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_ROOT_DIR)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
        
    caminhos_config = carregar_configuracoes_sair()

    if caminhos_config:
        if executar_saida(caminhos_config):
            logging.info("Processo de saída concluído. Chamando retorno_lobby.py...")
            logging.info(f"Aguardando {TEMPO_ESPERA_ACOES} segundos antes de chamar retorno_lobby.py...")
            time.sleep(TEMPO_ESPERA_ACOES)
            chamar_script_retorno_lobby()
        else:
            logging.error("Falha no processo de saída da partida. retorno_lobby.py não será chamado.")
    else:
        logging.error("Não foi possível carregar as configurações para sair.py.")

    logging.info("--- Encerrando sair.py ---")

