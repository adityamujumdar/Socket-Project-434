import socket
import sys

HOST = '' # Symbolic. Listening to all available interfaces
PORT = 8888 # Non-priviledged port
BUFFER_SIZE = 1024

try:
	socket_t = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	print('Socket creation successful!')
except socket.error as msg:
	print('Socker creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
	sys.exit()

# Bind socket to local host and port
try:
	socket_t.bind((HOST, PORT))
except socket.error as msg:
	print('Bind failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
	sys.exit()

print('Socket bind successful')

while 1:
	print('UDP Server is up and listening to port: ', PORT)
	#receive message from client (message, addr)
	transferred_d = socket_t.recvfrom(BUFFER_SIZE)
	message = transferred_d[0]
	addr = transferred_d[1]

	# check if message is none (if not message is true then break)
	if not message:
		break

	reply = 'Server says...' + message.decode('utf-8')
	socket_t.sendto(reply.encode('utf-8'), addr)
	print('Message[' + addr[0] + ':' + str(addr[1]) + '] - ' + message.decode('utf-8').strip())

socket_t.close()
