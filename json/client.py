import pygame, socket, threading, json

DEST_IP = socket.gethostbyname(socket.gethostname())
DEST_PORT = 54321

class Connection():
    '''A socket connection of class for players to connect to a server'''
    def __init__(self):
        #Intialize connection
        self.encoder = "utf-8"
        self.header_length = 10

        #create a socket and connect
        self.player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.player_socket.connect((DEST_IP, DEST_PORT))
        
        
class Player():
    '''A player class the client can control'''
    def __init__(self, connection):
        #Recieve the player information from the server
        packet_size = connection.player_socket.recv(connection.header_length).decode(connection.encoder)
        player_info_json = connection.player_socket.recv(int(packet_size))
        player_info = json.loads(player_info_json)

        self.number = player_info['number']
        self.size = player_info['size']

        self.start_x = player_info['start_x']
        self.start_y = player_info['start_y']
        self.colour = player_info['colour']
        self.scorecolour = player_info['scorecolour']
    
        self.x = player_info['x']
        self.y = player_info['y']
        self.dx = player_info['dx']
        self.dy = player_info['dy']
        self.coor = player_info['coor']

        self.is_waiting = player_info['is_waiting']
        self.is_ready = player_info['is_ready']
        self.is_playing = player_info['is_playing']
        self.status_mes = player_info['status_mes']
        

    def set_player_info(self, player_info):
        self.is_waiting = player_info['is_waiting']
        self.is_ready = player_info['is_ready']
        self.is_playing = player_info['is_playing']

        

    def update(self):
        #update the player by changing their corr in game
        keys = pygame.key.get_pressed()

        #create a rectangle to resrict player movment.
        player_rect = pygame.draw.rect(display_surface, self.colour, self.coor)

        #move player if game is playing
        if self.is_playing:
            if keys[pygame.K_w] and player_rect.top > 0:
                self.dx = 0
                self.dy = -1*self.size
            elif keys[pygame.K_s] and player_rect.bottom < HEIGHT:
                self.dx = 0
                self.dy = 1*self.size
            elif keys [pygame.K_a] and player_rect.left > 0:
                self.dx = -1*self.size
                self.dy = 0
            elif keys[pygame.K_d] and player_rect.right < WIDTH:
                self.dx = 1*self.size
                self.dy = 0
            else:
                self.dx = 0
                self.dy = 0
            
            #update coor
            self.x += self.dx
            self.y += self.dy
            self.coor = (self.x, self.y, self.size, self.size)



    def reset_player(self):
        '''reset player vaules for a new round on the client side'''
        self.x = self.start_x
        self.y = self.start_y
        self.coord = (self.x, self.y, self.size, self.size)

        self.is_waiting = False
        self.is_ready = True
        self.is_playing = False
        self.status_message = "Ready...waiting"
    
