# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import json
import logging
import queue
import threading
import io
import time
import pyautogui
import random

# --- Configuracao de Logging ---
log_queue = queue.Queue()
log_level = logging.INFO  # Mudar para logging.DEBUG para mais detalhes
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

class TkinterLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        log_queue.put(f"{msg}")

logging.basicConfig(level=log_level, format=log_format)
logger = logging.getLogger("PainelPrincipal")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGENS_USUARIO_DIR = os.path.join(os.path.dirname(BASE_DIR), 'assets', 'images')
CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), 'config', 'config.json')

if not os.path.exists(IMAGENS_USUARIO_DIR):
    try:
        os.makedirs(IMAGENS_USUARIO_DIR)
        logger.info(f"Diretorio criado: {IMAGENS_USUARIO_DIR}")
    except OSError as e:
        logger.error(f"Erro ao criar diretorio {IMAGENS_USUARIO_DIR}: {e}")

caminhos_imagens = {
    'selecionar_mundo_1': None, 'selecionar_mundo_2': None, 'jogar_selecao': None,
    'resgatar': None, 'avaliar_pular': None, 'sair_menu': None,
    'voltar_lobby': None, 'confirmar_sim': None
}
tempo_execucao_segundos = 0



def carregar_configuracoes():
    global caminhos_imagens, tempo_execucao_segundos
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                loaded_paths = config.get('caminhos_imagens', {})
                for key in caminhos_imagens.keys():
                    v = loaded_paths.get(key)
                    if v:
                        path_to_check = v
                        if not os.path.isabs(v):
                            project_root_guess = os.path.dirname(BASE_DIR)
                            path_to_check = os.path.abspath(os.path.join(project_root_guess, v))
                        if os.path.exists(path_to_check):
                            caminhos_imagens[key] = path_to_check
                        else:
                            logger.warning(f"Caminho carregado para '{key}' nao encontrado: {path_to_check} (original: {v})")
                            caminhos_imagens[key] = None
                    else:
                        caminhos_imagens[key] = None

                tempo_execucao_segundos = config.get('tempo_execucao_segundos', 0)
                return True
    except Exception as e:
        logger.exception(f"Erro ao carregar config.json: {e}")
    return False

def salvar_configuracoes():
    global tempo_execucao_segundos
    # Handle tempo_execucao_segundos
    tempo_selecionado_str = combo_tempo.get()
    if tempo_selecionado_str == "Personalizado":
        try:
            tempo_minutos = int(entry_tempo_personalizado.get())
            if tempo_minutos > 0:
                tempo_execucao_segundos = tempo_minutos * 60
        except ValueError:
            pass  # Keep previous value if invalid
    elif tempo_selecionado_str:
        try:
            tempo_minutos = int(tempo_selecionado_str.split()[0])
            tempo_execucao_segundos = tempo_minutos * 60
        except (ValueError, IndexError):
            pass  # Keep previous value

    caminhos_relativos = {}
    project_root_for_rel_paths = os.path.dirname(BASE_DIR)
    for k, v in caminhos_imagens.items():
        if v and os.path.isabs(v):
            try:
                rel_path = os.path.relpath(v, project_root_for_rel_paths)
                caminhos_relativos[k] = rel_path
            except ValueError:
                caminhos_relativos[k] = v
        else:
            caminhos_relativos[k] = v

    config = {
        'caminhos_imagens': caminhos_relativos,
        'tempo_execucao_segundos': tempo_execucao_segundos
    }
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        logger.info("Configuracoes salvas em config.json")
    except Exception as e:
        logger.error(f"Erro ao salvar config.json: {e}")
        messagebox.showerror("Erro ao Salvar", f"Nao foi possivel salvar as configuracoes: {e}")

