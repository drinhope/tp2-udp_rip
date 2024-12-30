import socket
import sys
import json
import time
import threading

TIMEOUT = 50
neighbors = set()
neighbor_timers = {}
destination_timers = {}  # Guarda o último tempo de atualização para cada destino


# Função para criar e configurar o socket UDP
def create_sockets(address, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    sock.bind((address, port))
    return sock

def ROUTES_FUSION(go_to, destination, weight):
    if destination == address:
        #print(f"Ignorando rota para si mesmo: {destination}")
        return

    current_time = time.time()

    with routing_table_lock:
        #print(f"\n[DEBUG] Atualizando ou inserindo rota para {destination} via {go_to} com peso {weight}")
        #print(f"   Destino: {destination}")
        #print(f"   Próximo salto: {go_to}")
        #print(f"   Custo: {weight}")
        #print(f"   Tabela de roteamento atual: {json.dumps(routing_table, indent=4)}\n")
        if destination in routing_table:
            route = routing_table[destination]
            if weight < route['weight']:
                route['go_to'] = go_to
                route['weight'] = weight
        else:
            routing_table[destination] = {'go_to': go_to, 'weight': weight}

        # Atualiza o timer do destino
        destination_timers[destination] = current_time



# Função para adicionar uma rota à tabela de roteamento
def ADD(routing_table, IP, weight):
    neighbors.add(IP)
    routing_table[IP] = {'go_to': IP, 'weight': weight}
    #print(f"Rota adicionada. Tabela de roteamento atualizada: {routing_table}")

# Função para remover uma rota da tabela de roteamento
def DEL(routing_table, IP):
    #with routing_table_lock:
        neighbors.discard(IP)
        if IP in routing_table:
            del routing_table[IP]
        
        # Remove rotas aprendidas através do vizinho
        to_remove = [destiny for destiny, route in routing_table.items() if route["go_to"] == IP]
        for destiny in to_remove:
            del routing_table[destiny]

        #print(f"Rota removida. Tabela de roteamento atualizada: {json.dumps(routing_table, indent=4)}")

def TRACE(sock, routing_table, IP, address):
    #print("Passei por aqui 1")
    message = {
        "type": "trace",
        "source": address,
        "destination": IP,
        "routers": [address]  # Inicia a lista com o roteador atual
        }
    
    if IP in routing_table:
        print("Passei por aqui 2")
        go_to = routing_table[IP]["go_to"]
        encoded_message = json.dumps(message).encode('utf-8')
        sock.sendto(encoded_message, (go_to, port))
            
def RECEIVE_TRACE(sock, source_IP, message):
    #print("cheguei aqui")
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
            #else:
                #print(f'[INFO] Mensagem de trace descartada. Sem rota para o destino: {message["destination"]}')
                
# Função para receber mensagens
def RECEIVE_MESSAGE(sock, routing_table, address):
    global neighbors
    while True:
        try:
            info, sender = sock.recvfrom(4096)
            decoded_message = json.loads(info.decode('utf-8'))
            source_IP = decoded_message["source"]
            #print(f"Mensagem recebida de {source_IP}:\n{json.dumps(decoded_message, indent=4)}")

            # messagens de update
            if decoded_message.get("type") == "update":
                with routing_table_lock:
                    neighbor_timers[source_IP] = time.time()
                distances = decoded_message.get('distances', {})
                #print(f'{distances}')
                for destination, add_weight in distances.items(): #distance.items par chave fechadura com o ip do roteador e a distancia até ele
                    # Corrige o cálculo da distância total
                    if destination == address:
                        continue 
                    #print(f'Recebido update de: {source_IP} com ip de destino (na tabela): {destination}, custo associado: {add_weight}')
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
                            #print(f"[INFO] Mensagem de trace descartada. Sem rota para o destino: {destination}")
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
                
def MONITOR_NEIGHBORS_AND_DESTINATIONS(sock, routing_table, period):
    global neighbors, neighbor_timers, destination_timers
    timeout_limit = 4 * period
    while True:
        time.sleep(period)
        current_time = time.time()  # Atualiza o tempo atual

        with routing_table_lock:
            # Verifica vizinhos diretos
            for neighbor in list(neighbor_timers):  # Copia a lista para evitar modificações durante a iteração
                last_update_time = neighbor_timers.get(neighbor, 0)
                if current_time - last_update_time > timeout_limit:
                    #print(f"[INFO] Vizinho inativo detectado: {neighbor}. Removendo rotas associadas...")
                    DEL(routing_table, neighbor)
                    del neighbor_timers[neighbor]

            # Verifica destinos indiretos
            for destination in list(destination_timers):  # Copia a lista para evitar modificações durante a iteração
                last_update_time = destination_timers.get(destination, 0)
                if current_time - last_update_time > timeout_limit:
                    if destination in routing_table:
                        #print(f"[INFO] Destino inalcançável detectado: {destination}. Removendo da tabela...")
                        del routing_table[destination]
                    del destination_timers[destination]  # Remove o timer do destino


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
    #print(f'{routing_table}')
    threading.Thread(target=RECEIVE_MESSAGE, args=(sock, routing_table, address), daemon=True).start()
    threading.Thread(target=SEND_UPDATE_MESSAGE, args=(sock, port), daemon=True).start()
    threading.Thread(target=MONITOR_NEIGHBORS_AND_DESTINATIONS, args=(sock, routing_table, period), daemon=True).start()


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
            #print("[INFO] Encerrando o programa...")
            sock.close()  
            sys.exit(0)   

if __name__ == '__main__':
    main()
