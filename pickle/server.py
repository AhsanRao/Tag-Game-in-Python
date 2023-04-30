import socket, threading, time
import pickle

HOST_IP = socket.gethostbyname(socket.gethostname()) #'0.0.0.0'
HOST_PORT = 54321

#constants
ROOM = 1200
PLAYER_SIZE = 60
ROUND_TIME = 5
FPS = 30
TOTAL_PLAYERS = 2


#room must be divisible by player size as moves in self increments

while ROOM % PLAYER_SIZE != 0:
    PLAYER_SIZE += 1

#validation of players in game
if TOTAL_PLAYERS > 4:
    TOTAL_PLAYERS = 4

#Define classes 
class Connection():
    '''socket conection can be used as a server'''
    def __init__ (self):
        '''intalizes the connection'''
        self.encoder = 'utf-8'
        self.header_length = 10

        #create a socket, bind and listen
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.server_socket.bind((HOST_IP, HOST_PORT))
        self.server_socket.listen()



class Player():
    '''stores connected clients info'''
    def __init__(self, number) :
        self.number = number
        self.size = PLAYER_SIZE
        self.score = 0

        #give start conditions that change due to player number
        if self.number == 1:
            self.start_x= 0
            self.start_y = 0
            self.colour = (0, 255, 0)
            self.scorecolour = (0,200,0)

        elif self.number == 2:
            self.start_x = ROOM - PLAYER_SIZE
            self.start_y = 0
            self.colour = (255, 0, 0)
            self.scorecolour = (200,0,0)


        elif self.number == 3:
            self.start_x = 0
            self.start_y = ROOM - PLAYER_SIZE
            self.colour = (0, 0, 255)
            self.scorecolour = (0,0,200)

        elif self.number == 4:
            self.start_x = ROOM- PLAYER_SIZE
            self.start_y = ROOM - PLAYER_SIZE
            self.colour = (255, 0, 255)
            self.scorecolour = (200,0,200)

        else:
            print("Max players reached")

        #rest of player attributes
        self.x = self.start_x
        self.y = self.start_y
        self.dx = 0
        self.dy = 0
        self.coor = (self.x, self.y, self.size, self.size)

        self.is_waiting = True
        self.is_ready = False
        self.is_playing = False
        self.status_mes = ("Waiting for total players")


    def set_player_info(self, player_info):
       '''changed info by player, coor, is set'''
       self.coor = player_info['coor']
       self.is_waiting = player_info['is_waiting']
       self.is_ready = player_info['is_ready']
       self.is_playing = player_info['is_playing']
       

    def reset(self):
        '''resets player info for each round'''
        self.score = 0


