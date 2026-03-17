import { type NextRequest, NextResponse } from "next/server"
import dbConnect from "@/lib/mongodb"
import Room from "@/lib/models/Room"

const GAMEON_BACKEND_URL = process.env.GAMEON_BACKEND_URL || "https://your-backend-url.com"

interface Player {
  uuid: string;
  name: string;
  profileImage: string;
  ready: boolean;
  winState: string;
}

interface SendWinnerRequest {
  gameSessionUuid: string;
  winner: string;
}

export async function POST(request: NextRequest) {
  try {
    await dbConnect()

    const body: SendWinnerRequest = await request.json()
    const { gameSessionUuid, winner } = body

    const room = await Room.findOne({ gameSessionUuid })

    if (!room) {
      return NextResponse.json(
        {
          status: false,
          message: "Room not found",
        },
        { status: 404 },
      )
    }

    room.gameStatus = "FINISHED"
    room.winner = winner
    room.players = room.players.map((player: Player) => ({
      ...player,
      winState: player.uuid === winner ? "WON" : "DEFEATED",
    }))

    await room.save()

    const payload = {
      gameSessionUuid,
      gameStatus: room.gameStatus,
      players: room.players.map((player: Player) => ({
        uuid: player.uuid,
        points: player.uuid === winner ? 100 : 0,
        userGameSessionStatus: player.winState,
      })),
    }

    try {
      const response = await fetch(`${GAMEON_BACKEND_URL}/api/external_game/v1/game_session_finish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      const result = await response.json()

      return NextResponse.json({
        status: true,
        message: "Winner data sent successfully",
        externalResponse: result,
      })
    } catch (externalError) {
      console.error("Error sending to external API:", externalError)
      return NextResponse.json(
        {
          status: false,
          message: "Error sending winner data to external API",
          error: externalError instanceof Error ? externalError.message : "Unknown error",
        },
        { status: 500 },
      )
    }
  } catch (error) {
    console.error("Error processing winner:", error)
    return NextResponse.json(
      {
        status: false,
        message: "Error processing winner",
        error: error instanceof Error ? error.message : "Unknown error",
      },
      { status: 500 },
    )
  }
}