class Game():
        '''A game class to handle all operations of gameplay'''
        def __init__(self, connection, player, total_players):
            '''intialize game class'''
            self.connection = connection
            self.player = player
            self.total_players = total_players
            self.is_active = False


            #set the player count to player number -1, we haven't recieved any game state data yet
            self.player_count = self.player.number -1

            #create a list to hold current state of the game (from the server)
            self.game_state = []

            #varibles to hold the state of the crrent game
            self.round_time = ROUND_TIME
            self.high_score = 0
            self.winning_player = 0

            #wait for all player joined 
            waiting_thread = threading.Thread(target=self.recieve_pregame_state)
            waiting_thread.start()


        def ready_game(self):
            '''ready the game to be player'''
            #update status flags for the player
            self.player.is_waiting = False
            self.player.is_ready = True
            self.player.status_mes = "Ready .... waiting"

            #send status to the server
            self.send_player_info()

            #monitor for the start of the game from the server
            start_thread = threading.Thread(target=self.start_game)
            start_thread.start()

        
        def start_game(self):
            '''start game'''
            while True:
                #wait to receive information from the server that the game has started
                self.recieve_player_info()
                if self.player.is_playing:
                    self.is_active = True
                    self.player.is_ready = False
                    self.player.status_mes = 'GO'
                    break
        
        def reset_game(self):
            '''reest game'''
            #reset teh clock
            self.round_time = ROUND_TIME
            self.winning_player = 0
            self.high_score = 0

            #Reset the player
            self.player.reset_player()

            #Send updated status to the server
            self.send_player_info()

            #Monitor for the start of the game from the server
            start_thread = threading.Thread(target=self.start_game)
            start_thread.start()

        def send_player_info(self):
            '''send info about player to the server'''
            #create a dictionairy of items to send
            player_info = {
                'coor':self.player.coor, 
                'is_waiting': self.player.is_waiting,
                'is_ready': self.player.is_ready,
                'is_playing': self.player.is_playing
            }

            #send the dict on to the server
            player_info_json = json.dumps(player_info)
            header = str(len(player_info_json))
            while len(header) < self.connection.header_length:
                header += " "  
            self.connection.player_socket.send(header.encode(self.connection.encoder))
            self.connection.player_socket.send(player_info_json.encode(self.connection.encoder))
            
        
        def recieve_player_info(self):
            '''Recieve specfic infon about this player from the server'''
            packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            player_info_json = self.connection.player_socket.recv(int(packet_size))
            player_info = json.loads(player_info_json)
            

            #set the updated flags 
            self.player.set_player_info(player_info)


        def recieve_pregame_state(self):
            '''recieve all info before game start'''
            while self.player_count < self.total_players:
                #wait for player to join and get their info
                packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
                game_state_json = self.connection.player_socket.recv(int(packet_size))
                game_state = json.loads(game_state_json)
                self.game_state = game_state

                #increase the games player count
                self.player_count += 1

            #when players is full
            self.player.status_mes = 'Ready to play'

        def recieve_game_state(self):
            '''recieve all infon about all players from the server during game'''
            #recive the games state
            packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            game_state_json = self.connection.player_socket.recv(int(packet_size))
            game_state = json.loads(game_state_json)

            #update the clients game state.
            self.game_state = game_state

            #recieve the server time
            packet_size = self.connection.player_socket.recv(self.connection.header_length).decode(self.connection.encoder)
            self.round_time = self.connection.player_socket.recv(int(packet_size)).decode(self.connection.encoder)

            #process game state innformation
            self.process_game_state()

                

        def process_game_state(self):
            '''process the game state to update scores winning player and time'''
            
            scores = []
          
            #update coordinates
            for player in self.game_state:
                
                player= json.loads(player)
                if player['number'] == self.player.number:
                    self.player.coor = player['coor']
                    self.player.x = self.player.coor[0]
                    self.player.y = self.player.coor[1]
                #see who winning
                if player['score'] > self.high_score:
                    self.winning_player = player['number']
                    self.high_score = player['score']
                scores.append(player['score'])

            #check for a tie
            count = 0
            for score in scores:
                if score == self.high_score:
                    count += 1
                #tie for 1st place 
                if count > 1:
                    self.winning_player = 0
    
        
        def update(self):
            #update game
            if self.player.is_playing:
                self.player.update()

                if int(self.round_time) == 0:
                    self.player.is_playing = False
                    self.player.is_ready = False
                    self.player.is_waiting = True
                    self.player.status_mes = "Game Over, Enter to reset"

                 #send player info to server
                self.send_player_info()
                self.recieve_game_state()
                    


        def draw(self):
            '''draw the game window and all the assets'''

            #show winning player onleader board
            for player in self.game_state:
                player = json.loads(player)
                if player['number'] == self.winning_player:
                    display_surface.fill(player['scorecolour'])

            #list holds scores
            current_scores = []


            #loop each players state througjh to the game
            for player in self.game_state:
                player = json.loads(player)

                #preps the score
                score = "P" + str(player['number']) + ': ' + str(player['score'])
                score_text = font.render(score, True, WHITE)
                score_rect = score_text.get_rect()
                if player['number'] ==1:
                    score_rect.topleft = (player['start_x'], player['start_y'])
                elif player['number'] == 2:
                    score_rect.topright = (player['start_x'], player['start_y'])
                elif player['number'] == 3:
                    score_rect.bottomleft = (player['start_x'], player['start_y'])
                else:
                    score_rect.topright = (player['start_x'], player['start_y'])

                current_scores.append((score_text, score_rect))
                    

                pygame.draw.rect(display_surface, player['colour'], player['coor'])

            #draw outline
            pygame.draw.rect(display_surface, self.player.colour, self.player.coor)
            pygame.draw.rect(display_surface, MAGENTA, self.player.coor, int(self.player.size/10))

            #draw scores
            for score in current_scores:
                display_surface.blit(score[0], score[1])

            time_text = font.render("round time: " + str(self.round_time), True, WHITE)
            time_rect = time_text.get_rect()
            time_rect.center = (WIDTH//2, 15)
            display_surface.blit(time_text, time_rect)

            status_text = font.render(self.player.status_mes, True, WHITE)
            status_rect = status_text.get_rect()
            status_rect.center = (WIDTH//2, HEIGHT//2)
            display_surface.blit(status_text, status_rect)

                
#create a connection and get game window info from the server

my_connection = Connection()
packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
room_size = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))

packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
round_time = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))

packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
fps = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))

packet_size = my_connection.player_socket.recv(my_connection.header_length).decode(my_connection.encoder)
total_players = int(my_connection.player_socket.recv(int(packet_size)).decode(my_connection.encoder))

#intialize pygame
pygame.init()

#constants

WIDTH = room_size
HEIGHT  = room_size
ROUND_TIME = round_time
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MAGENTA = (155, 0, 155)
FPS = fps
    
clock = pygame.time.Clock()
font = pygame.font.SysFont('Ariel', 30)

display_surface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('TAG')

#create player and game objects 
my_player = Player(my_connection)
my_game = Game(my_connection, my_player, total_players)

#Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            runnng = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                #trigger reset
                if my_player.is_waiting and my_game.is_active:
                    my_game.reset_game()
            #if the game aint started but everyone joined
                if my_player.is_waiting and my_game.player_count == my_game.total_players:
                    my_game.ready_game()
            

    #Fill screen
    display_surface.fill(BLACK)
    
    my_game.update()
    my_game.draw()

    #update tick time and the clock
    pygame.display.update()
    clock.tick(FPS)
    

    
    