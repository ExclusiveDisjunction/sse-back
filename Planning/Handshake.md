# Server Client Handshake

This protocol defines how the encryption should take place in the system. 

Pretext:
1. The server generates a public and private RSA key pair $P_s$ (public) and $p_s$ (private). 
2. The server generates an AES key $A$. 

1. Client connects to server.
2. Client creates a RSA public-private key pair. These are denoted with $P_c$ for public key, and $p_c$ for private key. 
3. The client sends $P_c$ to the server. 
4. Server uses $P_c$ to encrypt $P_s$
6. Server sends encrypted $P_s$ to client.
7. Client gets the user sign in information, and generates the message
8. Client sends message encrypted using $P_s$
9. Server receives request, decodes with $p_s$. 
10. If the user sign in is bad, and attempts is less or equal to 3, then go back to 7. 
11. If the attempts excedes 3, then the server will disconnect the session. 
12. At this point authentication is good. The server will encrypt the $A$ key, a user JWT. The JWT must be provided for requests. 
13. The server will decode, and store the $A$ key and JWT.

From this point on, the server and client will use the AES key for transmitting data. The JWT is sent with each request (encrypted), and is validated with a specific scheme. 