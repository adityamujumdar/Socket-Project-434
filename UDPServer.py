import socket
import sys

HOST = '' # Symbolic. Listening to all available interfaces
PORT = 8888 # Non-priviledged port
BUFFER_SIZE = 4096

# Create socket
try:
	socket_t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print('Socket creation successful!')
except socket.error as msg:
	print('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
	sys.exit()


# Bind socket to local host and port
try:
	socket_t.bind((HOST, PORT))
	print('Bind successful')	
except socket.error as msg:
	print('Bind failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
	sys.exit()

# Start the UDP server
while 1:
	print('UDP Server is up and listening to port: ', PORT)
	# receive message from client is in form (data, client_address)
	message, client_addr = socket_t.recvfrom(BUFFER_SIZE)

	# check if message is none
	if not message:
		reply = 'Warning: An empty message was sent'
		socket_t.sendto(reply.encode('utf-8'), client_addr)
		print('Message[' + client_addr[0] + ':' + str(client_addr[1]) + '] - ' + 'Warning: An empty message was sent')
	else:
		reply = 'Ok...' + message.decode('utf-8')
		socket_t.sendto(reply.encode('utf-8'), client_addr)
		print('Message[' + client_addr[0] + ':' + str(client_addr[1]) + '] - ' + message.decode('utf-8').strip())
socket_t.close()
