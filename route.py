import socket  # Biblioteca para criação e manipulação de sockets
import sys     # Biblioteca para lidar com argumentos da linha de comando
import json    # Biblioteca para trabalhar com dados em formato JSON
import math    # Biblioteca matemática
import select  # Biblioteca para monitorar múltiplos sockets
import time    # Biblioteca para trabalhar com tempo
import keyboard  # Biblioteca para capturar entradas do teclado
import numpy as np  # Biblioteca para cálculos matemáticos avançados

# Constante que define o tempo limite para operações de socket
TIMEOUT = 5

# Função para criar e configurar o socket UDP
def create_sockets(address, port):
    """
    Cria e configura um socket UDP vinculado a um endereço e porta específicos.
    Define um timeout de 5 segundos para operações de leitura.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Criação do socket UDP

    # Definir o tempo limite de 5 segundos para operações de leitura
    sock.settimeout(5)
    
    # Vincula o socket ao endereço e porta especificados
    sock.bind((address, port))
    return sock

# Função para adicionar uma rota à tabela de roteamento
def ADD(routing_table, IP, weight):
    """
    Adiciona uma nova rota à tabela de roteamento.
    - routing_table: Dicionário que armazena as rotas.
    - IP: Endereço IP do destino.
    - weight: Custo associado à rota.
    """
    routing_table[IP] = weight  # Adiciona ou atualiza a rota com o peso associado
    
# Função para remover uma rota da tabela de roteamento
def DEL(routing_table, IP):
    """
    Remove uma rota da tabela de roteamento.
    - routing_table: Dicionário que armazena as rotas.
    - IP: Endereço IP do destino a ser removido.
    """
    if IP in routing_table:
        del routing_table[IP]  # Remove a rota do dicionário
    else:
        print(f"Rota para {IP} não encontrada na tabela de roteamento.")

# Função para enviar mensagens de atualização para os vizinhos
def SEND_UPDATE_MESSAGE(sock, port, routing_table, address):
    """
    Envia mensagens de atualização de rota periodicamente para os vizinhos.
    - sock: Socket para envio de mensagens.
    - port: Porta dos vizinhos.
    - routing_table: Tabela de roteamento atual.
    - address: Endereço IP do roteador de origem.
    """
    for IP, weight in routing_table.items():
        # Cria a mensagem de atualização
        message = {
            "type": "update",
            "source": address,
            "destination": IP,
            "distances": routing_table
        }
        
        # Codifica a mensagem em JSON e a transforma em bytes
        encoded_message = json.dumps(message).encode('utf-8')
        
        # Envia a mensagem para o vizinho especificado
        sock.sendto(encoded_message, (IP, port))

# Função para receber mensagens de outros roteadores
def RECEIVE_UPDATE_MESSAGE(sock, routing_table, address):
    """
    Recebe mensagens enviadas por roteadores vizinhos e atualiza a tabela de roteamento.
    - sock: Socket para receber mensagens.
    - routing_table: Tabela de roteamento atual.
    - address: Endereço IP do roteador.
    """
    # Recebe dados do socket (máximo de 4096 bytes) e o endereço do remetente
    info, sender = sock.recvfrom(4096)
    
    # Decodifica a mensagem de bytes para string JSON e converte em dicionário
    decoded_message = json.loads(info.decode('utf-8'))
    
    # Verifica o tipo da mensagem recebida
    if decoded_message.get("type") == "update":
        source = decoded_message.get("source")  # Roteador de origem
        distances = decoded_message.get("distances")  # Distâncias da tabela de origem
            
        # Atualiza a tabela de roteamento com as informações recebidas
        if source and distances:
            for destiny, cost in distances.items():
                # Atualiza a rota apenas se for nova ou de menor custo
                if destiny not in routing_table or routing_table[destiny] > cost:
                    routing_table[destiny] = cost
                    print(f"Tabela de roteamento atualizada: {routing_table}")
    elif decoded_message.get("type") == "trace":
        # Tratamento para mensagens do tipo "trace" (a implementar)
        print(f"Mensagem de trace recebida: {decoded_message}")

# Função principal do programa
def main():
    """
    Função principal que inicializa o programa.
    Recebe argumentos da linha de comando e configura o roteador.
    """
    # Argumentos da linha de comando
    address = sys.argv[1]  # Endereço IP do roteador
    period = sys.argv[2]   # Período de envio de atualizações
    startup = sys.argv[3]  # Tipo de inicialização ('add' ou outro)
    IP = sys.argv[4]       # Endereço IP do destino inicial
    weight = sys.argv[5]   # Peso associado ao destino inicial
    
    # Porta padrão para comunicação
    port = 55151
    
    # Inicializa a tabela de roteamento como um dicionário vazio
    routing_table = {}
    
    # Cria o socket UDP
    sockets = create_sockets(address, port)

    # Executa ações específicas com base no tipo de inicialização
    if startup == 'add':
        ADD(routing_table, IP, weight);  # Placeholder para implementação futura

# Executa a função principal quando o script é iniciado
if __name__ == '__main__':
    main()
