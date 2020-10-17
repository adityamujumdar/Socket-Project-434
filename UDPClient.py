# Aditya Mujumdar and Jendric Shawn Chan
# COmputer Netorking CSE 434 Fall 2020 Milestone 1

# Client application

import socket, sys, pickle, threading
from datetime import datetime

# TODO: change BUFFER_SIZE in send_commands_to_server to the size of the message
# global BUFFER_SIZE
# BUFFER_SIZE= 1024


# ports are 43500 to 43999
class UDPClient:
    def __init__(self, server_ip, destination_port):
        self.server_ip = ''
        # destination port is servers port its listening at
        self.destination_port = 43599
        # ss port is the source port where client is sending information from
        self.ss_port = None
        # port for peer communication
        self.pp_port_1 = None
        # port for peer communication
        self.pp_port_2 = None
        self.client_ip = None
        self.ring_id = 0
        self.ring_size = 0
        self.rc_ip = None # right clients IP
        self.rc_port = None # right client port
        self.compute_port = None
        self.client_name = None

        # Create socket for pp_2 (right)
        try:
            self.print_log('Creating Socket...')
            self.socket_pp_2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_pp_2.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.print_log('Socket creation successful!')
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()

        # Create socket for pp_1 (left)
        try:
            self.print_log('Creating Socket...')
            self.socket_pp_1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_pp_1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.print_log('Socket creation successful!')
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()

        # Create socket for ss (server)
        try:
            self.print_log('Creating Socket...')
            self.socket_ss = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.socket_ss.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.print_log('Socket creation successful!')
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()


    def print_log(self, msg):
        # Log time for a message
        log_T = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        print(f'[{log_T}] {msg}')

    def interpret_commands(self, depickled_data):
        # for register command
        if(type(depickled_data) is str and depickled_data == 'SUCCESS'):
            # SUCCESS, client has been registerd
            self.print_log(f'SUCCESS')
        elif(type(depickled_data) is str and depickled_data == 'FAILURE'):
            # FAILURE, client couldn't be registered
            self.print_log(f'FAILURE')
        elif(type(depickled_data) is tuple and depickled_data[0] == 'SUCCESS' and len(depickled_data) == 5):
            # start the O-ring setup
            print(f'Users in Ring from Ring Database: {depickled_data[3]}')
            self.ring_id, self.ring_size = depickled_data[1], depickled_data[2]
            index_pos = depickled_data[4]
            self.print_log(f'index position is: {index_pos}')
            client_lst = depickled_data[3]
            self.print_log('got client list')
            #right client information
            self.print_log(f'client_lst: {client_lst}')
            self.rc_ip = client_lst[index_pos][1]
            self.rc_port = int(client_lst[index_pos][3])
            self.print_log(f'self.rc_ip: {self.rc_ip}, self.rc_port: {str(self.rc_port)}')
            index_pos+=1
            self.print_log('sending o-ring-setup to manage right client')
            self.manage_right_client(pickle.dumps(('o-ring-setup', client_lst, index_pos)))
        elif(type(depickled_data) is tuple and depickled_data[0] == 'o-ring-setup'):
            # setup of the ring.
            client_lst = depickled_data[1]
            index_pos = depickled_data[2]
            self.print_log(f'index position is: {index_pos}')
            # client allocated leader
            if index_pos == 1:
                self.compute_port = pp_port_1
                self.client_name
                stpreply_msg = pickle.dumps(('setup-complete ' + self.ring_id + ' ' + self.client_name + ' ' + self.compute_port))
                self.socket_ss.sendto(stpreply_msg, (self.server_ip, self.destination_port))
            else:
                if index_pos == len(client_lst):
                    self.rc_ip = client_lst[index_pos][1]
                    self.rc_port = int(client_lst[index_pos][3])
                    index_pos = 1
                else:
                    self.rc_ip = client_lst[index_pos][1]
                    self.rc_port = int(client_lst[index_pos][3])
                    index_pos+=1

                still_stp_msg = pickle.dumps(('setup', client_lst, index_pos))
                self.manage_right_client(still_stp_msg)

        elif(type(depickled_data) is tuple and depickled_data[0] == 'FAILURE'  and len(depickled_data) == 5):
            # couldn't setup ring
            self.print_log(f'Code: FAILURE. User is already in a ring.')
        # hold for other methods and their implementation
        else:
            self.print_log(f'Inside else')

    def manage_left_client(self):
        while 1:
            reply, address = self.socket_pp_1.recvfrom(4096)
            self.print_log(f'Message Received from: {str(address)}')
            
            self.socket_pp_1.sendto(pickle.dumps('SUCCESS'), address)
            self.print_log(f'Acknowledgement sent to {str(address)}')

            self.interpret_commands(pickle.loads(reply))
    
    def manage_right_client(self, message):
        self.print_log('inside right client')
        self.socket_pp_2.sendto(message, (self.rc_ip, self.rc_port))
        self.print_log(f'Message has been sent to {str((self.rc_port, self.rc_ip))}')

        reply, address = self.socket_pp_2.recvfrom(4096)
        self.print_log(f'Acknowledgment from {str(address)} has been received')

        self.interpret_commands(pickle.loads(reply))

    def send_commands_to_server(self):
        while 1:
            try:
                message = input('Enter command to send: ')
                self.print_log(f'Client sends {message} to server')
                decoded_split = message.split()
                # assign ports for binding. Supports only 3 ports right now
                if decoded_split[0] == 'register':
                    try:
                        port_list = []
                        for i in decoded_split[3:]:
                            if(int(i)<44000 and int(i)>43500):
                                port_list.append(i)
                        port_list = sorted(port_list)
                        if(decoded_split[2].count('.') == 3):
                            self.client_ip = decoded_split[2] # ip address of the client
                    except:
                        print('Error: Incorrect Port numbers/IP address. Please retype the command')
                    # ss_port is client port which is used to send packets to server socket 
                    # pp ports are used for peer processes. pp_1 is left, pp_2 is right
                    self.ss_port, self.pp_port_1, self.pp_port_2 = int(port_list[0]), int(port_list[1]), int(port_list[2])
                    # creates sockets and binds the correct ports to them
                    self.create_bind_sockets()
                elif decoded_split[0] == 'setup-ring':
                    self.compute_port = decoded_split[2]
                try:
                    # check if length of message to server is equal to the length of the message inputted
                    if(self.socket_ss.sendto(message.encode('utf-8'), (self.server_ip, self.destination_port)) == len(message)):
                        # Receive data from server (data, addr)
                        response, server_addr = self.socket_ss.recvfrom(4096)
                        # depickles the received response
                        de_pickle = pickle.loads(response)
                        self.print_log(f'Server response: {de_pickle}')
                        self.interpret_commands(de_pickle)
                except socket.error as message:
                    self.print_log(f'Error Code: {str(message[0])} | Message {message[1]}')
                    sys.exit()
            except KeyboardInterrupt:
                    self.close_socket()

    def create_bind_sockets(self):
        # bind socket to pp_port_2 (right)
        try:
            self.socket_pp_2.bind((self.client_ip, self.pp_port_2))
            self.print_log(f'Binded pp_2 to {self.client_ip}:{self.pp_port_2} successful')
        except socket.error as msg:
            self.print_log('Bind to pp_port_2 failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()
        
        # Bind socket to pp_port_1 (left)
        try:
            self.socket_pp_1.bind((self.client_ip, self.pp_port_1))
            self.print_log(f'Binded pp_1 to {self.client_ip}:{self.pp_port_1} successful')
        except socket.error as msg:
            self.print_log('Bind to pp_port_1 failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()
        
        # Bind socket to ss_port (server)
        try:
            self.socket_ss.bind((self.server_ip, self.ss_port))
            self.print_log(f'Binded ss to {self.server_ip}:{self.ss_port} successful')
        except socket.error as msg:
            self.print_log('Bind to ss_port failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()

    def close_socket(self):
        # Close socket
        if(self.socket_ss is None or self.socket_pp_1 is None or self.socket_pp_2 is None):
            sys.exit()
        else:
            self.print_log('Closing the sockets')
            self.socket_ss.close()
            self.socket_pp_1.close()
            self.socket_pp_2.close()
            self.print_log('Sockets closed')
            sys.exit()

def main():
    # get port and server_ip from command line
    argv = sys.argv[0:]
    # check if the 2nd argument is an ip address
    if(argv[1].count('.') != 3):
        print('Usage: python3 Client.py <server ipaddress>')
        sys.exit()
    else:
        server_ip = argv[1] # get server IP
        print(f'Argument passed: server IP {server_ip}. Port is 43599 by default')

    udp_client = UDPClient(server_ip, 43599)
    udp_client.print_log('Making instances...')
    server_instance = threading.Thread(target=udp_client.send_commands_to_server)
    client_instance = threading.Thread(target=udp_client.manage_left_client)

    try:
        udp_client.print_log('Starting Server Instance...')
        server_instance.start()
        udp_client.print_log('Starting Client Instance...')
        client_instance.start()

    except KeyboardInterrupt:
        server_instance.join()
        client_instance.join()
        udp_client.close_socket()


if __name__ == '__main__':
    main()
