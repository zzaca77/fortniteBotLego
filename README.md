Projeto de Automação de Jogo com Bot (Fortnite Lego)
Este projeto envolve a criação de um bot automatizado para simular interações dentro de um jogo, especificamente no Fortnite Lego. O bot é configurado para realizar ações como movimentos aleatórios, cliques, saltos e olhar ao redor. Além disso, o código é capaz de ler ações gravadas em um arquivo de texto (acoes_jogo.txt) e reproduzi-las de forma natural e aleatória.

Principais Funcionalidades
Bot Automático: O bot realiza movimentos aleatórios, saltos, cliques e movimentação da câmera (olhar ao redor), simulando um comportamento humano.

Gravação de Ações: O bot pode gravar ações realizadas, como cliques e movimentos, em um arquivo de texto para reprodução futura.

Execução de Scripts: O bot pode executar um script (sair.py) após um período de tempo determinado (1 hora, por exemplo), fechando o bot automaticamente.

Interações Baseadas em Coordenadas: As ações de clique podem ser feitas em coordenadas específicas da tela, configuradas pelo usuário.

Simulação de Comportamento Natural: Pequenas pausas e variações nas ações do bot são implementadas para simular um comportamento humano, evitando padrões previsíveis.

Componentes do Projeto
bot.py: O código principal que simula as ações do bot. Realiza movimentos aleatórios, cliques e saltos.

acoes_jogo.txt: Arquivo de texto que contém as ações gravadas do jogo. O bot pode ler este arquivo e realizar as ações em sequência.

sair.py: Script que é executado automaticamente após 1 hora de execução do bot, finalizando o processo.

resgatar.py: Script adicional que pode ser implementado para realizar ações específicas de resgatar pontos ou interagir com o jogo conforme necessário.

Como Funciona
O bot começa automaticamente e realiza ações de forma aleatória (movimentos, saltos, cliques).

O bot pode gravar essas ações em um arquivo de texto (acoes_jogo.txt) com as coordenadas de cada clique e ação realizada.

Após a execução de 1 hora, o bot executa o script sair.py para finalizar a sessão.

A leitura do arquivo de ações (acoes_jogo.txt) pode ser configurada para reproduzir cliques em pontos específicos da tela conforme gravado.

Configurações de Cliques e Ações
O bot pode ser configurado para realizar cliques em pontos específicos na tela, definidos pelas coordenadas X e Y. As coordenadas podem ser obtidas usando ferramentas como pyautogui.

Para personalizar o comportamento de cliques, basta editar as coordenadas no arquivo acoes_jogo.txt. O bot vai ler essas coordenadas e realizar os cliques na sequência.

Especificidade para Fortnite Lego
Este bot foi desenvolvido especificamente para o jogo Fortnite Lego. Embora ele possa ser adaptado para outros jogos, as coordenadas de clique e os comportamentos de movimentação estão configurados para funcionar de maneira ideal dentro do ambiente do Fortnite Lego.

Importante: O bot não funcionará corretamente em outros jogos sem ajustes nas coordenadas e nas funções de interação.

Notas Importantes
O bot simula um comportamento humano, incluindo pausas aleatórias entre ações para evitar padrões previsíveis.

O código foi projetado para ser simples de usar e personalizar, com funções separadas para ações específicas como pular (jump()), olhar ao redor (look_around()) e clicar em coordenadas específicas.
