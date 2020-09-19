import socket
import sys

HOST = 'localhost'
PORT = 8888
BUFFER_SIZE = 1024
ITERATIONS = 5

try:
	socket_t=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
except socket.error:
	print('Socket creation failed')
	sys.exit()


for i in range(ITERATIONS):
	message = input('Enter message to send: ')
	print('Client sends ', message, ' to server')

	try:
		socket_t.sendto(message.encode('utf-8'), (HOST, PORT))

		# Receive data from server (data, addr)
		received_d = socket_t.recvfrom(BUFFER_SIZE)
		reply = received_d[0]
		addr = received_d[1]

		print('Server replied: ', reply)

	except socket.error as message:
		print('Error Code: '+str(message[0])+' Message ' + message[1])
		sys.exit()

socket_t.close()
