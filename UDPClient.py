import socket, sys

#TODO: change BUFFER_SIZE in send_commands_to_server to the size of the message
global BUFFER_SIZE
BUFFER_SIZE= 4096


def create_socket():
	# Create socket
	try:
		socket_p = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		print('Socket creation successful!')
		return socket_p
	except socket.error as msg:
		print('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
		sys.exit()

def send_commands_to_server(socket_p, serverip, portnumber, iterations = 5):
	for i in range(iterations):
		message = input('Enter command to send: ')
		print('Client sends', message, 'to server')
		try:
			# check if length of message to server is equal to the length of the message inputted
			if(socket_p.sendto(message.encode('utf-8'), (serverip, portnumber)) == len(message)):
				# Receive data from server (data, addr)
				reply, server_addr = socket_p.recvfrom(BUFFER_SIZE)
				print('Server replied: ', reply)
		except socket.error as message:
			print('Error Code : ' + str(message[0]) + ' Message ' + message[1])
			sys.exit()

def main(argv):
	# get port and serverIP from command line
	try:
		# check if the 2nd argument is an ip address
		if(argv[1].count('.') == 3):
			serverIP = argv[1] # get server IP
		else:
			print('Usage: python3 Client.py <ipaddress> <port>')
			sys.exit()
		# convert port number to int
		PORT = int(argv[2])
		print('Arguments passed: server IP', serverIP, 'port(s)', PORT)
	except:
		print('Usage: python3 Client.py <ipaddress> <port>')
		sys.exit()
	socket_t = create_socket()
	# iterations is set to 5 by default
	send_commands_to_server(socket_t, serverIP, PORT, 10)
	socket_t.close()

if __name__ == '__main__':
	main(sys.argv[0:])
