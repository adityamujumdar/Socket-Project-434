# Aditya Mujumdar and Jendric Shawn Chan
# COmputer Netorking CSE 434 Fall 2020 Milestone 1

# Multithreaded server

import socket, threading, time, random, uuid, sys, pickle
from datetime import datetime

class ThreadedServer:
    # Make a multithreaded server with locks to respond to each client
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket_gen = None
        self.socket_lock = threading.Lock()
        self.big_database = []
        self.ringid_database = {}
        self.listening_ports = {}

    def start_server(self):
        # Socket creation and binding the server
        # Create socket
        try:
            self.print_log('Creating Socket...')
            self.socket_gen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.print_log('Socket creation successful!')
        except socket.error as msg:
            self.print_log('Socket creation failed. Error Code: ', str(msg[0]), 'Message ', msg[1])
            sys.exit()
        # Bind socket to local host and port
        try:
            if(self.socket_gen.bind((self.host, self.port)) == 0):
                self.print_log(f'Binded server to {self.host}:{self.port} successful')
        except socket.error as msg:
            self.print_log('Bind failed. Error Code : ', str(msg[0]), ' Message ', msg[1])
            sys.exit()

    def print_log(self, msg):
        # Log time for a message
        log_T = datetime.now().strftime('%Y/%m/%d; %H:%M:%S')
        print(f'[{log_T}] {msg}')

    def register_user(self, decoded_split):
        # Register the client in the database
        send_code = None
        self.print_log('REGISTER command selected')
        # check for username length (username <= 15)
        if(len(decoded_split[1])>15):
            self.print_log('Username should be less than 15 characters long. Please reinput')
            send_code = 'FAILURE'
        else:
            check_duplicate_ports = False
            # duplicate port check
            for i in range(len(self.big_database)):
                if(decoded_split[1] in self.big_database[i]):
                    self.print_log('Duplicate username, cannot register')
                    send_code = 'FAILURE'
                elif(send_code != 'FAILURE'):
                    # argument 3 onwards are the port numbers
                    for j in decoded_split[3:]:
                        if(j =='Free' or j=='InRing' or j == 'Leader'):#ignore state strings
                            check_duplicate_ports = False
                        elif(j in self.big_database[i]):
                            check_duplicate_ports = True # duplicate ports exist
                        else:
                            check_duplicate_ports = False
                else:
                    self.print_log('Should not be in this case of register!!!')
                    send_code = 'FAILURE'
            # correct port range check
            port_range = False
            for i in decoded_split[3:]:
                if(int(i)>=43500 and int(i)<=43999):
                    port_range = True # correct port range
                else:
                    port_range = False
            # check for port range, duplicate ports and if ipaddress is provided in correct format and if send_code is FAILURE
            # if send code is FAILURE then that means either a username longer than 15 chars is used, duplicate username exists or goes in else statement for loop shouldn't go inside
            # if parameters are unique then append them to the self.big_database.
            if(decoded_split[2].count('.') != 3 or (port_range == False) or (check_duplicate_ports == True) or (send_code == 'FAILURE')):
                self.print_log('Duplicate Username, Improper IP address or Improper port numbers. Please reinput')
                send_code = 'FAILURE'
            else:
                decoded_split.append('Free')
                self.big_database.append(list(decoded_split[1:]))
                send_code = 'SUCCESS'
                self.print_log('Username has been registered in the database')
                print(self.big_database)
        return send_code

    def deregister_user(self, decoded_split):
        # Deregister the User
        send_code = None
        self.print_log('DEREGISTER command selected')
        print(f'strip is: {decoded_split}')
        for i in range(len(self.big_database)):
            # check if the username is already in database
            try:
                if(decoded_split[1] == self.big_database[i][0]):
                    if('InRing' in self.big_database[i] or 'Leader' in self.big_database[i]):
                        self.print_log('Client has state InRing or is Leader, cannot deregister')
                        send_code =  'FAILURE'
                    else:
                        # deregister
                        try:
                            del self.big_database[i]
                            self.print_log('Client has been deregistered')
                            print(self.big_database)
                            send_code = 'SUCCESS'
                        except:
                            self.print_log('Deregistration failed even when client was not InRing/Leader')
                            send_code = 'FAILURE'
            except:
                self.print_log('Deregistration failed. client name is not in registry')
                print(self.big_database)
                send_code = 'FAILURE'
        return send_code

    def setup_ring(self, decoded_split):
        # Setup the O-Ring
        send_code = None
        self.print_log('SETUP-RING command')
        # will have setup-ring <n> <user-name> (n>=3)
        n = int(decoded_split[1])
        inring_flag = False
        ring_id = None
        free_position = []
        for i in range(len(self.big_database)):
            for j in range(len(self.big_database[i])):
                # check if username in the directory and InRing
                if(self.big_database[i][j] == decoded_split[2] and 'InRing' in self.big_database[i]):
                    inring_flag = True
        #check if correct n value is being used
        if(n>=3 and n%2==1 and inring_flag == False):
            user_name = decoded_split[2]
            free_counter = 0 # counts the number of free users in the database
            #check if user_name is registered and Free
            username_flag = False
            for i in range(len(self.big_database)):
                if('Free' in self.big_database[i]):
                    # username is free
                    username_flag = True
                    free_counter += 1
                elif(user_name in self.big_database[i]):
                    # username is in big database
                    username_flag = True
                else:
                    username_flag = False
            # TODO: Could assign an upper limit on n?
            if(username_flag==True and (free_counter>=(n-1))):
                # n is odd and >=3, username is free and registered and there's atleast n-1 free users in database
                # only 1 user can request ring making and be in the database. combating duplicates with below variable
                user_counter = False
                for i in range(len(self.big_database)):
                    if(user_name in self.big_database[i] and user_counter == False):
                        user_requesting_setup = self.big_database[i]
                        user_requesting_pos = i
                        user_counter = True # user_requesting_setup has been recognized
                    if('Free' in self.big_database[i] and (user_name not in self.big_database[i])):
                        # finds positions of free users in the big database and appends it
                        free_position.append(i)
                # g contains the random element positions to be selected in big database for random users
                # if n is 3, 2 users will be randomly selected from self.big_database
                # with user who requested setup-ring being the 3rd user
                g = random.sample(free_position, (n-1))
                # select random n-1 Free users to set their state to InRing
                selected_users = []
                selected_users.append(user_requesting_setup)
                for pos in g:
                    selected_users.append(self.big_database[pos])
                # sort and keep the list alphabetically organized by user name
                # append the user requesting setup to the n users list
                for i in range(len(selected_users)):
                    for j in range(len(selected_users[i])):
                        if(selected_users[i][j] == 'Free'):
                            selected_users[i][j] = 'InRing' # change state to InRing
                # ring_id contains the ring id for the ring being made
                ring_id = (uuid.uuid4().hex[:9])
                send_code = 'SUCCESS'
                # setting the ring_id in the database
                # setdefault will not override and change information for a key if it has alreay been set
                self.ringid_database.setdefault(ring_id, selected_users)
                # update states in big database:
                # the states in big database should be automatically updated due to changing those specific elements and assigning them
                # to selected users. Still printing the database to make sure!

                print('Ring ID database: ', self.ringid_database)
                return send_code, ring_id, n, tuple([tuple(i) for i in self.ringid_database[ring_id]]), 1
            else:   
                self.print_log(f'username {username_flag} free counter{free_counter}')
                self.print_log('Either username was not in database or there weren\'t enough free clients. Please type the command again')
                send_code = 'FAILURE'
                return send_code, ring_id, n, tuple(['None','FAILURE']), 20
        else:
            self.print_log('Username already InRing or n value is either < 3 or not odd')
            send_code = 'FAILURE'
            return send_code, ring_id, n, tuple(['None','FAILURE']), 20
    
    def setup_complete(self, decoded_split):
        send_code = None
        self.print_log('SETUP-COMPLETE command')
        # Change the username's in decoded_split[2] state to Leader in big_database and ringid_database
        # keep the port in decoded_split[3] in listener_database 
        # setup the port given by the client to listen as leader for compute commands
        try:
            # get the list of lists for the ring which has all the users and change the state of the user-id to Leader
            ring_id_list = self.ringid_database[decoded_split[1]]
            for i in range(len(ring_id_list)):     
                if (decoded_split[2] in ring_id_list[i] and 'InRing' in ring_id_list[i]):
                    for j in range(len(ring_id_list[i])):
                        if(ring_id_list[i][j] == 'InRing'):
                            ring_id_list[i][j] = 'Leader'

            # update the database entry to state Leader
            for i in range(len(self.big_database)):
                if(decoded_split[2] in self.big_database[i] and 'InRing' in self.big_database[i]):
                    for j in range(len(self.big_database[i])):
                        if(self.big_database[i][j] == 'InRing'):
                            self.big_database[i][j] = 'Leader'
            send_code = 'SUCCESS'
        except:
            print('Couldn\'t change the state to Leader. Please reinput')
            send_code = 'FAILURE'
        # key = ring id, value = (username, portnumber)
        self.print_log(decoded_split)
        self.listening_ports.setdefault(decoded_split[1], (decoded_split[2], decoded_split[3]))
        self.print_log('Setup Complete! Printing information about the system...')
        self.print_log(f'Database: {self.big_database}')
        self.print_log(f'Ring ID Database: {self.ringid_database}')
        self.print_log(f'Listening port: {self.listening_ports}')
        return send_code
    
    def compute(self, decoded_split):
        self.print_log('COMPUTE command')
        send_code = 'FAILURE'
        user_nm = decoded_split[1]
        if(len(self.ringid_database) == 0):
            send_code = 'FAILURE'
        else:
            for i in range(len(self.big_database)):
                if(user_nm == self.big_database[i][0] and self.big_database[i][5] =='Free'):
                    # user is registered
                    send_code = 'SUCCESS'

        if(send_code=='SUCCESS'):
            keys = []
            for i in self.ringid_database:
                keys.append(i)
            # ring if of O-ring
            ring_id_key = random.choice(keys)
            userlist = self.ringid_database[ring_id_key]
            # size n
            size_lst = len(userlist)
            leader_name = userlist[0][0]
            leader_ip = userlist[0][1]
            leader_port = userlist[0][3]
        else:
            send_code = 'FAILURE'
            ring_id_key = 0
            size_lst = 0
            leader_name = 0
            leader_ip = 0
            leader_port = 0

        return send_code, ring_id_key, size_lst, (leader_name, leader_ip, leader_port)


    def teardown_ring(self, decoded_split):
        send_code = None
        self.print_log('TEARDOWN-RING command')
        self.print_log(f'Ring ID: {decoded_split[1]}, User name: {decoded_split[2]}')
        ring_id = decoded_split[1]
        usr_nm = decoded_split[2]
        self.print_log(f'ring id: {ring_id}, user name: {usr_nm}')
        for i in self.ringid_database:
            if(i == ring_id):
                client_list = self.ringid_database[i]
                if(client_list[0][0] != 'usr_nm'):
                    send_code = 'SUCCESS'
        if(send_code=='SUCCESS'):
            self.print_log(f'Ring ID Database (before del): {self.ringid_database}')
            del(self.ringid_database[ring_id])
            self.print_log(f'Ring ID Database (after del): {self.ringid_database}')
        else:
            send_code = 'FAILURE'
        return send_code

    def teardown_complete(self, decoded_split):
        pass

    def interpret_request(self, decoded_data):
        send_code = None
        p_dump = None
        decoded_split = decoded_data.split()
        # for register command
        if(decoded_split[0] == 'register'):
            return_code = self.register_user(decoded_split)
            p_dump = pickle.dumps(return_code)
        # for deregister command
        elif(decoded_split[0] == 'deregister'):
            return_code = self.deregister_user(decoded_split)
            p_dump = pickle.dumps(return_code)
        # for setup-ring command
        elif(decoded_split[0] == 'setup-ring'):
            return_code, ring_id, n, users_list, index_pos = self.setup_ring(decoded_split)
            stp_ring_returns = (return_code, ring_id, n, users_list, index_pos)
            # serialize the data to bytes
            p_dump = pickle.dumps(stp_ring_returns)
            return p_dump
        # for setup-complete
        elif(decoded_split[0] == 'setup-complete'):
            return_code = self.setup_complete(decoded_split)
            p_dump = pickle.dumps(return_code)
        # for teardown-ring
        elif(decoded_split[0] == 'teardown-ring'):
            return_code = self.teardown_ring(decoded_split)
            p_dump = pickle.dumps(return_code)
            # for teardown-complete
        elif(decoded_split[0] == 'teardown-complete'):
            return_code = self.teardown_complete(decoded_split)
            p_dump = pickle.dumps(return_code)
            # for compute function
        elif(decoded_split[0] == 'compute'):
            send_code, ring_id_key, size_lst, (leader_name, leader_ip, leader_port) = self.compute(decoded_split)
            compt_rtrn = (send_code, ring_id_key, size_lst, (leader_name, leader_ip, leader_port))
            # serialize everything to bytes and return
            p_dump = pickle.dumps(compt_rtrn)
        else:
            self.print_log('Unsupported command was typed. Please retype the command')
            pass
        return p_dump

    def handle_request(self, data, client_addr):
        # Handle Client request
        message = data.decode('utf-8')
        response = self.interpret_request(message)
        self.print_log(f'response to client: {pickle.loads(response)}')
        try:
            if(response != None):
                self.print_log(f'REQUEST from {client_addr}')
                self.print_log(message)
                # time.sleep(5) # for testing the capabilities of the threaded server
                # send response to the client
                self.print_log(f'RESPONSE to {client_addr}')
                with self.socket_lock:
                    # resp will be in bytes as a pickled object
                    self.socket_gen.sendto(response, client_addr)
                self.print_log(pickle.loads(response))
        except:
                # didn't go in any conditions:
                self.print_log('Unsupported command was typed. Please retype the command')

    def listen(self, buffer_len = 4096):
        # Listen the clients
        try:
            while True: # keep alive
                try: # receive request from client
                    data, client_addr = self.socket_gen.recvfrom(buffer_len)
                    new_thread = threading.Thread(target = self.handle_request, args = (data, client_addr), daemon = True)
                    new_thread.start()
                except OSError as err:
                    self.print_log(err)

        except KeyboardInterrupt:
            self.close_socket()
    
    def close_socket(self):
        # Close socket
        self.print_log('Closing the socket')
        self.socket_gen.close()
        self.print_log('Socked closed')
        sys.exit()

def main():
    # Server will handle multiple clients using multithreading     
    # Server will listen to all interfaces for host = ''
    # Server would be on port 43500
    print('Server Starting at port 43599')
    threaded_udp_server = ThreadedServer('', 43599)
    threaded_udp_server.start_server()
    threaded_udp_server.listen()

if __name__ == '__main__':
    main()
