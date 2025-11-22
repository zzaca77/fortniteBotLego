# -*- coding: utf-8 -*-
"""
Este módulo, utils.py, fornece funções auxiliares essenciais para o funcionamento do bot de automação do Fortnite LEGO.
Ele inclui funcionalidades para localizar imagens na tela, clicar nelas e um sistema robusto de backup de coordenadas
para garantir que o bot possa continuar operando mesmo quando uma imagem específica não é imediatamente detectável.
Isso aumenta a resiliência do bot a pequenas variações na interface do jogo ou atrasos no carregamento.
As coordenadas encontradas são persistidas em um arquivo JSON.
"""

import pyautogui
import time
import logging
import json
import os

# Configuração básica de logging para registrar informações e erros.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define o caminho para o arquivo JSON que armazenará as coordenadas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDENADAS_JSON_PATH = os.path.join(os.path.dirname(BASE_DIR), 'config', 'coordenadas_backup.json')

# Dicionário global para armazenar as últimas coordenadas conhecidas das imagens.
# Será carregado do JSON no início e salvo quando atualizado.
coordenadas_armazenadas = {}

def carregar_coordenadas_json():
    """Carrega as coordenadas do arquivo JSON para o dicionário global."""
    global coordenadas_armazenadas
    try:
        if os.path.exists(COORDENADAS_JSON_PATH):
            with open(COORDENADAS_JSON_PATH, 'r', encoding='utf-8') as f:
                coordenadas_armazenadas = json.load(f)
                # Converte listas de volta para tuplas após carregar do JSON
                for key, value in coordenadas_armazenadas.items():
                    if isinstance(value, list) and len(value) == 2:
                        coordenadas_armazenadas[key] = tuple(value)
                logging.info(f"Coordenadas carregadas com sucesso de {COORDENADAS_JSON_PATH}")
        else:
            logging.info(f"Arquivo de coordenadas {COORDENADAS_JSON_PATH} não encontrado. Será criado um novo se necessário.")
            coordenadas_armazenadas = {}
    except json.JSONDecodeError:
        logging.error(f"Erro ao decodificar JSON de {COORDENADAS_JSON_PATH}. Iniciando com coordenadas vazias.")
        coordenadas_armazenadas = {}
    except Exception as e:
        logging.error(f"Erro inesperado ao carregar coordenadas de {COORDENADAS_JSON_PATH}: {e}")
        coordenadas_armazenadas = {}

