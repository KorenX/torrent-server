* assuming all connection are to be done with UDP 

When a client wants to aquire a file, it connects to the main server and requests the files list.
Each file has a FileID, and a Filename, with an optional description.
The user requests a certain FileID, and the main server responds with a list of possible hosts
IDs which hold the data.

File Request Protocol:

client                      server
   |                          |
   |--------list files------->|
   |<--------n files----------|\
   |-----------ack----------->| repeat m times
   |                          |/
   |                          |
   |                          |
   |-------request file------>|
   |<---------n ips-----------|\
   |-----------ack----------->| repeat m times
   |                          |/
   |                          |
   |                          |
   |----------thanks--------->|
   |                          |