class Game():
    '''handles game play operations'''
    def __init__(self, connection):
       '''intializes class'''
       self.connection = connection
       self.player_count = 0
       self.player_sockets = []
       self.player_objects = []
       self.round_time = ROUND_TIME


    def player_connection(self):
        '''connect incoming player rerquests'''
        #accept players when player count < that total
        while self.player_count < TOTAL_PLAYERS:
            #accept players connection
            player_socket, player_address = self.connection.server_socket.accept()

            #send game configurations vaules to client 
            header = str(len(str(ROOM)))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.sendall(header.encode())
            player_socket.sendall(str(ROOM).encode())

            header = str(len(str(ROUND_TIME)))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.sendall(header.encode())
            player_socket.sendall(str(ROUND_TIME).encode())

            header = str(len(str(FPS)))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.sendall(header.encode())
            player_socket.sendall(str(FPS).encode())

            header = str(len(str(TOTAL_PLAYERS)))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.sendall(header.encode())
            player_socket.sendall(str(TOTAL_PLAYERS).encode())

            #create a new player object for the connected client
            self.player_count += 1
            player = Player(self.player_count)
            self.player_objects.append(player)
            self.player_sockets.append(player_socket)
            print(f"New player joining from {player_address}, Total players =: {self.player_count}...")

            #send new player to object of connected client
            player_info_pickle = pickle.dumps(player.__dict__)
            header = str(len(player_info_pickle))
            while len(header) < self.connection.header_length:
                header += " "
            player_socket.sendall(header.encode())
            player_socket.sendall(player_info_pickle)

            #broadcast all players new data
            self.broadcast()

            #create a thread to moniter the ready status of THIS player
            ready_thread = threading.Thread(target= self.ready, args=(player, player_socket,))
            ready_thread.start()
 

        #when players = total no longer accept incoming requests
        print(f"{TOTAL_PLAYERS} players in game ... No longer allowing players")

        
    def broadcast(self):
        '''broadcasts information to all players'''
        game_state = []

        #turn each player object into a dict, then string with pickle
        for player_object in self.player_objects:
            player_pickle = pickle.dumps(player_object.__dict__) 
            game_state.append(player_pickle)

        #runs and sends game state whenever someone new joins
        game_state_pickle = pickle.dumps(game_state)
        header = str(len(game_state_pickle))
        while len(header) < self.connection.header_length:
            header += " "
        for player_socket in self.player_sockets:
            player_socket.sendall(header.encode())
            player_socket.sendall(game_state_pickle)
          
    
    def ready(self, player, player_socket):
        '''ready the game for a specfic player'''
        #wait until the given player has sent info to say they are ready
        self.recieve_pregame_player_info(player, player_socket)

        self.restart(player)

        #check if player is ready to play
        if player.is_ready:
            while True:
                #check if ALL players are ready 
                game_start = True
                for player_object in self.player_objects:
                    if player_object.is_ready == False:
                        game_start = False

                #All current players are ready to play the game
                if game_start:
                    player.is_playing = True
                    
                    #start a class on the server
                    self.start_time = time.time()
                    break

            #send updated player glafs on this player
            self.send_player_info(player, player_socket)

            #now player has started on client make a thread to recieve info
            receive_thread = threading.Thread(target=self.recieve_player_game_info, args=(player, player_socket))
            receive_thread.start()


    def restart (self, player):
        '''restart game and wipe info for specfic player'''
        #Reset the game
        self.round_time = ROUND_TIME

        #Reset the player
        player.reset()

    def send_player_info(self, player, player_socket):
        '''send specfic info about this player to the given client'''
        player_info = {
            'is_waiting': player.is_waiting,
            'is_ready': player.is_ready,
            'is_playing': player.is_playing,
        }

        #send the player info over to this player
        player_info_pickle = pickle.dumps(player_info)
        header = str(len(player_info_pickle))
        while len(header) < self.connection.header_length:
            header +=" "
        player_socket.sendall(header.encode())
        player_socket.sendall(player_info_pickle)

    
    def recieve_pregame_player_info(self, player, player_socket):
        '''recieve specfic info about this player pregame'''
        packet_size = player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
        player_info_pickle = player_socket.recv(int(packet_size))
        player_info = pickle.loads(player_info_pickle)

        #set the updated vaules for THIS player
        player.set_player_info(player_info)


    
    def recieve_player_game_info(self, player, player_socket):
        '''Recieve specfic info about player during the game'''
        while player.is_playing:
            packet_size = player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            player_info_pickle = player_socket.recv(int(packet_size))
            player_info = pickle.loads(player_info_pickle)

            player.set_player_info(player_info)
            self.process_game(player, player_socket)
        
        #moniter for game ending
        ready_thread = threading.Thread(target=self.ready, args=(player, player_socket))
        ready_thread.start()


    def process_game(self, player, player_socket):
        '''update game state dependant on player info'''
        #update clock 
        self.current_time = time.time()
        self.round_time = ROUND_TIME - int(self.current_time - self.start_time)

        #process collisons 
        for player_object in self.player_objects:
            if player!= player_object:
                if player.coor == player_object.coor:
                    player.score += 1
                    player.x = player.start_x
                    player.y = player.start_y
                    player.coor = (player.x, player.y, player.size, player.size)
            
        #send updated game state to player 
        self.send_game_state(player_socket)


    def send_game_state(self, player_socket):
        '''sned game state of all players to specfic player'''
        game_state = []
        

        #turn each connected player object into an object into a dict  then string
        for player_object in self.player_objects:
            player_pickle = pickle.dumps(player_object.__dict__)
            game_state.append(player_pickle)

        #snd the whole game state back to this player
        game_state_pickle = pickle.dumps(game_state)
        header = str(len(game_state_pickle))
        while len(header) < self.connection.header_length:
            header += " "
        player_socket.sendall(header.encode())
        player_socket.sendall(game_state_pickle)

        #send sverver time
        header = str(len(str(self.round_time)))
        while len(header) < self.connection.header_length:
            header += " "
        player_socket.sendall(header.encode())
        player_socket.sendall(str(self.round_time).encode())
        

#start the server
my_connection = Connection()
my_game = Game(my_connection)

print("server is looking for incoming connections ...")
my_game.player_connection()