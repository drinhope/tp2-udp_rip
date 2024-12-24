import socket  # Biblioteca para criar sockets
import sys     # Biblioteca para lidar com argumentos da linha de comando
import json    # Biblioteca para trabalhar com dados em formato JSON
import time    # Biblioteca para trabalhar com tempo
import threading  # Biblioteca para usar threads

# Constante que define o tempo limite para operações de socket
TIMEOUT = 10

# Função para criar e configurar o socket UDP
def create_sockets(address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Criação do socket UDP
    sock.settimeout(TIMEOUT)  # Define o tempo limite para operações de leitura
    sock.bind((address, port))  # Vincula o socket ao endereço e porta especificados
    return sock

# Função para adicionar uma rota à tabela de roteamento
def ADD(routing_table, IP, weight):
    routing_table[IP] = weight  # Adiciona ou atualiza a rota com o peso associado

# Função para remover uma rota da tabela de roteamento
def DEL(routing_table, IP):
    if IP in routing_table:
        del routing_table[IP]  # Remove a rota do dicionário
    else:
        print(f"Rota para {IP} não encontrada na tabela de roteamento.")

# Função para enviar mensagens de atualização para os vizinhos com Split Horizon
def SEND_UPDATE_MESSAGE(sock, port, routing_table, address):
    while True:
        #print("Enviando atualizações...")
        with routing_table_lock:
            for neighbor, weight in routing_table.items():
                filtered_table = {
                    destiny: travel_cost
                    for destiny, travel_cost in routing_table.items()
                    if destiny != neighbor
                }
                message = {
                    "type": "update",
                    "source": address,
                    "destination": neighbor,
                    "distances": filtered_table,
                }
                encoded_message = json.dumps(message).encode('utf-8')
                sock.sendto(encoded_message, (neighbor, port))
        time.sleep(period)  # Aguarda o período especificado

# Função para receber mensagens de outros roteadores
def RECEIVE_UPDATE_MESSAGE(sock, routing_table, address):
    while True:
        try:
            info, sender = sock.recvfrom(4096)
            decoded_message = json.loads(info.decode('utf-8'))
            print(f"Mensagem recebida: {decoded_message}")

            if decoded_message.get("type") == "update":
                source = decoded_message.get("source")
                distances = decoded_message.get("distances")

                if source and distances:
                    with routing_table_lock:
                        for destiny, cost in distances.items():
                            if destiny not in routing_table or routing_table[destiny] > cost:
                                routing_table[destiny] = cost
                                print(f"Tabela de roteamento atualizada: {routing_table}")
        except socket.timeout:
            continue  # Ignora timeouts

# Função principal do programa
def main():
    global period, routing_table_lock

    address = sys.argv[1]  # Endereço IP do roteador
    period = int(sys.argv[2])  # Período de envio de atualizações
    port = 55151  # Porta padrão para comunicação

    sock = create_sockets(address, port)  # Cria o socket UDP
    routing_table = {}  # Inicializa a tabela de roteamento como um dicionário vazio
    routing_table_lock = threading.Lock()  # Trava para sincronização de acesso à tabela

    # Inicia a thread para receber mensagens
    #while routing_table:
    threading.Thread(target=RECEIVE_UPDATE_MESSAGE, args=(sock, routing_table, address), daemon=True).start()

        # Inicia a thread para enviar atualizações periodicamente
    threading.Thread(target=SEND_UPDATE_MESSAGE, args=(sock, port, routing_table, address), daemon=True).start()

    # Loop principal para interação com o usuário
    while True:
        command = input()
        if command.startswith("add"):
            IP, weight = command.split()[1], int(command.split()[2])
            with routing_table_lock:
                ADD(routing_table, IP, weight)
        elif command.startswith("del"):
            IP = command.split()[1]
            with routing_table_lock:
                DEL(routing_table, IP)

# Executa a função principal quando o script é iniciado
if __name__ == '__main__':
    main()
