import time
import subprocess
import os
import json
import logging
import pyautogui
from utils import clicar_por_imagem  # Importa a função de clique com backup JSON

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Diretório base do script atual (src)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Diretório raiz do projeto (um nível acima de src)
PROJECT_ROOT_DIR = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT_DIR, 'config', 'config.json')

# Tempo de espera em segundos entre as ações no lobby (ajustável)
TEMPO_ESPERA_LOBBY = 60  # 60 segundos = 1 minuto, conforme instrução

def _get_absolute_image_path(relative_path_from_config):
    """Converte um caminho relativo do config.json para um caminho absoluto."""
    if not relative_path_from_config:
        return None
    if os.path.isabs(relative_path_from_config):
        return relative_path_from_config # Já é absoluto
    # Caminhos no config.json são relativos ao PROJECT_ROOT_DIR
    abs_path = os.path.join(PROJECT_ROOT_DIR, relative_path_from_config)
    return os.path.normpath(abs_path)

def carregar_configuracoes_lobby():
    """Carrega os caminhos das imagens necessárias do config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            caminhos_rel = config.get('caminhos_imagens', {})
            logging.info(f"Configurações carregadas com sucesso para retorno_lobby.py de {CONFIG_FILE}")
            
            caminhos_abs = {}
            for key, rel_path in caminhos_rel.items():
                caminhos_abs[key] = _get_absolute_image_path(rel_path)

            necessarias = ['resgatar', 'avaliar_pular', 'selecionar_mundo_1', 'selecionar_mundo_2', 'jogar_selecao']
            faltando = []
            for img_key in necessarias:
                abs_path = caminhos_abs.get(img_key)
                if not abs_path:
                    # Não adicionar à lista de faltando se a chave original não estava no config (é opcional)
                    if img_key in caminhos_rel and caminhos_rel[img_key] is not None:
                        faltando.append(f"{img_key} (não configurado ou caminho relativo inválido: {caminhos_rel.get(img_key)})")
                elif not os.path.exists(abs_path):
                    faltando.append(f"{img_key} (arquivo não encontrado em: {abs_path}, relativo original: {caminhos_rel.get(img_key)})")
            
            if faltando:
                logging.warning(f"Imagens para retorno_lobby.py não encontradas ou inválidas: {', '.join(faltando)}")
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

def executar_acoes_lobby(caminhos_imagens_abs):
    """
    Executa as ações no lobby: resgatar, pular avaliação e tentar reiniciar usando clicar_por_imagem.

    Args:
        caminhos_imagens_abs (dict): Dicionário com os caminhos ABSOLUTOS das imagens.
    """
    img_resgatar = caminhos_imagens_abs.get('resgatar')
    img_avaliar_pular = caminhos_imagens_abs.get('avaliar_pular')
    img_selecionar_mundo_1 = caminhos_imagens_abs.get('selecionar_mundo_1')
    img_selecionar_mundo_2 = caminhos_imagens_abs.get('selecionar_mundo_2')
    img_jogar_selecao = caminhos_imagens_abs.get('jogar_selecao')

    # Log para verificar os caminhos que serão usados
    logging.info(f"Usando imagem para Resgatar: {img_resgatar}")
    logging.info(f"Usando imagem para Avaliar/Pular: {img_avaliar_pular}")
    logging.info(f"Usando imagem para Selecionar Mundo 1: {img_selecionar_mundo_1}")
    logging.info(f"Usando imagem para Selecionar Mundo 2: {img_selecionar_mundo_2}")
    logging.info(f"Usando imagem para Jogar (Seleção): {img_jogar_selecao}")

    if img_resgatar and os.path.exists(img_resgatar):
        logging.info(f"Verificando por botão 'Resgatar' (imagem: {os.path.basename(img_resgatar)})...")
        for _ in range(3):
            if clicar_por_imagem(img_resgatar, tentativas=1, confianca=0.8, usar_backup=True):
                logging.info(f"Botão 'Resgatar' clicado. Aguardando {TEMPO_ESPERA_LOBBY} segundos...")
                time.sleep(TEMPO_ESPERA_LOBBY)
                break
            else:
                logging.info("Botão 'Resgatar' não encontrado nesta tentativa. Aguardando 5s...")
                time.sleep(5)
        else:
            logging.info("Botão 'Resgatar' não encontrado após várias tentativas.")
    elif img_resgatar: # Caminho configurado mas não existe
        logging.warning(f"Imagem 'resgatar' configurada ({img_resgatar}) mas não encontrada no disco.")
    else: # Não configurado
        logging.info("Caminho para imagem 'resgatar' não fornecido ou inválido. Pulando esta etapa.")

    if img_avaliar_pular and os.path.exists(img_avaliar_pular):
        logging.info(f"Verificando por tela de avaliação / botão 'Pular' (imagem: {os.path.basename(img_avaliar_pular)})...")
        if clicar_por_imagem(img_avaliar_pular, tentativas=2, confianca=0.8, usar_backup=True):
            logging.info(f"Botão 'Pular' da avaliação clicado. Aguardando {TEMPO_ESPERA_LOBBY} segundos...")
            time.sleep(TEMPO_ESPERA_LOBBY)
        else:
            logging.info("Tela de avaliação / botão 'Pular' não encontrado.")
    elif img_avaliar_pular:
        logging.warning(f"Imagem 'avaliar_pular' configurada ({img_avaliar_pular}) mas não encontrada no disco.")
    else:
        logging.info("Caminho para imagem 'avaliar_pular' não fornecido ou inválido. Pulando esta etapa.")

    logging.info("Tentando reiniciar o ciclo: Selecionar Mundo e Jogar...")
    if img_selecionar_mundo_1 and os.path.exists(img_selecionar_mundo_1):
        if clicar_por_imagem(img_selecionar_mundo_1, tentativas=15, confianca=0.8, usar_backup=True):
            logging.info(f"Aguardando {TEMPO_ESPERA_LOBBY // 2}s após clicar em Selecionar Mundo...")
            time.sleep(TEMPO_ESPERA_LOBBY // 2)
            if img_selecionar_mundo_2 and os.path.exists(img_selecionar_mundo_2):
                logging.info("Selecionando o mundo (LEGO Fortnite)...")
                if clicar_por_imagem(img_selecionar_mundo_2, tentativas=15, confianca=0.8, usar_backup=True):
                    logging.info(f"Aguardando {TEMPO_ESPERA_LOBBY // 2}s após selecionar mundo...")
                    time.sleep(TEMPO_ESPERA_LOBBY // 2)
                    if img_jogar_selecao and os.path.exists(img_jogar_selecao):
                        logging.info("Clicando em 'Jogar' na seleção de mundo...")
                        if clicar_por_imagem(img_jogar_selecao, tentativas=15, confianca=0.8, usar_backup=True):
                            logging.info("Botão 'Jogar' (Seleção) clicado. O ciclo deve recomeçar.")
                            logging.info("Aguardando o jogo iniciar a próxima partida...")
                            time.sleep(TEMPO_ESPERA_LOBBY)
                            chamar_script_bot()
                            return # Fim do fluxo bem sucedido
                        else:
                            logging.error("Falha ao clicar no botão 'Jogar' (Seleção).")
                    else:
                        logging.error("Imagem 'jogar_selecao' não configurada ou não encontrada.")
                else:
                    logging.error("Falha ao selecionar o mundo (LEGO Fortnite).")
            else:
                logging.error("Imagem 'selecionar_mundo_2' não configurada ou não encontrada.")
        else:
            logging.error("Falha ao clicar em 'Selecionar Mundo 1'.")
    else:
        logging.error("Imagem 'selecionar_mundo_1' não configurada ou não encontrada. Não é possível reiniciar o ciclo.")

def chamar_script_bot():
    """Chama o script bot.py para iniciar o processo de ações dentro do jogo."""
    try:
        script_bot_path = os.path.join(BASE_DIR, 'bot.py')
        if not os.path.exists(script_bot_path):
            logging.error(f"Arquivo 'bot.py' não encontrado em {BASE_DIR}.")
            return False

        logging.info(f"Chamando o script {script_bot_path}...")
        python_executable = 'python3' if os.name != 'nt' else 'python'
        subprocess.Popen([python_executable, script_bot_path], cwd=BASE_DIR)
        logging.info("Processo bot.py iniciado.")
        return True
    except Exception as e:
        logging.exception("Falha ao iniciar bot.py")
        return False

if __name__ == '__main__':
    logging.info("--- Iniciando retorno_lobby.py (versão com caminhos corrigidos) ---")
    import sys
    if PROJECT_ROOT_DIR not in sys.path:
        sys.path.insert(0, PROJECT_ROOT_DIR)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
        
    logging.info(f"Aguardando {TEMPO_ESPERA_LOBBY // 2} segundos para o lobby estabilizar...")
    time.sleep(TEMPO_ESPERA_LOBBY // 2)

    caminhos_config = carregar_configuracoes_lobby()

    if caminhos_config:
        executar_acoes_lobby(caminhos_config)
        logging.info("Ações no lobby concluídas (ou tentativa de reinício realizada).")
    else:
        logging.error("Não foi possível carregar as configurações para retorno_lobby.py.")

    logging.info("--- Encerrando retorno_lobby.py ---")

