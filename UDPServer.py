import socket, sys, threading, time

HOST = '' # Symbolic. Listening to all available interfaces
THREAD_COUNT = 0

def create_socket():
	# Create socket
	try:
		socket_p = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print('Socket creation successful!')
		return socket_p
	except socket.error as msg:
		print('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
		sys.exit()

def bind_socket(socket_p, host, portnumber):
	# Bind socket to local host and port
	try:
		# On a succesful bind, socket_p.bind() will return 0, otherwise returns 1
		if(socket_p.bind((host, portnumber)) == 0):
			print('Bind successful')
	except socket.error as msg:
		print('Bind failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
		sys.exit()

def run_UDPserver(socket_p, portnumber, buffersize = 4096):
	# Start the UDP server
	while 1:
		print('UDP Server is up and listening to port: ', portnumber)
		# receive message from client is in form (data, client_address)
		message, client_addr = socket_p.recvfrom(buffersize)
		# check if message is none
		if not message:
			reply = 'Warning: An empty message was sent'
			socket_p.sendto(reply.encode('utf-8'), client_addr)
			print('Message[' + client_addr[0] + ':' + str(client_addr[1]) + '] - ' + 'Warning: An empty message was sent')
		else:
			reply = 'Server says...' + message.decode('utf-8')
			socket_p.sendto(reply.encode('utf-8'), client_addr)
			print('Message[' + client_addr[0] + ':' + str(client_addr[1]) + '] - ' + message.decode('utf-8').strip())

def main(argv):
	try:
		if(len(argv)<3):
			PORT = int(argv[1])
	except:
		# print(str(sys.argv), len(sys.argv))
		print('Usage: python Server.py <port1> <port2> . . <portn>')
		sys.exit()

	socket_t = create_socket()
	bind_socket(socket_t, HOST, PORT)
	# change default buffer size to 5120
	run_UDPserver(socket_t, PORT, 5120)
	socket_t.close()

if __name__ == '__main__':
	main(sys.argv[0:])
