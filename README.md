# COMPANET - NETWORKING

COMPANET is a network project that simulates a network of 14 interconnected routers. Through a controller, the routers can communicate with each other, sending files and messages in an encrypted manner. Present by Juan Diego Morales & Alejandra Benavides

# Requirements

- Python 3.1
- Libraries:
  - json
  - os
  - base64
  - socket
  - threading
  - time
  - tkinter
  - rsa
  - cryptography


####Installation

1. Clone the repository:
 
        git clone https://github.com/JuanDiegoMorales/network.git

2. Navigate to the project directory:
 
       cd network

3. Install the dependencies:
 
        pip install json os base64 socket threading time tkinter rsa cryptography

####Usage

1. Generate the network routes:
 
        python3 test_network.py

2. Establish the clients:
 
       python3 test_client.py

3. Available commands for the clients are
  - Input port
  - Destination port
  - Select file
  - Write message

####Project Structure
Description of the main folders and files of the project:
```
network/
│
├ main.py
├ test_client.py
├ test_network.py
├
├ network/
│   - - ├── router.py
│   - - ├── controller.py
│   - - ├── client.py
│   - - ├── __init__.py
│   - - └── common/
│    - - - - - - -    ├── data.py
│   - - - - - - -     ├── network.py
│    - - - - - - -    ├── security.py
│    - - - - - - -    ├── utils.py
│     - - - - - - -   └── __init__.py
│
└── README.md
```

###Examples of Use
####Sending a file and a message


1. Run two or more clients:
 
        python3 test_client.py

2. Assign an input port to each client.
3. Set the destination port (the name of the router) for each client.
4. Write a message in both clients.
5. The clients will exchange the information.

###Links

`<Demonstration video>` : <https://youtu.be/tf-_d0mzaUs>