def salvar_coordenadas_json():
    """Salva o dicionário global de coordenadas no arquivo JSON."""
    global coordenadas_armazenadas
    try:
        # Converte tuplas para listas antes de salvar no JSON
        coordenadas_para_salvar = {}
        for key, value in coordenadas_armazenadas.items():
            if isinstance(value, tuple) and len(value) == 2:
                 # Garante que são coordenadas (x, y)
                 if all(isinstance(coord, (int, float)) for coord in value):
                    coordenadas_para_salvar[key] = list(value)
                 else:
                    logging.warning(f"Valor inválido {value} para a chave {key} não será salvo no JSON.")
            elif isinstance(value, pyautogui.Point):
                 # Trata o tipo Point do pyautogui que pode ocorrer
                 coordenadas_para_salvar[key] = [value.x, value.y]
            else:
                logging.warning(f"Tipo de valor inesperado {type(value)} para a chave {key} não será salvo no JSON.")

        with open(COORDENADAS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(coordenadas_para_salvar, f, indent=4, ensure_ascii=False)
        logging.info(f"Coordenadas salvas com sucesso em {COORDENADAS_JSON_PATH}")
    except Exception as e:
        logging.error(f"Erro inesperado ao salvar coordenadas em {COORDENADAS_JSON_PATH}: {e}")

# Carrega as coordenadas do JSON quando o módulo é importado pela primeira vez.
carregar_coordenadas_json()

def clicar_por_imagem(imagem_path, tentativas=3, intervalo=1, confianca=0.8, usar_backup=True):
    """
    Localiza uma imagem na tela e clica no centro dela, usando backup de coordenadas JSON.

    Esta função tenta localizar a imagem especificada (`imagem_path`) na tela usando a biblioteca pyautogui.
    Se a imagem for encontrada com um nível de confiança mínimo (`confianca`), a função move o mouse
    para o centro da imagem e realiza um clique.

    A função implementa um mecanismo de retentativa (`tentativas`) com um intervalo (`intervalo`) entre elas.
    Se a imagem for encontrada, suas coordenadas são atualizadas no dicionário `coordenadas_armazenadas`
    e salvas no arquivo JSON (`COORDENADAS_JSON_PATH`).

    Se a imagem não for encontrada após as tentativas, e `usar_backup` for True, a função verifica
    se há coordenadas previamente carregadas do JSON para essa imagem. Se houver, clica nessas coordenadas salvas.

    Args:
        imagem_path (str): O caminho absoluto ou relativo para o arquivo de imagem a ser localizado.
        tentativas (int, optional): O número máximo de vezes que a função tentará localizar a imagem.
                                   O padrão é 3.
        intervalo (int, optional): O tempo em segundos a esperar entre as tentativas. O padrão é 1.
        confianca (float, optional): O nível mínimo de confiança necessário para considerar a imagem encontrada.
                                     O valor deve estar entre 0.0 e 1.0. O padrão é 0.8.
        usar_backup (bool, optional): Se True, utiliza as coordenadas armazenadas (carregadas do JSON)
                                      caso a imagem não seja encontrada após as tentativas. O padrão é True.

    Returns:
        bool: True se a imagem foi encontrada e clicada (ou se o backup foi usado com sucesso),
              False caso contrário.
    """
    global coordenadas_armazenadas
    logging.info(f"Tentando localizar e clicar na imagem: {imagem_path}")
    localizacao = None
    for tentativa in range(tentativas):
        try:
            # Tenta localizar a imagem na tela.
            localizacao = pyautogui.locateCenterOnScreen(imagem_path, confidence=confianca, grayscale=True)
            if localizacao:
                # Converte para tupla de inteiros para consistência
                coord_tuple = (int(localizacao.x), int(localizacao.y))
                logging.info(f"Imagem '{imagem_path}' encontrada na tentativa {tentativa + 1} em {coord_tuple}.")
                pyautogui.moveTo(coord_tuple)
                pyautogui.click()
                logging.info(f"Clique realizado em {coord_tuple}.")
                # Atualiza o backup de coordenadas e salva no JSON.
                if coordenadas_armazenadas.get(imagem_path) != coord_tuple:
                    coordenadas_armazenadas[imagem_path] = coord_tuple
                    logging.info(f"Coordenadas de backup para '{imagem_path}' atualizadas para {coord_tuple}. Salvando no JSON...")
                    salvar_coordenadas_json()
                else:
                    logging.info(f"Coordenadas para '{imagem_path}' ({coord_tuple}) já estavam atualizadas.")
                return True
            else:
                logging.warning(f"Imagem '{imagem_path}' não encontrada na tentativa {tentativa + 1}. Aguardando {intervalo}s.")
                time.sleep(intervalo)
        except pyautogui.ImageNotFoundException:
            logging.warning(f"Exceção ImageNotFoundException na tentativa {tentativa + 1} para '{imagem_path}'. Aguardando {intervalo}s.")
            time.sleep(intervalo)
        except Exception as e:
            logging.error(f"Erro inesperado ao tentar localizar '{imagem_path}' na tentativa {tentativa + 1}: {e}")
            time.sleep(intervalo)

    # Se a imagem não foi encontrada após todas as tentativas
    logging.warning(f"Imagem '{imagem_path}' não encontrada após {tentativas} tentativas.")

    # Tenta usar o backup de coordenadas (carregado do JSON) se habilitado e disponível
    if usar_backup and imagem_path in coordenadas_armazenadas:
        coordenada_backup = coordenadas_armazenadas[imagem_path]
        # Verifica se coordenada_backup é uma tupla válida
        if isinstance(coordenada_backup, tuple) and len(coordenada_backup) == 2:
            logging.info(f"Usando coordenadas de backup do JSON para '{imagem_path}': {coordenada_backup}")
            try:
                pyautogui.moveTo(coordenada_backup)
                pyautogui.click()
                logging.info(f"Clique realizado nas coordenadas de backup {coordenada_backup}.")
                return True
            except Exception as e:
                logging.error(f"Erro ao tentar clicar nas coordenadas de backup {coordenada_backup} para '{imagem_path}': {e}")
                return False
        else:
             logging.warning(f"Coordenadas de backup inválidas ({coordenada_backup}) encontradas para '{imagem_path}'. Backup não utilizado.")
             # Opcional: Remover a entrada inválida
             # del coordenadas_armazenadas[imagem_path]
             # salvar_coordenadas_json()

    elif usar_backup:
        logging.warning(f"Backup de coordenadas JSON não disponível para '{imagem_path}'.")

    logging.error(f"Falha ao clicar na imagem '{imagem_path}', mesmo com backup JSON (se aplicável).")
    return False

# Exemplo de uso (pode ser removido ou comentado na versão final)
if __name__ == '__main__':
    logging.info("--- Testando utils.py com persistência JSON ---")
    # Limpa o arquivo JSON para um teste limpo (opcional)
    # if os.path.exists(COORDENADAS_JSON_PATH):
    #     os.remove(COORDENADAS_JSON_PATH)
    # carregar_coordenadas_json() # Recarrega (estará vazio)

    # Simula a localização de uma imagem (substitua por um caminho real se for testar de verdade)
    img_teste = 'imagens_usuario/teste_simulado.png'
    print(f"Coordenadas antes do teste para {img_teste}: {coordenadas_armazenadas.get(img_teste)}")

    # Simula encontrar a imagem e clica (isso atualizaria e salvaria no JSON)
    # Para simular sem pyautogui real, podemos adicionar manualmente:
    # coordenadas_armazenadas[img_teste] = (100, 200)
    # salvar_coordenadas_json()
    # print(f"Coordenadas salvas para {img_teste}: {coordenadas_armazenadas.get(img_teste)}")

    # Simula falha ao encontrar e uso do backup
    # Supondo que 'clicar_por_imagem' falhe em encontrar, mas 'usar_backup=True'
    # e a coordenada (100, 200) foi salva anteriormente.
    # A função tentaria clicar em (100, 200).

    # Exemplo real (requer uma imagem 'placeholder.png' visível na tela):
    # img_real = 'placeholder.png'
    # if clicar_por_imagem(img_real, tentativas=1, confianca=0.9):
    #     logging.info(f"Teste de clique (ou backup JSON) para {img_real} bem-sucedido.")
    # else:
    #     logging.error(f"Teste de clique (ou backup JSON) para {img_real} falhou.")

    logging.info("--- Teste de utils.py concluído ---")


