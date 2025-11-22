# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import json
import logging
import signal # Adicionado para constantes de sinal
import queue
import threading
import io
import time # Adicionado para sleep
import psutil # Importado para gerenciamento de processos filhos

# Importar o modulo de monitoramento de erro
from monitor_erro import monitorar_erros

# --- Configuracao de Logging ---
log_queue = queue.Queue()
log_level = logging.INFO # Mudar para logging.DEBUG para mais detalhes
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
    'voltar_lobby': None, 'confirmar_sim': None,
    'imagem_erro_monitor': None,
    'imagem_erro_monitor_2': None,
    'imagem_botao_monitor': None
}
tempo_execucao_segundos = 0
intervalo_monitor_erro_minutos = 1
bot_process = None
monitor_thread_stdout = None
monitor_thread_stderr = None
stop_monitoring_bot_output = threading.Event()

monitor_erro_thread = None
stop_monitor_erro_event = threading.Event()
monitor_status_label_text = None
combo_intervalo_monitor = None
monitor_erro_ativo_var = None # Sera tk.BooleanVar()

def carregar_configuracoes():
    global caminhos_imagens, tempo_execucao_segundos, intervalo_monitor_erro_minutos, combo_intervalo_monitor, monitor_erro_ativo_var
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                loaded_paths = config.get('caminhos_imagens', {})
                for key in caminhos_imagens.keys():
                    v = loaded_paths.get(key)
                    if v:
                        path_to_check = v
                        # Se o caminho no JSON for relativo, assume-se que e relativo e pasta pai da pasta 'src'
                        if not os.path.isabs(v):
                            project_root_guess = os.path.dirname(BASE_DIR) # pasta 'src'
                            path_to_check = os.path.abspath(os.path.join(project_root_guess, v))
                        
                        if os.path.exists(path_to_check):
                           caminhos_imagens[key] = path_to_check
                        else:
                           logger.warning(f"Caminho carregado para '{key}' nao encontrado: {path_to_check} (original: {v})")
                           caminhos_imagens[key] = None
                    else:
                        caminhos_imagens[key] = None

                tempo_execucao_segundos = config.get('tempo_execucao_segundos', 0)
                intervalo_monitor_erro_minutos = config.get('intervalo_monitor_erro_minutos', 1)
                
                monitor_ativo_config = config.get('monitor_erro_ativo', True)
                if monitor_erro_ativo_var: # Garante que a variavel Tkinter exista
                    monitor_erro_ativo_var.set(monitor_ativo_config)

                logger.info("Configuracoes carregadas de config.json")

                if combo_intervalo_monitor:
                    combo_intervalo_monitor.set(f"{intervalo_monitor_erro_minutos} minuto(s)")
                return True
    except Exception as e:
        logger.exception(f"Erro ao carregar config.json: {e}")
    return False

