// pages/api/socket.ts
import type { NextApiRequest, NextApiResponse } from "next";
import type { Server as NetServer } from "http";
import { Server as SocketIOServer } from "socket.io";

type Res = NextApiResponse & {
  socket: NextApiResponse["socket"] & {
    server: NetServer & { io?: SocketIOServer };
  };
};

const gameRooms = new Map<string, Set<string>>();

export default function handler(req: NextApiRequest, res: Res) {
  if (!res.socket.server.io) {
    console.log("Setting up Socket.IO server...");

    const io = new SocketIOServer(res.socket.server, {
      path: "/api/socket",
      addTrailingSlash: false,
      cors: { origin: "*", methods: ["GET", "POST"] },
    });

    io.on("connection", (socket) => {
      console.log("User connected:", socket.id);

      socket.on("join-game", ({ gameSessionUuid, playerUuid }) => {
        socket.join(gameSessionUuid);
        if (!gameRooms.has(gameSessionUuid)) gameRooms.set(gameSessionUuid, new Set());
        gameRooms.get(gameSessionUuid)!.add(socket.id);
        socket.to(gameSessionUuid).emit("player-joined", { playerUuid });
      });

      socket.on("make-move", ({ gameSessionUuid, playerUuid, position, gameBoard, currentTurn }) => {
        socket.to(gameSessionUuid).emit("move-made", { playerUuid, position, gameBoard, currentTurn });
      });

      socket.on("game-won", ({ gameSessionUuid, winner }) => {
        socket.to(gameSessionUuid).emit("game-ended", { winner });
      });

      socket.on("disconnect", () => {
        for (const [room, ids] of gameRooms.entries()) {
          if (ids.delete(socket.id) && ids.size === 0) gameRooms.delete(room);
        }
      });
    });

    res.socket.server.io = io;
  }

  res.end("Socket.IO server is running");
}