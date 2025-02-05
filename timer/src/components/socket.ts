import {io,  Socket } from "socket.io-client";

const socket: Socket = io("http://localhost:8000", {
    transports: ["websocket"],
  });

export default socket