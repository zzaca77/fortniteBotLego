#Em beta, está com alguns problemas  Por isso deixo avisado aqui para  quem entende tambem ! é uma funcionalida extra .  Toda vez que um erro aparecer o Bot toma providencia . 

# -*- coding: utf-8 -*-
import pyautogui
import time
import subprocess
import os
import logging
import threading

logger = logging.getLogger(__name__) 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def encontrar_imagem(imagem_path, confianca=0.9):
    if not imagem_path or not os.path.exists(imagem_path):
        #logger.debug(f"Caminho da imagem inválido ou não fornecido: {imagem_path}")
        return None
    try:
        posicao = pyautogui.locateCenterOnScreen(imagem_path, confidence=confianca)
        if posicao:
            logger.info(f"Imagem {os.path.basename(imagem_path)} encontrada em {posicao}.")
            return posicao
        #logger.debug(f"Imagem {os.path.basename(imagem_path)} não encontrada na tela.")
        return None
    except Exception as e:
        # Isso pode acontecer se o PyAutoGUI não puder acessar a tela (ex: Wayland sem config, ou erro de permissão)
        logger.error(f"Erro ao tentar encontrar a imagem {os.path.basename(imagem_path)} na tela: {e}")
        return None

def clicar_posicao(posicao):
    try:
        pyautogui.click(posicao)
        logger.info(f"Clicado na posição {posicao}.")
        return True
    except Exception as e:
        logger.error(f"Erro ao tentar clicar na posição {posicao}: {e}")
        return False