def selecionar_imagem(chave_imagem, label_status):
    filepath = filedialog.askopenfilename(
        title=f"Selecione a imagem para {chave_imagem}",
        initialdir=IMAGENS_USUARIO_DIR,
        filetypes=[("Arquivos PNG", "*.png")]
    )
    if filepath:
        filepath = os.path.abspath(filepath)
        caminhos_imagens[chave_imagem] = filepath
        label_status.config(text=os.path.basename(filepath), foreground='green')
        logger.info(f"Imagem {chave_imagem} selecionada: {filepath}")
        salvar_configuracoes()
    else:
        logger.warning(f"Nenhuma nova imagem selecionada para {chave_i
bot_thread = None
stop_bot_event = threading.Event()

def iniciar_bot():
    global bot_thread, stop_bot_event
    if bot_thread and bot_thread.is_alive():
        logger.warning("Tentativa de iniciar bot, mas uma thread anterior ainda parece existir. Tentando parar novamente.")
        parar_bot(notify_user=False)
        root.after(1000, _actually_start_bot)
        return
    _actually_start_bot()

def _actually_start_bot():
    global tempo_execucao_segundos, bot_thread, stop_bot_event
    logger.info("Procedendo com _actually_start_bot.")
    tempo_selecionado_str = combo_tempo.get()
    if tempo_selecionado_str == "Personalizado":
        try:
            tempo_minutos = int(entry_tempo_personalizado.get())
            if tempo_minutos <= 0:
                raise ValueError("Tempo deve ser positivo")
            tempo_execucao_segundos = tempo_minutos * 60
        except ValueError:
            logger.error("Tempo personalizado inválido inserido.")
            messagebox.showerror("Erro de Tempo", "Tempo personalizado inválido.")
            return
    elif tempo_selecionado_str:
        try:
            tempo_minutos = int(tempo_selecionado_str.split()[0])
            tempo_execucao_segundos = tempo_minutos * 60
        except (ValueError, IndexError):
            logger.error("Seleção de tempo inválida.")
            messagebox.showerror("Erro de Tempo", "Seleção de tempo inválida.")
            return
    else:
        logger.error("Nenhum tempo de execução selecionado.")
        messagebox.showerror("Erro de Tempo", "Selecione um tempo de execução.")
        return
    logger.info(f"Tempo de execução definido: {tempo_execucao_segundos} segundos.")

    imagens_std_necessarias = [\'selecionar_mundo_1\', \'selecionar_mundo_2\', \'jogar_selecao\', \'resgatar\', \'avaliar_pular\', \'sair_menu\', \'voltar_lobby\', \'confirmar_sim\']
    imagens_faltando = []
    for img_key in imagens_std_necessarias:
        path = caminhos_imagens.get(img_key)
        if not path or not os.path.exists(path):
            imagens_faltando.append(f"{img_key} (verifique aba \'Imagens Bot\')")

    if imagens_faltando:
        msg = f"Faltam imagens ou caminhos inválidos:\n- {\'; \'.join(imagens_faltando)}"
        logger.error(f"Erro de imagem ao iniciar: {msg}")
        messagebox.showerror("Erro de Imagem", msg)
        return

    salvar_configuracoes()
    try:
        stop_bot_event.clear()
        bot_thread = threading.Thread(target=run_bot_logic, args=(stop_bot_event, tempo_execucao_segundos, caminhos_imagens), daemon=True)
        bot_thread.start()
        logger.info("Thread do bot iniciada.")
        messagebox.showinfo("Iniciado", "O bot foi iniciado. Verifique \'Logs\'.")

        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Erro ao Iniciar", f"Não foi possível iniciar o bot: {e}")
        logger.exception("Falha ao iniciar o bot")
        bot_thread = None
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)

def run_bot_logic(stop_event, tempo_execucao_segundos, caminhos_imagens):
    """
    Função principal que executa a lógica do bot (anteriormente start.py e bot.py).
    Esta função será executada em uma thread separada.
    """
    logger.info("Lógica do bot iniciada na thread.")
    try:
        # PASSO 1: Iniciar a partida (lógica de start.py)
        logger.info("Iniciando a partida...")
        config_for_start = {"caminhos_imagens": {k: os.path.relpath(v, os.path.dirname(BASE_DIR)) if v else None for k, v in caminhos_imagens.items()}}
        if not iniciar_partida_interna(config_for_start, stop_event):
            logger.error("Não foi possível iniciar a partida. Encerrando a lógica do bot.")
            return
        
        if stop_event.is_set():
            logger.info("Sinal de parada recebido durante a inicialização da partida.")
            return

        logger.info("Partida iniciada. Aguardando 60 segundos para o carregamento...")
        for _ in range(60):
            if stop_event.is_set():
                logger.info("Sinal de parada recebido durante a espera de carregamento da partida.")
                return
            time.sleep(1)
        logger.info("Tempo de espera de carregamento concluído.")

        # PASSO 2: Realizar ações aleatórias (lógica de bot.py)
        logger.info("Pausa de 2 segundos para garantir que o jogo esteja em foco. Clique na janela do Fortnite se necessário.")
        time.sleep(2)
        if stop_event.is_set():
            logger.info("Sinal de parada recebido antes de iniciar ações aleatórias.")
            return

        logger.info("Iniciando ações aleatórias...")
        realizar_acoes_aleatorias(tempo_execucao_segundos, stop_event)
        
        if stop_event.is_set():
            logger.info("Sinal de parada recebido durante ações aleatórias.")
            return

        logger.info("Ações aleatórias concluídas. Preparando para sair da partida...")
        
        # PASSO 3: Sair da partida (lógica de sair.py)
        config_for_sair = carregar_configuracoes_sair()
        if config_for_sair:
            if executar_saida(config_for_sair):
                logger.info("Processo de saída concluído. Chamando retorno_lobby.py...")
                logger.info(f"Aguardando {TEMPO_ESPERA_ACOES} segundos antes de chamar retorno_lobby.py...")
                for _ in range(TEMPO_ESPERA_ACOES):
                    if stop_event.is_set():
                        logger.info("Sinal de parada recebido durante a espera antes de retorno_lobby.")
                        return
                    time.sleep(1)
                
                # PASSO 4: Retornar ao lobby (lógica de retorno_lobby.py)
                config_for_lobby = carregar_configuracoes_lobby()
                if config_for_lobby:
                    executar_acoes_lobby(config_for_lobby)
                    logger.info("Ações no lobby concluídas (ou tentativa de reinício realizada).")
                else:
                    logger.error("Não foi possível carregar as configurações para retorno_lobby.py.")
            else:
                logger.error("Falha no processo de saída da partida. retorno_lobby.py não será chamado.")
        else:
            logger.error("Não foi possível carregar as configurações para sair.py.")

    except Exception as e:
        logger.exception(f"Erro inesperado na lógica do bot: {e}")
    finally:
        logger.info("Lógica do bot finalizada na thread.")
        # Garante que os botões voltem ao normal se a thread terminar por conta própria
        root.after(0, lambda: start_button.config(state=tk.NORMAL))
        root.after(0, lambda: stop_button.config(state=tk.DISABLED))



def parar_bot(notify_user=True):
    global bot_thread, stop_bot_event
    logger.info("Função parar_bot chamada.")

    if bot_thread and bot_thread.is_alive():
        logger.info("Sinalizando a thread do bot para encerrar...")
        stop_bot_event.set()
        bot_thread.join(timeout=5) # Espera até 5 segundos pela thread
        if bot_thread.is_alive():
            logger.warning("A thread do bot não encerrou no tempo esperado.")
            if notify_user:
                messagebox.showwarning("Aviso", "A thread do bot pode não ter encerrado completamente.")
        else:
            logger.info("Thread do bot encerrada com sucesso.")
            if notify_user:
                messagebox.showinfo("Parado", "O bot foi encerrado.")
    else:
        logger.info("Nenhuma thread do bot ativa para parar.")

    # Garante que os botões voltem ao normal
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    bot_thread = None

def process_log_queue():
    while not log_queue.empty():
        try:
            message = log_queue.get_nowait()
            log_text_widget.insert(tk.END, message + "\n")
            log_text_widget.see(tk.END)
        except queue.Empty:
            pass
    root.after(100, process_log_queue)

def on_closing():
    logger.info("Fechando a aplicação. Tentando parar o bot...")
    parar_bot() # Chama parar_bot para garantir o encerramento antes de fechar
    root.destroy()

# --- Interface Grafica (Tkinter) ---
root = tk.Tk()
root.title("Painel de Controle do Bot")
root.geometry("800x600")

# Notebook (abas)
notebook = ttk.Notebook(root)
notebook.pack(pady=10, expand=True, fill="both")

# Aba de Controle
control_frame = ttk.LabelFrame(notebook)
notebook.add(control_frame, text="Controle")

# Seção de Tempo de Execução
tempo_frame = ttk.LabelFrame(control_frame, text="Tempo de Execução do Bot")
tempo_frame.pack(pady=10, padx=10, fill="x")

tempo_options = ["5 minutos", "10 minutos", "30 minutos", "1 hora", "2 horas", "Personalizado"]
combo_tempo = ttk.Combobox(tempo_frame, values=tempo_options, state="readonly")
combo_tempo.set(tempo_options[0]) # Default
combo_tempo.pack(pady=5, padx=10)

entry_tempo_personalizado = ttk.Entry(tempo_frame)
entry_tempo_personalizado.pack(pady=5, padx=10)
entry_tempo_personalizado.pack_forget() # Esconde por padrão

def toggle_tempo_personalizado(*args):
    if combo_tempo.get() == "Personalizado":
        entry_tempo_personalizado.pack(pady=5, padx=10)
    else:
        entry_tempo_personalizado.pack_forget()

combo_tempo.bind("<<ComboboxSelected>>", toggle_tempo_personalizado)

# Botões de Controle
button_frame = ttk.Frame(control_frame)
button_frame.pack(pady=20)

start_button = ttk.Button(button_frame, text="Iniciar Bot", command=iniciar_bot)
start_button.pack(side=tk.LEFT, padx=10)

stop_button = ttk.Button(button_frame, text="Parar Bot", command=parar_bot, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, padx=10)

# Aba de Imagens do Bot
images_frame = ttk.Frame(notebook)
notebook.add(images_frame, text="Imagens Bot")

# Funções auxiliares para criar a UI de seleção de imagem
def create_image_selection_row(parent_frame, label_text, image_key):
    row_frame = ttk.Frame(parent_frame)
    row_frame.pack(pady=5, fill="x", padx=10)

    label = ttk.Label(row_frame, text=label_text)
    label.pack(side=tk.LEFT, padx=5)

    status_label = ttk.Label(row_frame, text="Nenhuma selecionada", foreground='red')
    status_label.pack(side=tk.LEFT, expand=True, fill="x", padx=5)

    button = ttk.Button(row_frame, text="Selecionar", command=lambda: selecionar_imagem(image_key, status_label))
    button.pack(side=tk.RIGHT, padx=5)
    return status_label

image_status_labels = {}
image_status_labels['selecionar_mundo_1'] = create_image_selection_row(images_frame, "Selecionar Mundo 1:", 'selecionar_mundo_1')
image_status_labels['selecionar_mundo_2'] = create_image_selection_row(images_frame, "Selecionar Mundo 2:", 'selecionar_mundo_2')
image_status_labels['jogar_selecao'] = create_image_selection_row(images_frame, "Jogar Seleção:", 'jogar_selecao')
image_status_labels['resgatar'] = create_image_selection_row(images_frame, "Resgatar:", 'resgatar')
image_status_labels['avaliar_pular'] = create_image_selection_row(images_frame, "Avaliar/Pular:", 'avaliar_pular')
image_status_labels['sair_menu'] = create_image_selection_row(images_frame, "Sair Menu:", 'sair_menu')
image_status_labels['voltar_lobby'] = create_image_selection_row(images_frame, "Voltar Lobby:", 'voltar_lobby')
image_status_labels['confirmar_sim'] = create_image_selection_row(images_frame, "Confirmar Sim:", 'confirmar_sim')

def update_image_labels_on_load():
    for key, label_widget in image_status_labels.items():
        path = caminhos_imagens.get(key)
        if path and os.path.exists(path):
            label_widget.config(text=os.path.basename(path), foreground='green')
        else:
            label_widget.config(text="Nenhuma selecionada", foreground='red')

# Aba de Logs
log_frame = ttk.Frame(notebook)
notebook.add(log_frame, text="Logs")

log_text_widget = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=15)
log_text_widget.pack(pady=10, padx=10, expand=True, fill="both")

