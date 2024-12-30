import socket
import sys
import json
import time
import threading

TIMEOUT = 50
neighbors = set()
neighbor_timers = {}

# Função para criar e configurar o socket UDP
def create_sockets(address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.bind((address, port))
    return sock

def ROUTES_FUSION(go_to, destination, weight):
    if destination == address:
        return  # Ignora tentativas de atualizar a métrica para o próprio roteador

    with routing_table_lock:

        # Checa se a rota para o destino já existe
        if destination in routing_table:
            route = routing_table[destination]

            # Atualiza se o custo for menor
            if weight < route['weight']:
                route['go_to'] = go_to
                route['weight'] = weight
            
        else:
            # Insere uma nova rota
            routing_table[destination] = {
                'go_to': go_to,
                'weight': weight
            }

        # Garante que o próximo salto esteja registrado na tabela
        if go_to not in routing_table:
            routing_table[go_to] = {'go_to': go_to, 'weight': weight}

    # Exibe o estado atualizado da tabela de roteamento


# Função para adicionar uma rota à tabela de roteamento
def ADD(routing_table, IP, weight):
    neighbors.add(IP)
    routing_table[IP] = {'go_to': IP, 'weight': weight}

# Função para remover uma rota da tabela de roteamento
def DEL(routing_table, IP):
    #with routing_table_lock:
        neighbors.discard(IP)
        if IP in routing_table:
            del routing_table[IP]
        
        # Remove rotas aprendidas através do vizinho
        to_remove = [dest for dest, route in routing_table.items() if route["go_to"] == IP]
        for dest in to_remove:
            del routing_table[dest]


def TRACE(sock, routing_table, IP, address):
    message = {
        "type": "trace",
        "source": address,
        "destination": IP,
        "routers": [address]  # Inicia a lista com o roteador atual
        }
    
    if IP in routing_table:
        go_to = routing_table[IP]["go_to"]
        encoded_message = json.dumps(message).encode('utf-8')
        sock.sendto(encoded_message, (go_to, port))
            
def RECEIVE_TRACE(sock, source_IP, message):
    if address in message["routers"]:
        return
    
    message["routers"].append(address)
    
    if message["destination"] == address:
        trace_response = {
            "type": "data",
            "source": address,
            "destination": message["source"],
            "payload": json.dumps(message)
            }
        encoded_trace_response = json.dumps(trace_response).encode('utf-8')
        sock.sendto(encoded_trace_response, (message["source"], port))
    else:
        with routing_table_lock:
            if message["destination"] in routing_table:
                go_to = routing_table[message["destination"]]["go_to"]
                encoded_message = json.dumps(message).encode('utf-8')
                sock.sendto(encoded_message, (go_to, port))
                
# Função para receber mensagens
def RECEIVE_MESSAGE(sock, routing_table, address):
    global neighbors
    while True:
        try:
            info, sender = sock.recvfrom(4096)
            decoded_message = json.loads(info.decode('utf-8'))
            source_IP = decoded_message["source"]

            # messagens de update
            if decoded_message.get("type") == "update":
                with routing_table_lock:
                    neighbor_timers[source_IP] = time.time()
                distances = decoded_message.get('distances', {})
                print(f'{distances}')
                for destination, add_weight in distances.items(): #distance.items par chave fechadura com o ip do roteador e a distancia até ele
                    # Corrige o cálculo da distância total
                    if destination == address:
                        continue  # Não altera a distância do próprio roteador
                    ROUTES_FUSION(source_IP, destination, add_weight)
            
            elif decoded_message.get("type") == "data":
                if decoded_message.get("destination") == address:
                    print("Payload:", json.dumps(decoded_message['payload'], indent=4))
                else:
                    with routing_table_lock:
                        if decoded_message.get("destination") in routing_table:
                            encoded_message = json.dumps(decoded_message).encode('utf-8')
                            sock.sendto(encoded_message, (routing_table[decoded_message['destination']]['go_to'], port))
                        else:
                            continue 
                        
            elif decoded_message.get("type") == "trace":
                RECEIVE_TRACE(sock, source_IP, decoded_message)

        except socket.timeout:
            continue

# Função para enviar mensagens de atualização
def SEND_UPDATE_MESSAGE(sock, port):
    
    while True:
        time.sleep(period)
        with routing_table_lock:
            for neighbor in neighbors:
                if neighbor in routing_table:
                    add_weight = routing_table[neighbor]['weight']
                distances = {}
                
                for destination, path in routing_table.items():
                    if path['go_to'] == neighbor:
                        # Evita enviar rotas aprendidas de um roteador de volta para ele mesmo
                        continue
                    elif destination == neighbor:
                        continue
                    elif destination == address:  # Se o destino for o IP da origem, soma a distância extra
                        distances[destination] = path['weight'] + add_weight
                    elif destination in neighbors:
                        distances[destination] = path['weight']+ add_weight
                    elif destination not in neighbors:
                        distances[destination] = path['weight']
                
                message = {
                    "type": "update",
                    "source": address,
                    "destination": neighbor,
                    "distances": distances
                }
                encoded_message = json.dumps(message).encode('utf-8')
                sock.sendto(encoded_message, (neighbor, port))
                
def MONITOR_NEIGHBORS(sock, routing_table, period):
    global neighbors, neighbor_timers
    timeout_limit = 4 * period
    while True:
        time.sleep(period)
        current_time = time.time()  # Atualiza o tempo atual
        with routing_table_lock:
            for neighbor in list(neighbor_timers):  # Use list() para evitar problemas ao modificar o set durante a iteração
                last_update_time = neighbor_timers.get(neighbor, 0)
                delta_time = (current_time - last_update_time)
                if delta_time > timeout_limit:
                    DEL(routing_table, neighbor)
                    del neighbor_timers[neighbor]

# Função principal
def main():
    global period, address, routing_table, routing_table_lock, port

    address = sys.argv[1]
    period = int(sys.argv[2])
    port = 55151

    sock = create_sockets(address, port)
    
    routing_table = {}
    routing_table_lock = threading.Lock()
    
    routing_table[address] = {'go_to': address, 'weight': 0}
    print(f'{routing_table}')
    threading.Thread(target=RECEIVE_MESSAGE, args=(sock, routing_table, address), daemon=True).start()
    threading.Thread(target=SEND_UPDATE_MESSAGE, args=(sock, port), daemon=True).start()
    threading.Thread(target=MONITOR_NEIGHBORS, args=(sock, routing_table, period), daemon=True).start()


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
                TRACE(sock, routing_table, IP, address)
        elif command.startswith("quit"):
            sock.close()  # Fecha o socket
            sys.exit(0)   # Encerra o programa de forma limpa

if __name__ == '__main__':
    main()
