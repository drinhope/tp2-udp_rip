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

# Função para enviar uma mensagem que traça uma rota até um IP (retorna até o remetente)
def TRACE(routing_table, IP, my_address):
    message = {
                "type": "trace",
                "source": my_address,
                "destination": IP,
                "routers": [my_address],
                }
    #Falta reenviar para seguir o caminho até o destino

# A trace chegou até o destino, função que reenvia para a origem
def send_trace_back(decoded_message, my_address):
    message = {
                "type": "data",
                "source": my_address,
                "destination": decoded_message.get("source"),
                "payload": decoded_message,
                }
    #Falta enviar de volta para a origem e não sei se está tratado para os roteadores de caminho

# Roteador de caminho, deve reenviar a trace seguindo até o destinatário
def resend_trace(message, my_address):
    destination = message.get("destination")
    message.get("routers").append(my_address)
    #Agora deve enviar message para o próximo roteador, não sei fazer isso ainda kkkkk

# Função para enviar mensagens de atualização para os vizinhos com Split Horizon
def SEND_UPDATE_MESSAGE(sock, port, routing_table, address):
    while True:
        with routing_table_lock:
            for neighbor, weight in routing_table.items():
                # Cria uma tabela filtrada (Split Horizon)
                filtered_table = {
                    destination: cost + weight  # Adiciona o custo do link ao vizinho
                    for destination, cost in routing_table.items()
                    if destination != neighbor
                }

                # Monta a mensagem de update
                message = {
                    "type": "update",
                    "source": address,
                    "destination": neighbor,
                    "distances": filtered_table,
                }
                encoded_message = json.dumps(message).encode('utf-8')
                sock.sendto(encoded_message, (neighbor, port))
        time.sleep(period)  # Aguarda o período especificado

# Função para receber mensagens de atualização e atualizar a tabela de roteamento
def RECEIVE_UPDATE_MESSAGE(sock, routing_table, my_address):
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
                        for destination, received_cost in distances.items():
                            # Soma o peso do link para o vizinho (source)
                            link_cost = routing_table.get(source, float('inf'))
                            total_cost = received_cost + link_cost

                            # Atualiza apenas se for mais barato ou a rota não existir
                            if destination not in routing_table or routing_table[destination] > total_cost:
                                routing_table[destination] = total_cost
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
        elif command.startswith("trace"):
            IP = command.split()[1]
            with routing_table_lock:
                TRACE(routing_table, IP, address)

# Executa a função principal quando o script é iniciado
if __name__ == '__main__':
    main()
