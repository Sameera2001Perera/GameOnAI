import { type NextRequest, NextResponse } from "next/server"
import dbConnect from "@/lib/mongodb"
import Room from "@/lib/models/Room"

interface Player {
  name: string;
  uuid: string;
  profileImage: string;
}

interface CreateRoomRequest {
  room: {
    gameSessionUuid: string;
  };
  players: Player[];
}

export async function POST(request: NextRequest) {
  try {
    await dbConnect()

    const body: CreateRoomRequest = await request.json()
    const { room, players } = body

    const gameStateId = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15)

    const newRoom = new Room({
      gameSessionUuid: room.gameSessionUuid,
      players: players.map((player: Player) => ({
        name: player.name,
        uuid: player.uuid,
        profileImage: player.profileImage,
        ready: false,
        winState: "DEFEATED",
      })),
      currentTurn: players[0].uuid,
    })

    await newRoom.save()

    const baseUrl = process.env.NODE_ENV === "production" ? "https://your-domain.com" : "http://localhost:3000"

    const link1 = `${baseUrl}/?gameSessionUuid=${room.gameSessionUuid}&gameStateId=${gameStateId}&uuid=${players[0].uuid}`
    const link2 = `${baseUrl}/?gameSessionUuid=${room.gameSessionUuid}&gameStateId=${gameStateId}&uuid=${players[1].uuid}`

    return NextResponse.json({
      status: true,
      message: "success",
      payload: {
        gameSessionUuid: room.gameSessionUuid,
        gameStateId: gameStateId,
        createDate: newRoom.createdDate.toISOString(),
        link1: link1,
        link2: link2,
      },
    })
  } catch (error) {
    console.error("Error creating room:", error)
    return NextResponse.json(
      {
        status: false,
        message: "Error creating room",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}