def monitorar_erros(imagem_erro_path_1, imagem_erro_path_2, imagem_botao_path, stop_event, restart_callback, intervalo_verificacao_segundos=300):
    logger.info(f"Monitor de Erro iniciado. Verificando a cada {intervalo_verificacao_segundos} segundos.")
    logger.info(f"Usando imagem de erro 1: {os.path.basename(imagem_erro_path_1) if imagem_erro_path_1 else 'Nenhuma'} ({imagem_erro_path_1})")
    if imagem_erro_path_2:
        logger.info(f"Usando imagem de erro 2: {os.path.basename(imagem_erro_path_2)} ({imagem_erro_path_2})")
    else:
        logger.info("Imagem de erro 2 não configurada.")
    logger.info(f"Usando imagem de botão: {os.path.basename(imagem_botao_path) if imagem_botao_path else 'Nenhuma'} ({imagem_botao_path})")

    # Validação das imagens essenciais
    if not imagem_erro_path_1 or not os.path.exists(imagem_erro_path_1):
        logger.error(f"Imagem de erro 1 não encontrada ou caminho inválido: {imagem_erro_path_1}. Monitoramento não pode iniciar.")
        return
    if not imagem_botao_path or not os.path.exists(imagem_botao_path):
        logger.error(f"Imagem do botão não encontrada ou caminho inválido: {imagem_botao_path}. Monitoramento não pode iniciar.")
        return
    # A imagem de erro 2 é opcional, mas se fornecida e não existir, logar um aviso.
    if imagem_erro_path_2 and not os.path.exists(imagem_erro_path_2):
        logger.warning(f"Imagem de erro 2 fornecida mas não encontrada em: {imagem_erro_path_2}. Será ignorada.")
        imagem_erro_path_2 = None # Trata como não configurada

    while not stop_event.is_set():
        imagem_detectada = None
        posicao_erro_detectada = None
        
        # Tenta encontrar a primeira imagem de erro
        #logger.debug(f"Verificando tela por imagem de erro 1: {os.path.basename(imagem_erro_path_1)}")
        pos_erro_1 = encontrar_imagem(imagem_erro_path_1, confianca=0.8)
        if pos_erro_1:
            imagem_detectada = imagem_erro_path_1
            posicao_erro_detectada = pos_erro_1
        
        # Se a primeira não foi encontrada e a segunda está configurada, tenta a segunda
        if not posicao_erro_detectada and imagem_erro_path_2:
            #logger.debug(f"Verificando tela por imagem de erro 2: {os.path.basename(imagem_erro_path_2)}")
            pos_erro_2 = encontrar_imagem(imagem_erro_path_2, confianca=0.8)
            if pos_erro_2:
                imagem_detectada = imagem_erro_path_2
                posicao_erro_detectada = pos_erro_2

        if posicao_erro_detectada:
            logger.info(f"Imagem de erro '{os.path.basename(imagem_detectada)}' detectada!")
            
            logger.info("Aguardando 1 minuto antes de clicar no botão de desconexão...")
            for _ in range(60):
                if stop_event.is_set(): break
                time.sleep(1)
            if stop_event.is_set(): 
                logger.info("Monitor de erro interrompido durante espera para clicar no botão.")
                break

            logger.info(f"Tentando encontrar e clicar no botão de desconexão: {os.path.basename(imagem_botao_path)}")
            posicao_botao = encontrar_imagem(imagem_botao_path, confianca=0.8)
            if posicao_botao:
                clicar_posicao(posicao_botao)
                logger.info("Botão de desconexão clicado.")
            else:
                logger.warning("Botão de desconexão não encontrado após detecção de erro. Tentando prosseguir com reinício.")
        
            logger.info("Aguardando 1 minuto antes de solicitar o reinício do start.py...")
            for _ in range(60):
                if stop_event.is_set(): break
                time.sleep(1)
            if stop_event.is_set(): 
                logger.info("Monitor de erro interrompido durante espera para reiniciar.")
                break
            
            logger.info("Sinalizando para o painel principal para tratar o reinício do bot...")
            if restart_callback:
                restart_callback()
            
            logger.info("Monitor de erro concluiu sua tarefa após acionar o reinício. Parando este ciclo de monitoramento.")
            break 
        else:
            #logger.debug("Nenhuma imagem de erro configurada foi detectada nesta verificação.")
            pass # Nenhuma imagem de erro encontrada, continua o loop após o intervalo
        
        # Pausa entre verificações normais
        #logger.debug(f"Aguardando {intervalo_verificacao_segundos}s para próxima verificação.")
        for i in range(intervalo_verificacao_segundos):
            if stop_event.is_set():
                break
            time.sleep(1)
        
        if stop_event.is_set():
            logger.info("Monitor de erro interrompido externamente durante o intervalo.")
            break

    logger.info("Monitor de Erro finalizado.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Crie caminhos de exemplo. Para teste, coloque as imagens em /home/ubuntu/upload
    img_erro_exemplo_1 = "/fortnite_bot/assets/images/disconet.png" # Imagem de erro principal
    img_erro_exemplo_2 = "/fortnite_bot/assets/images/ocorreu_umErro.png" # Segunda imagem de erro (opcional)
    img_botao_exemplo = "/fortnite_bot/assets/images/disconect _button.png"

    # Verifica se as imagens de teste existem
    if not os.path.exists(img_erro_exemplo_1):
        print(f"Para teste: Imagem de erro 1 de exemplo não encontrada em {img_erro_exemplo_1}")
        # exit()
    if img_erro_exemplo_2 and not os.path.exists(img_erro_exemplo_2):
        print(f"Para teste: Imagem de erro 2 de exemplo não encontrada em {img_erro_exemplo_2}. Será testada como None.")
        # img_erro_exemplo_2 = None # Descomente para testar sem a segunda imagem
    if not os.path.exists(img_botao_exemplo):
        print(f"Para teste: Imagem de botão de exemplo não encontrada em {img_botao_exemplo}")
        # exit()

    def mock_restart_callback():
        print("MOCK: Função de callback de reinício chamada!")

    print("Iniciando teste do monitor_erro.py. Pressione Ctrl+C para parar.")
    print(f"Testando com erro1='{img_erro_exemplo_1}', erro2='{img_erro_exemplo_2}', botao='{img_botao_exemplo}'")
    stop_event_teste = threading.Event()
    try:
        thread_teste = threading.Thread(target=monitorar_erros, 
                                        args=(img_erro_exemplo_1, img_erro_exemplo_2, img_botao_exemplo, 
                                              stop_event_teste, mock_restart_callback, 10)) # Intervalo de 10s para teste
        thread_teste.start()
        while thread_teste.is_alive():
            thread_teste.join(0.5)
    except KeyboardInterrupt:
        print("\nParando monitor de erro por interrupção do usuário...")
        stop_event_teste.set()
        if 'thread_teste' in locals() and thread_teste.is_alive():
            thread_teste.join()
    print("Teste do monitor_erro.py finalizado.")