def salvar_configuracoes():
    global tempo_execucao_segundos, intervalo_monitor_erro_minutos, monitor_erro_ativo_var
    # ... (logica de tempo)
    tempo_selecionado_str = combo_tempo.get()
    if tempo_selecionado_str == "Personalizado":
        try:
            tempo_minutos = int(entry_tempo_personalizado.get())
            if tempo_minutos > 0:
                tempo_execucao_segundos = tempo_minutos * 60
        except ValueError:
            pass # Mantem valor anterior se invalido
    elif tempo_selecionado_str:
        try:
            tempo_minutos = int(tempo_selecionado_str.split()[0])
            tempo_execucao_segundos = tempo_minutos * 60
        except (ValueError, IndexError):
            pass # Mantem valor anterior

    if combo_intervalo_monitor:
        intervalo_selecionado_str = combo_intervalo_monitor.get()
        if intervalo_selecionado_str:
            try:
                intervalo_monitor_erro_minutos = int(intervalo_selecionado_str.split()[0])
            except (ValueError, IndexError):
                logger.error(f"Valor invalido para intervalo do monitor: {intervalo_selecionado_str}")

    caminhos_relativos = {}
    project_root_for_rel_paths = os.path.dirname(BASE_DIR) # Pasta pai de 'src'
    for k, v in caminhos_imagens.items():
        if v and os.path.isabs(v):
            try:
                rel_path = os.path.relpath(v, project_root_for_rel_paths)
                caminhos_relativos[k] = rel_path
            except ValueError: # Drives diferentes no Windows
                caminhos_relativos[k] = v
        else:
            caminhos_relativos[k] = v # Mantem None ou ja relativo

    config = {
        'caminhos_imagens': caminhos_relativos,
        'tempo_execucao_segundos': tempo_execucao_segundos,
        'intervalo_monitor_erro_minutos': intervalo_monitor_erro_minutos,
        'monitor_erro_ativo': monitor_erro_ativo_var.get() if monitor_erro_ativo_var else True
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
    # ... (codigo existente)
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
        logger.warning(f"Nenhuma nova imagem selecionada para {chave_imagem}.")

def monitor_process_output(process_obj, stream_name, prefix):
    # ... (codigo existente)
    global stop_monitoring_bot_output
    try:
        stream = getattr(process_obj, stream_name)
        with io.TextIOWrapper(stream, encoding='utf-8', errors='replace') as text_stream:
            for line in iter(text_stream.readline, ''):
                if stop_monitoring_bot_output.is_set():
                    logger.info(f"Monitoramento de {stream_name} do processo {prefix} (PID: {process_obj.pid}) interrompido.")
                    break
                if line:
                    log_queue.put(f"[{prefix}] {line.strip()}")
                else: # EOF
                    break
    except ValueError: # Can happen if stream is closed
        logger.info(f"Stream {stream_name} para {prefix} (PID: {process_obj.pid if process_obj else 'N/A'}) fechado.")
    except Exception as e:
        logger.error(f"Erro ao monitorar {stream_name} do processo {prefix} (PID: {process_obj.pid if process_obj else 'N/A'}): {e}")
    finally:
        logger.info(f"Thread de monitoramento para {stream_name} do processo {prefix} (PID: {process_obj.pid if process_obj else 'N/A'}) finalizada.")

def handle_bot_restart_request():
    logger.info("Monitor de erro solicitou reinício do bot.")
    log_queue.put("[PAINEL] Monitor de erro detectou problema. Agendando reinício do bot.")
    root.after(0, _perform_restart_sequence)
    if monitor_status_label_text:
        monitor_status_label_text.set("Monitor: Reiniciando bot...")

def _perform_restart_sequence():
    logger.info("Executando sequência de reinício na thread principal.")
    if bot_process and bot_process.poll() is None:
        logger.info("Parando o bot atual antes de reiniciar...")
        parar_bot(notify_user=False)
        logger.info("Bot parado. Agendando início de novo bot após um breve intervalo.")
        root.after(2000, iniciar_bot)
    else:
        logger.info("Bot não estava rodando ou já foi encerrado. Tentando iniciar novo bot diretamente.")
        iniciar_bot()

def iniciar_bot():
    global bot_process
    if bot_process and bot_process.poll() is None:
        logger.warning("Tentativa de iniciar bot, mas um processo anterior ainda parece existir. Tentando parar novamente.")
        parar_bot(notify_user=False)
        root.after(1000, _actually_start_bot)
        return
    _actually_start_bot()

def _actually_start_bot():
    global tempo_execucao_segundos, bot_process, monitor_thread_stdout, monitor_thread_stderr, monitor_erro_thread, stop_monitoring_bot_output, stop_monitor_erro_event, intervalo_monitor_erro_minutos, monitor_erro_ativo_var
    logger.info("Procedendo com _actually_start_bot.")
    # ... (lógica de tempo)
    tempo_selecionado_str = combo_tempo.get()
    if tempo_selecionado_str == "Personalizado":
        try:
            tempo_minutos = int(entry_tempo_personalizado.get())
            if tempo_minutos <= 0: raise ValueError("Tempo deve ser positivo")
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

    intervalo_selecionado_str = combo_intervalo_monitor.get()
    try:
        intervalo_monitor_erro_minutos = int(intervalo_selecionado_str.split()[0])
    except (ValueError, IndexError):
        logger.error(f"Valor inválido para intervalo do monitor: {intervalo_selecionado_str}. Usando padrão: 1 min.")
        intervalo_monitor_erro_minutos = 1
        combo_intervalo_monitor.set("1 minuto(s)")

    imagens_std_necessarias = ['selecionar_mundo_1', 'selecionar_mundo_2', 'jogar_selecao', 'resgatar', 'avaliar_pular', 'sair_menu', 'voltar_lobby', 'confirmar_sim']
    imagens_faltando = []
    for img_key in imagens_std_necessarias:
        path = caminhos_imagens.get(img_key)
        if not path or not os.path.exists(path):
             imagens_faltando.append(f"{img_key} (verifique aba 'Imagens Bot')")

    if monitor_erro_ativo_var and monitor_erro_ativo_var.get():
        img_erro_mon = caminhos_imagens.get('imagem_erro_monitor')
        img_erro_mon_2 = caminhos_imagens.get('imagem_erro_monitor_2')
        img_botao_mon = caminhos_imagens.get('imagem_botao_monitor')
        if not img_erro_mon or not os.path.exists(img_erro_mon):
            imagens_faltando.append("Imagem de Erro 1 (Monitor Ativo - aba 'Monitor de Erro')")
        if img_erro_mon_2 and not os.path.exists(img_erro_mon_2):
            imagens_faltando.append("Imagem de Erro 2 (Monitor Ativo - caminho inválido, aba 'Monitor de Erro')")
        if not img_botao_mon or not os.path.exists(img_botao_mon):
            imagens_faltando.append("Imagem de Botão (Monitor Ativo - aba 'Monitor de Erro')")

    if imagens_faltando:
        msg = f"Faltam imagens ou caminhos inválidos:\n- {'; '.join(imagens_faltando)}"
        logger.error(f"Erro de imagem ao iniciar: {msg}")
        messagebox.showerror("Erro de Imagem", msg)
        return

    salvar_configuracoes()
    try:
        script_path = os.path.join(BASE_DIR, 'start.py')
        if not os.path.exists(script_path):
             logger.error(f"Arquivo 'start.py' não encontrado em {BASE_DIR}.")
             messagebox.showerror("Erro de Arquivo", f"'start.py' não encontrado.")
             return

        logger.info(f"Iniciando o script {script_path}...")
        python_executable = 'python3' if os.name != 'nt' else 'python'
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        bot_process = subprocess.Popen(
            [python_executable, script_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            creationflags=creationflags, cwd=BASE_DIR,
            start_new_session=True if os.name != 'nt' else False
        )
        pgid_info = f", PGID: {os.getpgid(bot_process.pid)}" if os.name != 'nt' else ""
        logger.info(f"Processo start.py (PID: {bot_process.pid}{pgid_info}) iniciado.")
        messagebox.showinfo("Iniciado", f"O bot foi iniciado (PID: {bot_process.pid}). Verifique 'Logs'.")

        stop_monitoring_bot_output.clear()
        monitor_thread_stdout = threading.Thread(target=monitor_process_output, args=(bot_process, 'stdout', 'BOT'), daemon=True)
        monitor_thread_stderr = threading.Thread(target=monitor_process_output, args=(bot_process, 'stderr', 'BOT-ERR'), daemon=True)
        monitor_thread_stdout.start()
        monitor_thread_stderr.start()

        if monitor_erro_ativo_var and monitor_erro_ativo_var.get():
            img_erro_mon = caminhos_imagens.get('imagem_erro_monitor')
            img_erro_mon_2 = caminhos_imagens.get('imagem_erro_monitor_2')
            img_botao_mon = caminhos_imagens.get('imagem_botao_monitor')
            stop_monitor_erro_event.clear()
            intervalo_monitor_segundos = intervalo_monitor_erro_minutos * 60
            logger.info(f"Iniciando monitor de erro ({intervalo_monitor_segundos}s). Imagens: E1='{os.path.basename(img_erro_mon if img_erro_mon else '')}', E2='{os.path.basename(img_erro_mon_2 if img_erro_mon_2 else '')}', BTN='{os.path.basename(img_botao_mon if img_botao_mon else '')}'")
            monitor_erro_thread = threading.Thread(target=monitorar_erros,
                                                 args=(img_erro_mon, img_erro_mon_2, img_botao_mon, stop_monitor_erro_event, handle_bot_restart_request, intervalo_monitor_segundos),
                                                 daemon=True)
            monitor_erro_thread.start()
            if monitor_status_label_text: monitor_status_label_text.set("Monitor: Ativo")
        else:
            if monitor_status_label_text: monitor_status_label_text.set("Monitor: Desativado (Config)")
            logger.info("Monitor de erro desativado por configuração.")

        start_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror("Erro ao Iniciar", f"Não foi possível iniciar o bot: {e}")
        logger.exception("Falha ao iniciar start.py")
        bot_process = None
        if monitor_status_label_text:
            status_val = "Monitor: Desativado (Config)" if monitor_erro_ativo_var and not monitor_erro_ativo_var.get() else "Monitor: Inativo (Erro Bot)"
            monitor_status_label_text.set(status_val)
        start_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)

def _kill_proc_tree(pid, pgid=None, including_parent=True):
    logger.debug(f"Tentando matar árvore de processos para PID: {pid}, PGID: {pgid}")
    killed_pg = False
    if os.name != 'nt' and pgid is not None and pgid != 0 and pgid != os.getpid(): # Não matar o próprio painel
        try:
            logger.info(f"Tentando matar grupo de processos (PGID: {pgid}) com SIGTERM...")
            os.killpg(pgid, signal.SIGTERM)
            time.sleep(0.5) # Dar tempo para terminar graciosamente
            try: # Checar se ainda existe
                os.killpg(pgid, 0) # Testa se o processo existe
                logger.info(f"Grupo de processos (PGID: {pgid}) ainda existe. Enviando SIGKILL...")
                os.killpg(pgid, signal.SIGKILL)
                killed_pg = True
            except ProcessLookupError:
                logger.info(f"Grupo de processos (PGID: {pgid}) encerrado após SIGTERM.")
                killed_pg = True 
        except ProcessLookupError:
            logger.warning(f"Grupo de processos (PGID: {pgid}) não encontrado. Provavelmente já encerrado.")
            killed_pg = True # Considera como se tivesse sido morto
        except Exception as e:
            logger.error(f"Erro ao tentar os.killpg no PGID {pgid}: {e}")
    
    if killed_pg and os.name != 'nt':
        logger.info(f"Grupo de processos {pgid} tratado. Verificando processo pai {pid} individualmente se necessário.")
        # Se o pai (líder do grupo) não morreu com killpg (raro), psutil abaixo pode pegar.

    # Usar psutil como fallback ou para Windows, ou se pgid não funcionou completamente
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        logger.debug(f"Filhos de {pid} (psutil): {[c.pid for c in children]}")
        for child in children:
            try:
                logger.info(f"Terminando filho (PID: {child.pid}) com psutil.terminate()...")
                child.terminate()
            except psutil.NoSuchProcess: pass
            except Exception as e: logger.error(f"Erro psutil.terminate() filho {child.pid}: {e}")
        
        gone, alive = psutil.wait_procs(children, timeout=2)
        for child_alive in alive:
            try:
                logger.warning(f"Filho (PID: {child_alive.pid}) ainda vivo. Forçando psutil.kill()...")
                child_alive.kill()
            except psutil.NoSuchProcess: pass
            except Exception as e: logger.error(f"Erro psutil.kill() filho {child_alive.pid}: {e}")

        if including_parent:
            try:
                logger.info(f"Terminando pai (PID: {parent.pid}) com psutil.terminate()...")
                parent.terminate()
                parent.wait(timeout=2)
                if parent.is_running():
                    logger.warning(f"Pai (PID: {parent.pid}) ainda vivo. Forçando psutil.kill()...")
                    parent.kill()
                    parent.wait(timeout=1)
            except psutil.NoSuchProcess: logger.warning(f"Pai (PID: {parent.pid}) não encontrado por psutil.")
            except Exception as e: logger.error(f"Erro psutil.terminate/kill() pai {parent.pid}: {e}")
    except psutil.NoSuchProcess:
        logger.warning(f"Processo pai (PID: {pid}) não encontrado por psutil para matar árvore.")
    logger.debug(f"Finalizada tentativa de matar árvore para PID: {pid}")

def parar_bot(notify_user=True):
    global bot_process, monitor_thread_stdout, monitor_thread_stderr, monitor_erro_thread, stop_monitoring_bot_output, stop_monitor_erro_event, monitor_erro_ativo_var
    logger.info("Função parar_bot chamada.")
    stop_monitor_erro_event.set()
    if monitor_erro_thread and monitor_erro_thread.is_alive():
        logger.info("Aguardando thread do monitor de erro parar...")
        monitor_erro_thread.join(timeout=3)
        if monitor_erro_thread.is_alive(): logger.warning("Thread do monitor não encerrou a tempo.")
    monitor_erro_thread = None
    if monitor_status_label_text:
        status_val = "Monitor: Desativado (Config)" if monitor_erro_ativo_var and not monitor_erro_ativo_var.get() else "Monitor: Inativo"
        monitor_status_label_text.set(status_val)

    if bot_process and bot_process.poll() is None:
        pid_to_kill = bot_process.pid
        pgid_to_kill = None
        if os.name != 'nt':
            try: pgid_to_kill = os.getpgid(pid_to_kill)
            except ProcessLookupError: logger.warning(f"PGID para {pid_to_kill} não encontrado.")
        
        logger.info(f"Processo bot (PID: {pid_to_kill}, PGID: {pgid_to_kill}) ativo. Encerrando...")
        _kill_proc_tree(pid_to_kill, pgid=pgid_to_kill, including_parent=True)
        time.sleep(0.5) # Dar tempo para SO atualizar
        try:
            if psutil.Process(pid_to_kill).is_running(): # Recheca
                logger.error(f"Processo (PID: {pid_to_kill}) ainda rodando após kill tree!")
        except psutil.NoSuchProcess:
            logger.info(f"Processo (PID: {pid_to_kill}) não encontrado após kill (esperado).")
        if notify_user: messagebox.showinfo("Parado", f"Bot (PID: {pid_to_kill}) sinalizado para encerrar.")
    else:
        logger.info("Nenhum processo do bot ativo para parar.")

    stop_monitoring_bot_output.set()
    # ... (joins das threads de output) ...
    if monitor_thread_stdout and monitor_thread_stdout.is_alive(): monitor_thread_stdout.join(timeout=1)
    if monitor_thread_stderr and monitor_thread_stderr.is_alive(): monitor_thread_stderr.join(timeout=1)
    monitor_thread_stdout, monitor_thread_stderr, bot_process = None, None, None
    logger.info("Referências do processo e threads de output limpas.")
    start_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

def on_closing():
    # ... (código existente, garantir que parar_bot seja chamado) ...
    global bot_process
    logger.info("Tentativa de fechar a janela.")
    if bot_process and bot_process.poll() is None:
        if messagebox.askyesno("Sair", "O bot ainda está em execução. Deseja pará-lo e sair?"):
            logger.info("Usuário escolheu parar o bot e sair.")
            parar_bot(notify_user=False)
            root.after(500, root.destroy) # Pequeno delay para garantir parada
        else:
            logger.info("Usuário cancelou o fechamento da janela.")
            return
    else:
        logger.info("Fechando a janela (bot não rodando ou já parado).")
        # Limpeza final de threads se ainda existirem (ex: monitor se bot nunca iniciou)
        stop_monitor_erro_event.set()
        if monitor_erro_thread and monitor_erro_thread.is_alive(): monitor_erro_thread.join(timeout=1)
        stop_monitoring_bot_output.set()
        if monitor_thread_stdout and monitor_thread_stdout.is_alive(): monitor_thread_stdout.join(timeout=1)
        if monitor_thread_stderr and monitor_thread_stderr.is_alive(): monitor_thread_stderr.join(timeout=1)
        root.destroy()

def process_log_queue():
    # ... (código existente) ...
    try:
        while True:
            record = log_queue.get(block=False)
            log_text_widget.configure(state='normal')
            log_text_widget.insert(tk.END, record + '\n')
            log_text_widget.configure(state='disabled')
            log_text_widget.yview(tk.END)
            log_queue.task_done()
    except queue.Empty:
        pass
    if root.winfo_exists(): # Evita erro se root já foi destruído
        root.after(100, process_log_queue)

def on_monitor_enable_change():
    global monitor_erro_thread, stop_monitor_erro_event, intervalo_monitor_erro_minutos, monitor_erro_ativo_var, monitor_status_label_text
    salvar_configuracoes()
    is_monitor_supposed_to_be_active = monitor_erro_ativo_var.get()
    is_bot_running = bot_process and bot_process.poll() is None

    if is_bot_running:
        if is_monitor_supposed_to_be_active:
            if not monitor_erro_thread or not monitor_erro_thread.is_alive():
                logger.info("Monitor ativado pelo usuário com bot rodando. Iniciando...")
                img_erro_mon = caminhos_imagens.get('imagem_erro_monitor')
                img_erro_mon_2 = caminhos_imagens.get('imagem_erro_monitor_2')
                img_botao_mon = caminhos_imagens.get('imagem_botao_monitor')
                if not img_erro_mon or not os.path.exists(img_erro_mon) or \
                   not img_botao_mon or not os.path.exists(img_botao_mon) or \
                   (img_erro_mon_2 and not os.path.exists(img_erro_mon_2)):
                    logger.error("Não é possível ativar monitor: imagens não configuradas/inválidas.")
                    messagebox.showerror("Erro Monitor", "Imagens do monitor não configuradas/inválidas.")
                    monitor_erro_ativo_var.set(False)
                    if monitor_status_label_text: monitor_status_label_text.set("Monitor: Desativado (Erro Imagem)")
                    salvar_configuracoes() # Salva o estado revertido
                    return
                stop_monitor_erro_event.clear()
                intervalo_monitor_segundos = intervalo_monitor_erro_minutos * 60
                monitor_erro_thread = threading.Thread(target=monitorar_erros,
                                                     args=(img_erro_mon, img_erro_mon_2, img_botao_mon, stop_monitor_erro_event, handle_bot_restart_request, intervalo_monitor_segundos),
                                                     daemon=True)
                monitor_erro_thread.start()
                if monitor_status_label_text: monitor_status_label_text.set("Monitor: Ativo")
        else: # Desativar monitor com bot rodando
            if monitor_erro_thread and monitor_erro_thread.is_alive():
                logger.info("Monitor desativado pelo usuário com bot rodando. Parando...")
                stop_monitor_erro_event.set()
                monitor_erro_thread.join(timeout=3)
                monitor_erro_thread = None
                if monitor_status_label_text: monitor_status_label_text.set("Monitor: Desativado (Usuário)")
    else: # Bot não está rodando
        if monitor_status_label_text:
            status_val = "Monitor: Inativo (Aguardando Bot)" if is_monitor_supposed_to_be_active else "Monitor: Desativado (Usuário)"
            monitor_status_label_text.set(status_val)
    logger.info(f"Monitor de erro alterado para: {is_monitor_supposed_to_be_active}")

# --- Criação da Interface Gráfica ---
root = tk.Tk()
root.title("Painel de Controle - Bot Fortnite LEGO (v1.0) -  By OST-Berserker Fortnite")
root.resizable(True, True)
root.minsize(700, 680)

monitor_erro_ativo_var = tk.BooleanVar(value=True)
style = ttk.Style()
style.theme_use('clam')
main_frame = ttk.Frame(root, padding="10")
main_frame.pack(expand=True, fill=tk.BOTH)
main_frame.rowconfigure(0, weight=1)
main_frame.columnconfigure(0, weight=1)
notebook = ttk.Notebook(main_frame)
notebook.grid(row=0, column=0, sticky='nsew', pady=(0, 10))

# Aba: Configurações
config_tab = ttk.Frame(notebook, padding="10")
notebook.add(config_tab, text=' Configurações ')
tempo_frame = ttk.LabelFrame(config_tab, text="Tempo de Execução", padding="10")
tempo_frame.pack(fill=tk.X, pady=(5, 10))
ttk.Label(tempo_frame, text="Tempo ativo na partida:").pack(side=tk.LEFT, padx=(0, 10))
tempo_options = ["1 minuto", "5 minutos", "10 minutos", "15 minutos", "20 minutos", "30 minutos", "Personalizado"]
combo_tempo = ttk.Combobox(tempo_frame, values=tempo_options, state="readonly", width=15)
combo_tempo.pack(side=tk.LEFT, padx=(0, 10))
frame_tempo_personalizado = ttk.Frame(tempo_frame)
frame_tempo_personalizado.pack(side=tk.LEFT)
entry_tempo_personalizado = ttk.Entry(frame_tempo_personalizado, width=5)
label_minutos = ttk.Label(frame_tempo_personalizado, text="minutos")
def toggle_tempo_personalizado(event=None):
    if combo_tempo.get() == "Personalizado":
        entry_tempo_personalizado.pack(side=tk.LEFT, padx=(0, 5)); label_minutos.pack(side=tk.LEFT); entry_tempo_personalizado.focus()
    else:
        entry_tempo_personalizado.pack_forget(); label_minutos.pack_forget()
combo_tempo.bind("<<ComboboxSelected>>", toggle_tempo_personalizado)
save_button_config_tab = ttk.Button(config_tab, text="Salvar Configs Gerais", command=salvar_configuracoes)
save_button_config_tab.pack(pady=(10,5))

# Aba: Imagens Bot
imagens_tab = ttk.Frame(notebook, padding="10")
notebook.add(imagens_tab, text=' Imagens Bot ')
imagens_frame = ttk.Frame(imagens_tab)
imagens_frame.pack(expand=True, fill=tk.BOTH)
imagens_grid = ttk.Frame(imagens_frame)
imagens_grid.pack(anchor='center')
image_keys_labels_bot = {
    'selecionar_mundo_1': "1. Sel. Mundo (Principal):", 'selecionar_mundo_2': "2. Sel. Mundo (LEGO):",
    'jogar_selecao': "3. Jogar (Pós Sel.):", 'resgatar': "4. Resgatar (Lobby):",
    'avaliar_pular': "5. Pular Aval. (Lobby):", 'sair_menu': "6. Sair (Menu ESC):",
    'voltar_lobby': "7. Voltar Lobby (ESC):", 'confirmar_sim': "8. Confirmar Saída (Sim):",
}
image_widgets = {}
row_num = 0
for key, label_text in image_keys_labels_bot.items():
    frame = ttk.Frame(imagens_grid)
    frame.grid(row=row_num, column=0, sticky='ew', pady=3)
    label = ttk.Label(frame, text=label_text, width=25, anchor='w')
    label.pack(side=tk.LEFT, padx=(0, 5))
    status_label = ttk.Label(frame, text="-", foreground='red', width=20, anchor='w')
    status_label.pack(side=tk.LEFT, padx=5)
    button = ttk.Button(frame, text="Selecionar...", command=lambda k=key, sl=status_label: selecionar_imagem(k, sl))
    button.pack(side=tk.LEFT)
    image_widgets[key] = status_label
    row_num += 1

# Aba: Monitor de Erro
monitor_erro_tab = ttk.Frame(notebook, padding="10")
notebook.add(monitor_erro_tab, text=' Monitor de Erro  Beta')
monitor_enable_frame = ttk.LabelFrame(monitor_erro_tab, text="Controle do Monitor", padding="10")
monitor_enable_frame.pack(fill=tk.X, pady=(5,10))
chk_monitor_ativo = ttk.Checkbutton(monitor_enable_frame, text="Ativar Monitor de Erro (Como esta em beta pode ser que nao funciona corretamente em alguns Pcs)", variable=monitor_erro_ativo_var, command=on_monitor_enable_change)
chk_monitor_ativo.pack(side=tk.LEFT, padx=5)
monitor_frame_config = ttk.LabelFrame(monitor_erro_tab, text="Imagens do Monitor", padding="10")
monitor_frame_config.pack(fill=tk.X, pady=(5,5))
# ... (labels e botões para imagens do monitor, similar à aba de imagens bot) ...
img_mon_keys = {'imagem_erro_monitor': "Erro Principal:", 'imagem_erro_monitor_2': "Erro Secundário (Opc.):", 'imagem_botao_monitor': "Botão Confirmação:"}
for key, text in img_mon_keys.items():
    f = ttk.Frame(monitor_frame_config); f.pack(fill=tk.X, pady=2)
    ttk.Label(f, text=text, width=25, anchor='w').pack(side=tk.LEFT, padx=(0,5))
    sl = ttk.Label(f, text="-", foreground='red', width=20, anchor='w'); sl.pack(side=tk.LEFT, padx=5)
    ttk.Button(f, text="Sel...", command=lambda k=key, s=sl: selecionar_imagem(k,s)).pack(side=tk.LEFT)
    image_widgets[key] = sl

intervalo_monitor_frame = ttk.LabelFrame(monitor_erro_tab, text="Intervalo Verificação", padding="10")
intervalo_monitor_frame.pack(fill=tk.X, pady=(5,5))
ttk.Label(intervalo_monitor_frame, text="Verificar a cada:").pack(side=tk.LEFT, padx=(0, 10))
intervalo_options = ["1 minuto(s)", "2 minuto(s)", "3 minuto(s)", "5 minuto(s)", "10 minuto(s)"]
combo_intervalo_monitor = ttk.Combobox(intervalo_monitor_frame, values=intervalo_options, state="readonly", width=15)
combo_intervalo_monitor.pack(side=tk.LEFT, padx=(0,10))
combo_intervalo_monitor.bind("<<ComboboxSelected>>", lambda event: salvar_configuracoes())
monitor_status_frame = ttk.LabelFrame(monitor_erro_tab, text="Status Monitor", padding="10")
monitor_status_frame.pack(fill=tk.X, pady=(5,5))
monitor_status_label_text = tk.StringVar(value="Monitor: Inativo")
monitor_status_label = ttk.Label(monitor_status_frame, textvariable=monitor_status_label_text, font=("Segoe UI", 10, "bold"))
monitor_status_label.pack(pady=5)

# Aba: Logs
log_tab = ttk.Frame(notebook, padding="10")
notebook.add(log_tab, text=' Logs ')
log_tab.rowconfigure(0, weight=1); log_tab.columnconfigure(0, weight=1)
log_text_widget = scrolledtext.ScrolledText(log_tab, wrap=tk.WORD, state='disabled', height=15)
log_text_widget.grid(row=0, column=0, sticky='nsew')

# Botões de Controle
control_frame = ttk.Frame(main_frame, padding="10")
control_frame.grid(row=1, column=0, sticky='ew')
control_frame.columnconfigure(0, weight=1); control_frame.columnconfigure(1, weight=1)
start_button = ttk.Button(control_frame, text="Iniciar Bot", command=iniciar_bot)
start_button.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
stop_button = ttk.Button(control_frame, text="Encerrar Bot", command=lambda: parar_bot(notify_user=True), state=tk.DISABLED)
stop_button.grid(row=0, column=1, padx=5, pady=5, sticky='ew')

# Inicialização
def update_image_labels_on_load():
    for key, status_label_widget in image_widgets.items():
        path = caminhos_imagens.get(key)
        if path and os.path.exists(path):
            status_label_widget.config(text=os.path.basename(path), foreground='green')
        elif path: # Caminho existe no config mas arquivo não no disco
             status_label_widget.config(text=f"Inválido: {os.path.basename(path)}", foreground='orange')
        else: # Não carregada
            default_text = "Não carregada (Opc.)" if key == 'imagem_erro_monitor_2' else "Não carregada"
            default_color = 'grey' if key == 'imagem_erro_monitor_2' else 'red'
            status_label_widget.config(text=default_text, foreground=default_color)

if carregar_configuracoes():
    update_image_labels_on_load()

# ... (configuração de combos de tempo e intervalo) ...
if tempo_execucao_segundos > 0:
    tempo_min = tempo_execucao_segundos // 60
    tempo_str = f"{tempo_min} minutos"
    if tempo_str in tempo_options: combo_tempo.set(tempo_str)
    else: combo_tempo.set("Personalizado"); entry_tempo_personalizado.insert(0, str(tempo_min)); toggle_tempo_personalizado()
else: combo_tempo.set(tempo_options[1]) # Padrão 5 minutos

if intervalo_monitor_erro_minutos > 0:
    intervalo_str = f"{intervalo_monitor_erro_minutos} minuto(s)"
    if intervalo_str in intervalo_options: combo_intervalo_monitor.set(intervalo_str)
    else: combo_intervalo_monitor.set(intervalo_options[0])
else: combo_intervalo_monitor.set(intervalo_options[0]) # Padrão 1 minuto

on_monitor_enable_change() # Atualiza estado inicial do label do monitor

ui_log_handler = TkinterLogHandler(log_text_widget)
ui_log_handler.setFormatter(logging.Formatter(log_format))
logging.getLogger().addHandler(ui_log_handler)

root.protocol("WM_DELETE_WINDOW", on_closing)
root.after(100, process_log_queue)
root.mainloop()