# Configuração inicial e loop principal
if carregar_configuracoes():
    update_image_labels_on_load()

if tempo_execucao_segundos > 0:
    tempo_min = tempo_execucao_segundos // 60
    tempo_str = f"{tempo_min} minutos"
    if tempo_options and tempo_str in tempo_options:
        combo_tempo.set(tempo_str)
    else:
        combo_tempo.set("Personalizado")
        entry_tempo_personalizado.insert(0, str(tempo_min))
        toggle_tempo_personalizado()
else:
    combo_tempo.set(tempo_options[1])  # Padrão 5 minutos

ui_log_handler = TkinterLogHandler(log_text_widget)
ui_log_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(ui_log_handler)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.after(100, process_log_queue)
root.mainloop()




# --- Funções e variáveis de utils.py ---
# Define o caminho para o arquivo JSON que armazenará as coordenadas
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
                logger.info(f"Coordenadas carregadas com sucesso de {COORDENADAS_JSON_PATH}")
        else:
            logger.info(f"Arquivo de coordenadas {COORDENADAS_JSON_PATH} não encontrado. Será criado um novo se necessário.")
            coordenadas_armazenadas = {}
    except json.JSONDecodeError:
        logger.error(f"Erro ao decodificar JSON de {COORDENADAS_JSON_PATH}. Iniciando com coordenadas vazias.")
        coordenadas_armazenadas = {}
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar coordenadas de {COORDENADAS_JSON_PATH}: {e}")
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
                    logger.warning(f"Valor inválido {value} para a chave {key} não será salvo no JSON.")
            elif isinstance(value, pyautogui.Point):
                 # Trata o tipo Point do pyautogui que pode ocorrer
                 coordenadas_para_salvar[key] = [value.x, value.y]
            else:
                logger.warning(f"Tipo de valor inesperado {type(value)} para a chave {key} não será salvo no JSON.")

        os.makedirs(os.path.dirname(COORDENADAS_JSON_PATH), exist_ok=True)
        with open(COORDENADAS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(coordenadas_para_salvar, f, indent=4, ensure_ascii=False)
        logger.info(f"Coordenadas salvas com sucesso em {COORDENADAS_JSON_PATH}")
    except Exception as e:
        logger.error(f"Erro inesperado ao salvar coordenadas em {COORDENADAS_JSON_PATH}: {e}")

# Carrega as coordenadas do JSON quando o módulo é importado pela primeira vez.
# Isso será chamado quando painel_unified.py for executado.
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
    logger.info(f"Tentando localizar e clicar na imagem: {imagem_path}")
    localizacao = None
    for tentativa in range(tentativas):
        try:
            # Tenta localizar a imagem na tela.
            localizacao = pyautogui.locateCenterOnScreen(imagem_path, confidence=confianca, grayscale=True)
            if localizacao:
                # Converte para tupla de inteiros para consistência
                coord_tuple = (int(localizacao.x), int(localizacao.y))
                logger.info(f"Imagem '{imagem_path}' encontrada na tentativa {tentativa + 1} em {coord_tuple}.")
                pyautogui.moveTo(coord_tuple)
                pyautogui.click()
                logger.info(f"Clique realizado em {coord_tuple}.")
                # Atualiza o backup de coordenadas e salva no JSON.
                if coordenadas_armazenadas.get(imagem_path) != coord_tuple:
                    coordenadas_armazenadas[imagem_path] = coord_tuple
                    logger.info(f"Coordenadas de backup para '{imagem_path}' atualizadas para {coord_tuple}. Salvando no JSON...")
                    salvar_coordenadas_json()
                else:
                    logger.info(f"Coordenadas para '{imagem_path}' ({coord_tuple}) já estavam atualizadas.")
                return True
            else:
                logger.warning(f"Imagem '{imagem_path}' não encontrada na tentativa {tentativa + 1}. Aguardando {intervalo}s.")
                time.sleep(intervalo)
        except pyautogui.ImageNotFoundException:
            logger.warning(f"Exceção ImageNotFoundException na tentativa {tentativa + 1} para '{imagem_path}'. Aguardando {intervalo}s.")
            time.sleep(intervalo)
        except Exception as e:
            logger.error(f"Erro inesperado ao tentar localizar '{imagem_path}' na tentativa {tentativa + 1}: {e}")
            time.sleep(intervalo)

    # Se a imagem não foi encontrada após todas as tentativas
    logger.warning(f"Imagem '{imagem_path}' não encontrada após {tentativas} tentativas.")

    # Tenta usar o backup de coordenadas (carregado do JSON) se habilitado e disponível
    if usar_backup and imagem_path in coordenadas_armazenadas:
        coordenada_backup = coordenadas_armazenadas[imagem_path]
        # Verifica se coordenada_backup é uma tupla válida
        if isinstance(coordenada_backup, tuple) and len(coordenada_backup) == 2:
            logger.info(f"Usando coordenadas de backup do JSON para '{imagem_path}': {coordenada_backup}")
            try:
                pyautogui.moveTo(coordenada_backup)
                pyautogui.click()
                logger.info(f"Clique realizado nas coordenadas de backup {coordenada_backup}.")
                return True
            except Exception as e:
                logger.error(f"Erro ao tentar clicar nas coordenadas de backup {coordenada_backup} para '{imagem_path}': {e}")
                return False
        else:
             logger.warning(f"Coordenadas de backup inválidas ({coordenada_backup}) encontradas para '{imagem_path}'. Backup não utilizado.")

    elif usar_backup:
        logger.warning(f"Backup de coordenadas JSON não disponível para '{imagem_path}'.")

    logger.error(f"Falha ao clicar na imagem '{imagem_path}', mesmo com backup JSON (se aplicável).")
    return False





# --- Funções de monitor_erro.py ---
def encontrar_imagem(imagem_path, confianca=0.9):
    if not imagem_path or not os.path.exists(imagem_path):
        return None
    try:
        posicao = pyautogui.locateCenterOnScreen(imagem_path, confidence=confianca)
        if posicao:
            logger.info(f"Imagem {os.path.basename(imagem_path)} encontrada em {posicao}.")
            return posicao
        return None
    except Exception as e:
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

    if not imagem_erro_path_1 or not os.path.exists(imagem_erro_path_1):
        logger.error(f"Imagem de erro 1 não encontrada ou caminho inválido: {imagem_erro_path_1}. Monitoramento não pode iniciar.")
        return
    if not imagem_botao_path or not os.path.exists(imagem_botao_path):
        logger.error(f"Imagem do botão não encontrada ou caminho inválido: {imagem_botao_path}. Monitoramento não pode iniciar.")
        return
    if imagem_erro_path_2 and not os.path.exists(imagem_erro_path_2):
        logger.warning(f"Imagem de erro 2 fornecida mas não encontrada em: {imagem_erro_path_2}. Será ignorada.")
        imagem_erro_path_2 = None

    while not stop_event.is_set():
        imagem_detectada = None
        posicao_erro_detectada = None
        
        pos_erro_1 = encontrar_imagem(imagem_erro_path_1, confianca=0.8)
        if pos_erro_1:
            imagem_detectada = imagem_erro_path_1
            posicao_erro_detectada = pos_erro_1
        
        if not posicao_erro_detectada and imagem_erro_path_2:
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
            pass
        
        for i in range(intervalo_verificacao_segundos):
            if stop_event.is_set():
                break
            time.sleep(1)
        
        if stop_event.is_set():
            logger.info("Monitor de erro interrompido externamente durante o intervalo.")
            break

    logger.info("Monitor de Erro finalizado.")





# --- Funções de retorno_lobby.py ---
TEMPO_ESPERA_LOBBY = 60

def _get_absolute_image_path_lobby(relative_path_from_config):
    """Converte um caminho relativo do config.json para um caminho absoluto."""
    if not relative_path_from_config:
        return None
    if os.path.isabs(relative_path_from_config):
        return relative_path_from_config # Já é absoluto
    # Caminhos no config.json são relativos ao PROJECT_ROOT_DIR
    abs_path = os.path.join(os.path.dirname(BASE_DIR), relative_path_from_config)
    return os.path.normpath(abs_path)

def carregar_configuracoes_lobby():
    """Carrega os caminhos das imagens necessárias do config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            caminhos_rel = config.get('caminhos_imagens', {})
            logger.info(f"Configurações carregadas com sucesso para retorno_lobby.py de {CONFIG_FILE}")
            
            caminhos_abs = {}
            for key, rel_path in caminhos_rel.items():
                caminhos_abs[key] = _get_absolute_image_path_lobby(rel_path)

            necessarias = ['resgatar', 'avaliar_pular', 'selecionar_mundo_1', 'selecionar_mundo_2', 'jogar_selecao']
            faltando = []
            for img_key in necessarias:
                abs_path = caminhos_abs.get(img_key)
                if not abs_path:
                    if img_key in caminhos_rel and caminhos_rel[img_key] is not None:
                        faltando.append(f"{img_key} (não configurado ou caminho relativo inválido: {caminhos_rel.get(img_key)})")
                elif not os.path.exists(abs_path):
                    faltando.append(f"{img_key} (arquivo não encontrado em: {abs_path}, relativo original: {caminhos_rel.get(img_key)})")
            
            if faltando:
                logger.warning(f"Imagens para retorno_lobby.py não encontradas ou inválidas: {', '.join(faltando)}")
            return caminhos_abs
    except FileNotFoundError:
        logger.error(f"Erro: Arquivo de configuração {CONFIG_FILE} não encontrado.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Erro: Falha ao decodificar o arquivo JSON: {CONFIG_FILE}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar configurações: {e}")
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

    logger.info(f"Usando imagem para Resgatar: {img_resgatar}")
    logger.info(f"Usando imagem para Avaliar/Pular: {img_avaliar_pular}")
    logger.info(f"Usando imagem para Selecionar Mundo 1: {img_selecionar_mundo_1}")
    logger.info(f"Usando imagem para Selecionar Mundo 2: {img_selecionar_mundo_2}")
    logger.info(f"Usando imagem para Jogar (Seleção): {img_jogar_selecao}")

    if img_resgatar and os.path.exists(img_resgatar):
        logger.info(f"Verificando por botão 'Resgatar' (imagem: {os.path.basename(img_resgatar)})...")
        for _ in range(3):
            if clicar_por_imagem(img_resgatar, tentativas=1, confianca=0.8, usar_backup=True):
                logger.info(f"Botão 'Resgatar' clicado. Aguardando {TEMPO_ESPERA_LOBBY} segundos...")
                time.sleep(TEMPO_ESPERA_LOBBY)
                break
            else:
                logger.info("Botão 'Resgatar' não encontrado nesta tentativa. Aguardando 5s...")
                time.sleep(5)
        else:
            logger.info("Botão 'Resgatar' não encontrado após várias tentativas.")
    elif img_resgatar:
        logger.warning(f"Imagem 'resgatar' configurada ({img_resgatar}) mas não encontrada no disco.")
    else:
        logger.info("Caminho para imagem 'resgatar' não fornecido ou inválido. Pulando esta etapa.")

    if img_avaliar_pular and os.path.exists(img_avaliar_pular):
        logger.info(f"Verificando por tela de avaliação / botão 'Pular' (imagem: {os.path.basename(img_avaliar_pular)})...")
        if clicar_por_imagem(img_avaliar_pular, tentativas=2, confianca=0.8, usar_backup=True):
            logger.info(f"Botão 'Pular' da avaliação clicado. Aguardando {TEMPO_ESPERA_LOBBY} segundos...")
            time.sleep(TEMPO_ESPERA_LOBBY)
        else:
            logger.info("Tela de avaliação / botão 'Pular' não encontrado.")
    elif img_avaliar_pular:
        logger.warning(f"Imagem 'avaliar_pular' configurada ({img_avaliar_pular}) mas não encontrada no disco.")
    else:
        logger.info("Caminho para imagem 'avaliar_pular' não fornecido ou inválido. Pulando esta etapa.")

    logger.info("Tentando reiniciar o ciclo: Selecionar Mundo e Jogar...")
    if img_selecionar_mundo_1 and os.path.exists(img_selecionar_mundo_1):
        if clicar_por_imagem(img_selecionar_mundo_1, tentativas=15, confianca=0.8, usar_backup=True):
            logger.info(f"Aguardando {TEMPO_ESPERA_LOBBY // 2}s após clicar em Selecionar Mundo...")
            time.sleep(TEMPO_ESPERA_LOBBY // 2)
            if img_selecionar_mundo_2 and os.path.exists(img_selecionar_mundo_2):
                logger.info("Selecionando o mundo (LEGO Fortnite)...")
                if clicar_por_imagem(img_selecionar_mundo_2, tentativas=15, confianca=0.8, usar_backup=True):
                    logger.info(f"Aguardando {TEMPO_ESPERA_LOBBY // 2}s após selecionar mundo...")
                    time.sleep(TEMPO_ESPERA_LOBBY // 2)
                    if img_jogar_selecao and os.path.exists(img_jogar_selecao):
                        logger.info("Clicando em 'Jogar' na seleção de mundo...")
                        if clicar_por_imagem(img_jogar_selecao, tentativas=15, confianca=0.8, usar_backup=True):
                            logger.info("Botão 'Jogar' (Seleção) clicado. O ciclo deve recomeçar.")
                            logger.info("Aguardando o jogo iniciar a próxima partida...")
                            time.sleep(TEMPO_ESPERA_LOBBY)
                            # chamar_script_bot() # Esta chamada será refatorada para chamar a função interna do bot
                            return 
                        else:
                            logger.error("Falha ao clicar no botão 'Jogar' (Seleção).")
                    else:
                        logger.error("Imagem 'jogar_selecao' não configurada ou não encontrada.")
                else:
                    logger.error("Falha ao selecionar o mundo (LEGO Fortnite).")
            else:
                logger.error("Imagem 'selecionar_mundo_2' não configurada ou não encontrada.")
        else:
            logger.error("Falha ao clicar em 'Selecionar Mundo 1'.")
    else:
        logger.error("Imagem 'selecionar_mundo_1' não configurada ou não encontrada. Não é possível reiniciar o ciclo.")

# A função chamar_script_bot será removida/refatorada na próxima fase.
# def chamar_script_bot():
#     pass





# --- Funções de sair.py ---
TEMPO_ESPERA_ACOES = 15

def _get_absolute_image_path_sair(relative_path_from_config):
    """Converte um caminho relativo do config.json para um caminho absoluto."""
    if not relative_path_from_config:
        return None
    if os.path.isabs(relative_path_from_config):
        return relative_path_from_config # Já é absoluto
    # Caminhos no config.json são relativos ao PROJECT_ROOT_DIR
    abs_path = os.path.join(os.path.dirname(BASE_DIR), relative_path_from_config)
    return os.path.normpath(abs_path)

def carregar_configuracoes_sair():
    """Carrega os caminhos das imagens necessárias do config.json."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            caminhos_rel = config.get('caminhos_imagens', {})
            logger.info(f"Configurações carregadas com sucesso para sair.py de {CONFIG_FILE}")
            
            caminhos_abs = {}
            for key, rel_path in caminhos_rel.items():
                caminhos_abs[key] = _get_absolute_image_path_sair(rel_path)

            necessarias = ['sair_menu', 'voltar_lobby', 'confirmar_sim']
            faltando = []
            for img_key in necessarias:
                abs_path = caminhos_abs.get(img_key)
                if not abs_path:
                    faltando.append(f"{img_key} (não configurado ou caminho relativo inválido: {caminhos_rel.get(img_key)})")
                elif not os.path.exists(abs_path):
                    faltando.append(f"{img_key} (arquivo não encontrado em: {abs_path}, relativo original: {caminhos_rel.get(img_key)})")
            
            if faltando:
                logger.warning(f"Imagens necessárias para sair.py não encontradas ou inválidas: {', '.join(faltando)}")
            return caminhos_abs
    except FileNotFoundError:
        logger.error(f"Erro: Arquivo de configuração {CONFIG_FILE} não encontrado.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Erro: Falha ao decodificar o arquivo JSON: {CONFIG_FILE}")
        return None
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar configurações: {e}")
        return None

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
        logger.error("Faltam caminhos de imagem essenciais (absolutos) para o processo de saída. Verifique logs anteriores de carregamento.")
        return False
    
    logger.info(f"Usando imagem para Sair Menu: {img_sair_menu}")
    logger.info(f"Usando imagem para Voltar ao Lobby: {img_voltar_lobby}")
    logger.info(f"Usando imagem para Confirmar Sim: {img_confirmar_sim}")

    try:
        time.sleep(2)
        logger.info("Pressionando ESC para abrir o menu...")
        pyautogui.keyDown('esc')
        time.sleep(0.05)
        pyautogui.keyUp('esc')
        logger.info("Aguardando 3 segundos após pressionar ESC...")
        time.sleep(3)

        logger.info(f"Tentando clicar em 'Sair' (imagem: {os.path.basename(img_sair_menu if img_sair_menu else 'N/A')})...")
        if clicar_por_imagem(img_sair_menu, tentativas=3, confianca=0.8):
            logger.info(f"Botão 'Sair' clicado. Aguardando {TEMPO_ESPERA_ACOES} segundos...")
            time.sleep(TEMPO_ESPERA_ACOES)

            logger.info(f"Tentando clicar em 'Voltar ao Lobby' (imagem: {os.path.basename(img_voltar_lobby if img_voltar_lobby else 'N/A')})...")
            if clicar_por_imagem(img_voltar_lobby, tentativas=3, confianca=0.8):
                logger.info(f"Botão 'Voltar ao Lobby' clicado. Aguardando {TEMPO_ESPERA_ACOES} segundos...")
                time.sleep(TEMPO_ESPERA_ACOES)

                logger.info(f"Tentando clicar em 'Sim' para confirmação (imagem: {os.path.basename(img_confirmar_sim if img_confirmar_sim else 'N/A')})...")
                clicou_sim = clicar_por_imagem(img_confirmar_sim, tentativas=2, confianca=0.8, usar_backup=False)
                if clicou_sim:
                    logger.info("Botão 'Sim' de confirmação clicado.")
                    logger.info(f"Aguardando {TEMPO_ESPERA_ACOES // 2} segundos extras...")
                    time.sleep(TEMPO_ESPERA_ACOES // 2)
                else:
                    logger.info("Botão 'Sim' não encontrado ou não foi necessário.")

                logger.info("Processo de saída iniciado com sucesso.")
                return True
            else:
                logger.error(f"Falha ao clicar em 'Voltar ao Lobby' ({os.path.basename(img_voltar_lobby if img_voltar_lobby else 'N/A')}).")
                return False
        else:
            logger.error(f"Falha ao clicar em 'Sair' no menu ({os.path.basename(img_sair_menu if img_sair_menu else 'N/A')}).")
            return False
    except Exception as e:
        logger.exception("Erro inesperado durante o processo de saída.")
        return False

# A função chamar_script_retorno_lobby será removida/refatorada na próxima fase.
# def chamar_script_retorno_lobby():
#     pass




import pyautogui
import random

# --- Funções e variáveis de bot.py ---

pyautogui.FAILSAFE = False

def carregar_configuracoes_bot():
    """Carrega as configurações do config.json, especificamente o tempo de execução."""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            tempo_segundos = config.get('tempo_execucao_segundos')
            if tempo_segundos is None or not isinstance(tempo_segundos, int) or tempo_segundos <= 0:
                logger.error("Tempo de execução inválido ou não encontrado em config.json. Usando padrão de 300s (5 min).")
                return 300
            logger.info(f"Configurações carregadas para bot.py. Tempo de execução: {tempo_segundos}s")
            return tempo_segundos
    except FileNotFoundError:
        logger.error(f"Erro: Arquivo de configuração {CONFIG_FILE} não encontrado. Usando padrão de 300s.")
        return 300
    except json.JSONDecodeError:
        logger.error(f"Erro: Falha ao decodificar {CONFIG_FILE}. Usando padrão de 300s.")
        return 300
    except Exception as e:
        logger.error(f"Erro inesperado ao carregar config: {e}. Usando padrão de 300s.")
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

def realizar_acoes_aleatorias(duracao_total_segundos, stop_event):
    """
    Executa ações aleatórias aprimoradas, incluindo combinações de teclas e sequências,
    pelo tempo especificado.
    """
    tempo_inicio = time.time()
    tempo_fim = tempo_inicio + duracao_total_segundos

    logger.info(f"Iniciando ciclo de ações aleatórias por {duracao_total_segundos} segundos.")

    acoes_possiveis = [
        ('mover_curto', 12), ('mover_longo', 6), ('correr_curto', 10), ('correr_longo', 5),
        ('pular', 7), ('agachar_toggle', 5), ('agachar_hold', 3), ('interagir', 4),
        ('recarregar', 3), ('mover_camera_suave', 18), ('mover_camera_rapido', 7),
        ('pausa_curta', 12), ('pausa_media', 8),
        ('seq_mover_olhar', 9), ('seq_correr_parar_olhar', 8)
    ]
    nomes_acoes = [a[0] for a in acoes_possiveis]
    pesos_acoes = [a[1] for a in acoes_possiveis]

    while time.time() < tempo_fim and not stop_event.is_set():
        tempo_restante = tempo_fim - time.time()
        if tempo_restante <= 0:
            break

        acao_escolhida = random.choices(nomes_acoes, weights=pesos_acoes, k=1)[0]
        logger.debug(f"Tempo restante: {tempo_restante:.2f}s. Próxima ação: {acao_escolhida}")

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
            logger.error(f"Erro durante a execução da ação {acao_escolhida}: {e}")
            tempo_restante_ex = tempo_fim - time.time()
            time.sleep(max(0, min(0.5, tempo_restante_ex)))

    logger.info("Tempo de execução do bot concluído.")

# A função chamar_script_sair será refatorada para chamar a função interna de sair.
# def chamar_script_sair():
#     pass





# --- Funções de start.py ---
def iniciar_partida_interna(config, stop_event):
    """
    Tenta iniciar a partida usando o fluxo alternativo de 'Selecionar Mundo',
    utilizando clicar_por_imagem com muitas tentativas e backup JSON.

    Args:
        config (dict): Dicionário contendo os caminhos das imagens e outras configs.
        stop_event (threading.Event): Evento para sinalizar a parada da thread.

    Returns:
        bool: True se a partida foi iniciada com sucesso, False caso contrário.
    """
    caminhos_rel = config.get("caminhos_imagens", {})
    
    img_selecionar_mundo_1_rel = caminhos_rel.get("selecionar_mundo_1")
    img_selecionar_mundo_2_rel = caminhos_rel.get("selecionar_mundo_2")
    img_jogar_selecao_rel = caminhos_rel.get("jogar_selecao")

    img_selecionar_mundo_1 = _get_absolute_image_path_lobby(img_selecionar_mundo_1_rel)
    img_selecionar_mundo_2 = _get_absolute_image_path_lobby(img_selecionar_mundo_2_rel)
    img_jogar_selecao = _get_absolute_image_path_lobby(img_jogar_selecao_rel)

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
            logger.error(f"Caminho para imagem '{name}' não configurado ou inválido no config.json.")
            return False
        if not os.path.exists(path):
            logger.error(f"Imagem '{name}' não encontrada no caminho: {path} (Relativo original: {caminhos_rel.get(name.lower().replace(' ', '_').replace('(', '').replace(')', ''))}). Verifique o config.json e a existência do arquivo.")
            return False
        logger.info(f"Caminho absoluto para '{name}': {path}")

    logger.info("Fluxo Secundário: Sempre indo para a seleção de mundo.")
    time.sleep(2)

    logger.info(f"Tentando clicar em 'Selecionar Mundo 1' ({os.path.basename(img_selecionar_mundo_1)})...")
    if clicar_por_imagem(img_selecionar_mundo_1, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
        time.sleep(2)
        if stop_event.is_set(): return False
        logger.info(f"Fluxo Secundário: Selecionar o mundo (LEGO Fortnite) ({os.path.basename(img_selecionar_mundo_2)})...")
        if clicar_por_imagem(img_selecionar_mundo_2, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
            time.sleep(4)
            if stop_event.is_set(): return False
            logger.info(f"Fluxo Secundário: Clicar em 'Jogar' na seleção de mundo ({os.path.basename(img_jogar_selecao)})...")
            time.sleep(2)
            if stop_event.is_set(): return False
            if clicar_por_imagem(img_jogar_selecao, tentativas=TENTATIVAS_ALTAS, intervalo=INTERVALO_TENTATIVAS, confianca=CONFIANCA_IMAGEM, usar_backup=True):
                logger.info("Fluxo Secundário concluído. Botão 'Jogar' (Seleção) clicado.")
                return True
            else:
                logger.error(f"Falha ao clicar no botão 'Jogar' (Seleção) ({os.path.basename(img_jogar_selecao)}). Tentativas esgotadas.")
                return False
        else:
            logger.error(f"Falha ao selecionar o mundo (LEGO Fortnite) ({os.path.basename(img_selecionar_mundo_2)}). Tentativas esgotadas.")
            return False
    else:
        logger.error(f"Falha ao clicar em 'Selecionar Mundo 1' ({os.path.basename(img_selecionar_mundo_1)}). Tentativas esgotadas.")
        return False

# A função chamar_script_bot será refatorada para chamar a função interna do bot.
# def chamar_script_bot():
#     pass


