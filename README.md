# Tag Game Two Player GUI using Python with JSON Library Client-Server
This is a two-player GUI game where one player is "it" and tries to catch the other player. The game is played on a grid, and the players move their respective characters around to try to evade or catch each other.

The game uses a client-server architecture, with the server responsible for keeping track of the game state and the clients responsible for displaying the game and sending user input to the server.

The game is written in Python and uses the JSON library for communication between the client and server.

# Prerequisites
- Python 3.x
- Pygame library
- JSON library

# How to Run the Game
1. Open the terminal and navigate to the directory where the game files are stored.
2. Start the server by running python server.py in the terminal.
3. Start the client by running python client.py in another terminal.
4. The game GUI will open up on both the client screens.
5. One of the players can click the "Start" button to begin the game.
6. Use the arrow keys to move the characters around the grid.
7. If the "it" character touches the other player's character, they become the new "it" character.
8. The game ends when one of the players reaches the opposite end of the grid.
9. Close the game window to exit the game.

# Communication Protocol
The client and server communicate using JSON messages. The following messages are exchanged between the client and server:

## Client to Server
- **start_game:** Sent by the client when the "Start" button is clicked. This message notifies the server that the game has started.

- **move:** Sent by the client when a player moves their character. This message contains the new position of the player's character.

## Server to Client
- **game_state:** Sent by the server to update the client's game state. This message contains the positions of both players' characters.

- **game_over:** Sent by the server to notify the client that the game has ended. This message contains the name of the winning player.

# Game Interface
The game interface consists of a grid with two characters, one representing the "it" character and the other representing the other player. The characters can be moved using the arrow keys.

# Game Rules
One player is designated as "it" and the other player tries to evade them.
The game is played on a grid.
Both players assigned with colors like red and green both moves simultaneously.
If player 1 box cathes the other player 1 gets 1 point and bacground color changes to player 1 color.
Game ends when the timmer stops.

# Acknowledgements
This game was developed using the pygame library for the GUI and the JSON library for communication between the client and server.

License
This project is licensed under the MIT License. See the LICENSE file for details.