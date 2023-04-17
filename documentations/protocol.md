* assuming all connection are to be done with UDP 

When a client wants to aquire a file, it connects to the main server and requests the files list.
Each file has a FileID, and a Filename, with an optional description.
The user requests a certain FileID, and the main server responds with a list of possible peer IDs which hold the file.

Once the client has the file id and the peers who have this file, it can start requesting this file.
A request of this file is a request sent from a client to a client. The client requesting the file is marked with (req), and the client responding to the request is marked with (res).
A request is made of the fileID, and the chunks requested.
This way, the client can request different chunks from different clients.


File Info Protocol:

client                      server
   |                          |
   |--------list files------->|
   |<--------n files----------|\
   |-----------ack----------->| repeat m times
   |                          |/
   |<------finish files-------|
   |                          |
   |                          |
   |                          |
   |-------request file------>|
   |<---------n ips-----------|\
   |-----------ack----------->| repeat m times
   |                          |/
   |<-------finish ips--------|
   |                          |
   |                          |
   |                          |
   |----------thanks--------->|
   |                          |


Register To Server:

client                      server
   |                          |
   |---------register-------->|
   |<----------ack------------|
   |----------thanks--------->|

Get Torrent Data:

client(req)                 client(res)
   |                          |
   |---------request--------->|
   |<----------ack------------|
   |<---------chunk-----------| repeat n times