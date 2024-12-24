# tp2-udprip

INSTRUÇÕES PARA RODAR:
1 - Baixar o arquivo zip que o professor disponibilizou
2 - Rodar esse código aqui no terminal do Ubuntu: sudo ./lo-addresses.sh add
3 - Dá esse comando para verificar se todos os endereços de 127.0.1.1-127.0.1.16 foram adicionados: ip addr show lo
4 - Dá esse comando aqui de acordo com o local do seu arquivo: cd /mnt/c/Pasta (o meu arquivo do código está em uma pasta dentro do C: do Windows. Se o seu for assim, coloca o nome da pasta e é só rodar o código).
5 - Para inicializar o código: python3 router.py 127.0.1.2 5 (o IP pode ser qualquer um até 127.0.1.16 e o 5 é só um tempo de transmissão entre mensagens)
6 - Para adicionar um IP pode fazer: add 127.0.1.x Peso (como está descrito no trabalho).
